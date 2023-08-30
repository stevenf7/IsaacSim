// Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "LidarNodeUtils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/tasking/ITasking.h>

#include <internal/omni/sensors/lidar/LidarReturnHelper.h>
#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>
#include <thrust/copy.h>
#include <thrust/device_ptr.h>

#include <OgnIsaacCreateRTXLidarScanBufferDatabase.h>

extern "C" void azimuthRightHanded(float* srcDest, float3* scratch, float accuracyError, int N, int cdi);
extern "C" void elevation(float* srcDest, float3* scratch, float* scratch2, float accuracyError, int N, int cdi);
extern "C" void pointCloud(float3* srcDest, const float* cosEle, const float* dist, int N, int cdi);

namespace omni
{
namespace isaac
{
namespace sensor
{

std::ostream& operator<<(std::ostream& os, const SensorPose& sp)
{
    os << "(" << sp.posM[0] << ", " << sp.posM[1] << ", " << sp.posM[2] << ")[" << sp.orientation[0] << ", "
       << sp.orientation[1] << ", " << sp.orientation[2] << ", " << sp.orientation[3] << "]";
    return os;
}

const size_t sizeofLidarTick = sizeof(float) + sizeof(uint32_t) + sizeof(uint64_t); // see: struct LidarTicks
const size_t sizeofLidarReturn = sizeof(float) * 10 + sizeof(uint32_t) * 5; // see: struct LidarReturns

// The idea of this node is to keep a larger copy of the rtx sensor buffer that holds
// a full 360 scan, updating the locations with the newest available one and keeping
// the rest of the angles the same.
// header
// TODOMTC stop assuming dataHost comes in as CPU when you can make GPU work!
// TODOMTC output GPU!
class OgnIsaacCreateRTXLidarScanBuffer
{
private:
    std::string config;
    LidarScanType scanType{ LidarScanType::kUnknown };
    LidarSolidStateProfile solidStateProfile;
    LidarRotaryProfile rotaryProfile;
    uint32_t lostReturns{ 0 };

    isaac::utils::HostBufferBase<float3> hostPcScanBuffer; // TODO pass out gpu or use managed memory.
    isaac::utils::HostBufferBase<float> hostDistanceScanBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityScanBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthScanBuffer;
    isaac::utils::HostBufferBase<float> hostElevationScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdScanBuffer;
    // when keep only positive distance is true, we ouput smaller arrays.
    isaac::utils::HostBufferBase<uint32_t> hostIndexShrunkBuffer;
    isaac::utils::HostBufferBase<float3> hostPcShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostDistanceShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostElevationShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdShrunkBuffer;

    isaac::utils::DeviceBufferBase<float3> pcBuffer; // 3d point cloud
    isaac::utils::DeviceBufferBase<float> distanceBuffer;
    isaac::utils::DeviceBufferBase<float> intensityBuffer;
    isaac::utils::DeviceBufferBase<float> azimuthBuffer;
    isaac::utils::DeviceBufferBase<float> elevationBuffer;

    // TODOMTC EmitterProfile only need distanceCorrectionM, horOffsetM, vertOffsetM for GPU

public:
    static bool compute(OgnIsaacCreateRTXLidarScanBufferDatabase& db)
    {
        // std::cout << "EnterCompute -------------------\n";
        // TODOMTC Streams?  each node should have it's own stream?
        CARB_PROFILE_ZONE(0, "Create RTX Lidar Scan Buffer");
        // safe or passthrough values so we can return without worry anywhere in compute.
        db.outputs.exec() = db.inputs.exec();
        db.outputs.dataPtr() = 0;
        db.outputs.cudaDeviceIndex() = -1; // db.inputs.cudaDeviceIndex();
        db.outputs.bufferSize() = 0;
        db.outputs.width() = 0;
        db.outputs.height() = 1;
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        matrixOutput.SetIdentity();

        db.outputs.intensityPtr() = 0;
        db.outputs.distancePtr() = 0;
        db.outputs.azimuthPtr() = 0;
        db.outputs.elevationPtr() = 0;
        db.outputs.objectIdPtr() = 0;
        db.outputs.indexPtr() = 0; // only if keepOnlyPositiveDistance

        db.outputs.numReturnsPerScan() = 0;
        db.outputs.ticksPerScan() = 0;
        db.outputs.numChannels() = 0;
        db.outputs.numEchos() = 0;
        db.outputs.renderProductPath() = db.inputs.renderProductPath();

        uint8_t* dataHost = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataHost)
        {
            return true;
        }
        auto& state = db.internalState<OgnIsaacCreateRTXLidarScanBuffer>();

        // fill the structure of arrays
        LidarTicks lidarTicksHost;
        LidarReturns lidarReturnsHost;
        LidarParameterType* parameterHost =
            omni::sensors::nv::lidar::fillStructsFromBuffer(dataHost, lidarReturnsHost, lidarTicksHost);
        const uint32_t ticksPerScan = parameterHost->async.ticksPerScan;
        const uint32_t numTicks = parameterHost->async.numTicks;
        const uint32_t numChannels = parameterHost->async.numChannels;
        const uint32_t numEchos = parameterHost->async.numEchos;

        if (numTicks == 0 || numChannels * numEchos == 0)
        {
            return true;
        }

        // This is a gpu buffer generating node.  If the input cudaHandle is -1 (cpu), then just use the host device.
        int cudaDeviceIndex = db.inputs.cudaDeviceIndex();
        if (cudaDeviceIndex == -1)
        {
            if (cudaGetDevice(&cudaDeviceIndex) != cudaError::cudaSuccess)
            {
                CARB_LOG_ERROR("IsaacCreateRTXLidarScanBuffer can't find a cuda device.");
                return false;
            }
        }
        // TODOMTC db.outputs.cudaDeviceIndex() = cudaDeviceIndex;
        std::string curConfig = "";
        pxr::UsdAttribute configAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "sensorModelConfig", db.tokenToString(db.inputs.renderProductPath()));
        if (configAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
        }
        updateLidarConfig(curConfig, state.config, state.scanType, state.rotaryProfile, state.solidStateProfile);

        // TODOMTC Transform applied to previous buffer values is newer, either store transforms, or apply here.
        getTransformFromLidarAsyncParameter(parameterHost->async, matrixOutput); // TODOMTC use moving transoforms?

        // startLocFullScan is the location in a full scan buffer of first element in the incoming data.
        //   startTick is 0 for all solid state, so use the fist emitter Id.  This will usually be 0, unless one of the
        //   previous frames ran over, then it will start at the length of the run over... for now we can just mod the
        //   run over, but TODOMTC deal with lidarReturnsHost.emitterIds[0] == 1 etc...
        bool isSolidState = state.scanType == LidarScanType::kSolidState;
        const uint32_t startLocFullScan =
            numEchos * (isSolidState ? lidarReturnsHost.emitterIds[0] : parameterHost->async.startTick * numChannels);

        // numReturns is the number returns held in the incoming data
        const uint32_t numReturnsInput = numTicks * numChannels * numEchos;

        // numReturnsPerScan is the number or returns in a full scan
        // the numReturnsPerScan computation differ depending on what type of lidar you have.
        // numChannels is always the numEmitters in a rotary, and it is variable in solid state.
        const uint32_t numReturnsPerScan =
            numEchos * (isSolidState ? state.solidStateProfile.numberOfEmitters : ticksPerScan * numChannels);

        db.outputs.numReturnsPerScan() = numReturnsPerScan;
        db.outputs.ticksPerScan() = isSolidState ? 1 : ticksPerScan;
        db.outputs.numChannels() = isSolidState ? state.solidStateProfile.numberOfEmitters : numChannels;
        db.outputs.numEchos() = numEchos;

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();
        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };

        // std::cout << "Before resize  -------------------\n";
        // TODO PASS OUT A GPU INSTEAD OF USING THIS, OR AT LEAST USE MANAGED MEMORY.
        state.hostPcScanBuffer.resize(numReturnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
        state.hostDistanceScanBuffer.resize(numReturnsPerScan, 0);
        state.hostIntensityScanBuffer.resize(numReturnsPerScan, 0);
        state.hostAzimuthScanBuffer.resize(numReturnsPerScan, 0);
        state.hostElevationScanBuffer.resize(numReturnsPerScan, 0);
        state.hostObjectIdScanBuffer.resize(numReturnsPerScan, 0);
        if (keepOnlyPositiveDistance)
        {
            state.hostIndexShrunkBuffer.resize(numReturnsPerScan, 0);
            state.hostPcShrunkBuffer.resize(numReturnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
            state.hostDistanceShrunkBuffer.resize(numReturnsPerScan, 0);
            state.hostIntensityShrunkBuffer.resize(numReturnsPerScan, 0);
            state.hostAzimuthShrunkBuffer.resize(numReturnsPerScan, 0);
            state.hostElevationShrunkBuffer.resize(numReturnsPerScan, 0);
            state.hostObjectIdShrunkBuffer.resize(numReturnsPerScan, 0);
        }

        state.pcBuffer.setDevice(cudaDeviceIndex);
        state.distanceBuffer.setDevice(cudaDeviceIndex);
        state.intensityBuffer.setDevice(cudaDeviceIndex);
        state.azimuthBuffer.setDevice(cudaDeviceIndex);
        state.elevationBuffer.setDevice(cudaDeviceIndex);

        state.pcBuffer.resize(numReturnsInput);
        state.distanceBuffer.resize(numReturnsInput);
        state.intensityBuffer.resize(numReturnsInput);
        state.azimuthBuffer.resize(numReturnsInput);
        state.elevationBuffer.resize(numReturnsInput);

        // If the number or returns is greater then the returns left to fill in the scan, then we need to roll over the
        // remaining to the start
        uint32_t numReturns = numReturnsInput;
        uint32_t numSpilloverReturns = 0;
        if (startLocFullScan + numReturnsInput > numReturnsPerScan)
        {
            numReturns = numReturnsPerScan - startLocFullScan;
            numSpilloverReturns = numReturnsInput - numReturns;
        }


        // std::cout << "Before cuda calls  -------------------\n";
        // These do nothing if the device and size are the same the last time we called this.
        {
            isaac::utils::ScopedDevice scopedDevice(cudaDeviceIndex);
            state.distanceBuffer.copyAsync(lidarReturnsHost.distances, numReturnsInput, cudaMemcpyHostToDevice);
            // objectId
            cudaMemcpyAsync(&state.hostObjectIdScanBuffer.data()[startLocFullScan], lidarReturnsHost.objectIds,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);
            cudaMemcpyAsync(&state.hostObjectIdScanBuffer.data()[0], lidarReturnsHost.objectIds + numReturns,
                            numSpilloverReturns * sizeof(float), cudaMemcpyHostToHost);

            // distance
            cudaMemcpyAsync(&state.hostDistanceScanBuffer.data()[startLocFullScan], lidarReturnsHost.distances,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);
            cudaMemcpyAsync(&state.hostDistanceScanBuffer.data()[0], lidarReturnsHost.distances + numReturns,
                            numSpilloverReturns * sizeof(float), cudaMemcpyHostToHost);
            // intensity
            // TODOMTC Map intensity?
            cudaMemcpyAsync(&state.hostIntensityScanBuffer.data()[startLocFullScan], lidarReturnsHost.intensities,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);
            cudaMemcpyAsync(&state.hostIntensityScanBuffer.data()[0], lidarReturnsHost.intensities + numReturns,
                            numSpilloverReturns * sizeof(float), cudaMemcpyHostToHost);

            state.elevationBuffer.copyAsync(lidarReturnsHost.elevations, numReturnsInput, cudaMemcpyHostToDevice);
            elevation(state.elevationBuffer.data(), state.pcBuffer.data(), state.intensityBuffer.data(),
                      accuracyErrorElevationDeg, numReturnsInput, cudaDeviceIndex);
            // elevation
            cudaMemcpyAsync(&state.hostElevationScanBuffer.data()[startLocFullScan], state.elevationBuffer.data(),
                            numReturns * sizeof(float), cudaMemcpyDeviceToHost);
            cudaMemcpyAsync(&state.hostElevationScanBuffer.data()[0], state.elevationBuffer.data() + numReturns,
                            numSpilloverReturns * sizeof(float), cudaMemcpyDeviceToHost);

            state.azimuthBuffer.copyAsync(lidarReturnsHost.azimuths, numReturnsInput, cudaMemcpyHostToDevice);
            azimuthRightHanded(state.azimuthBuffer.data(), state.pcBuffer.data(), accuracyErrorAzimuthDeg,
                               numReturnsInput, cudaDeviceIndex);
            // azimuth
            cudaMemcpyAsync(&state.hostAzimuthScanBuffer.data()[startLocFullScan], state.azimuthBuffer.data(),
                            numReturns * sizeof(float), cudaMemcpyDeviceToHost);
            cudaMemcpyAsync(&state.hostAzimuthScanBuffer.data()[0], state.azimuthBuffer.data() + numReturns,
                            numSpilloverReturns * sizeof(float), cudaMemcpyDeviceToHost);


            pointCloud(state.pcBuffer.data(), state.intensityBuffer.data(), state.distanceBuffer.data(),
                       numReturnsInput, cudaDeviceIndex);
            // point cloud
            cudaMemcpyAsync(&state.hostPcScanBuffer.data()[startLocFullScan], state.pcBuffer.data(),
                            numReturns * sizeof(float3), cudaMemcpyDeviceToHost);
            cudaMemcpyAsync(&state.hostPcScanBuffer.data()[0], state.pcBuffer.data() + numReturns,
                            numSpilloverReturns * sizeof(float3), cudaMemcpyDeviceToHost);

            cudaDeviceSynchronize();
        }
        db.outputs.exec() = db.inputs.exec();
        // TODOMTC Move this to the GPU
        // TODOMTC output GPU data.
        if (keepOnlyPositiveDistance)
        {
            auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();
            int outSize = 0;
            const float* distScan = state.hostDistanceScanBuffer.data();
            uint32_t* ib = state.hostIndexShrunkBuffer.data(); // index buffer
            // preform sequential stream compaction
            const int rps = numReturnsPerScan;
            for (int i = 0; i < rps; ++i) // starts as max size.
            {
                if (distScan[i] > 0.f)
                {
                    ib[outSize] = i;
                    ++outSize;
                }
            }
            db.outputs.bufferSize() = outSize * sizeof(float3);
            db.outputs.width() = static_cast<uint32_t>(outSize);
            db.outputs.indexPtr() = reinterpret_cast<uint64_t>(ib);
// fill the others
// need to wait for futures?
#define _GATHER_OUTPUT(BUFF_NAME)                                                                                      \
    tasking->addTask(carb::tasking::Priority::eDefault, {},                                                            \
                     [ib, outSize, shrunkBuff = state.host##BUFF_NAME##ShrunkBuffer.data(),                            \
                      scanBuffer = state.host##BUFF_NAME##ScanBuffer.data()]                                           \
                     {                                                                                                 \
                         for (int i = 0; i < outSize; ++i)                                                             \
                         {                                                                                             \
                             shrunkBuff[i] = scanBuffer[ib[i]];                                                        \
                         }                                                                                             \
                     })

#define _GATHER_OUTPUT_SEQUENTIAL(BUFF_NAME)                                                                           \
    {                                                                                                                  \
        const auto* scanBuffer = state.host##BUFF_NAME##ScanBuffer.data();                                             \
        auto* shrunkBuff = state.host##BUFF_NAME##ShrunkBuffer.data();                                                 \
        for (int i = 0; i < outSize; ++i)                                                                              \
        {                                                                                                              \
            shrunkBuff[i] = scanBuffer[ib[i]];                                                                         \
        }                                                                                                              \
    }

            _GATHER_OUTPUT(Pc);
            _GATHER_OUTPUT(Distance);
            _GATHER_OUTPUT(Intensity);
            _GATHER_OUTPUT(Azimuth);
            _GATHER_OUTPUT(Elevation);
            _GATHER_OUTPUT(ObjectId);

#undef _GATHER_OUTPUT

            db.outputs.distancePtr() = reinterpret_cast<uint64_t>(state.hostDistanceShrunkBuffer.data());
            db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcShrunkBuffer.data());
            db.outputs.intensityPtr() = reinterpret_cast<uint64_t>(state.hostIntensityShrunkBuffer.data());
            db.outputs.azimuthPtr() = reinterpret_cast<uint64_t>(state.hostAzimuthShrunkBuffer.data());
            db.outputs.elevationPtr() = reinterpret_cast<uint64_t>(state.hostElevationShrunkBuffer.data());
            db.outputs.objectIdPtr() = reinterpret_cast<uint64_t>(state.hostObjectIdShrunkBuffer.data());
        }
        else
        {
            db.outputs.bufferSize() = state.hostPcScanBuffer.sizeInBytes();
            db.outputs.width() = static_cast<uint32_t>(state.hostPcScanBuffer.size());
            db.outputs.distancePtr() = reinterpret_cast<uint64_t>(state.hostDistanceScanBuffer.data());

            db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcScanBuffer.data());
            db.outputs.intensityPtr() = reinterpret_cast<uint64_t>(state.hostIntensityScanBuffer.data());
            db.outputs.azimuthPtr() = reinterpret_cast<uint64_t>(state.hostAzimuthScanBuffer.data());
            db.outputs.elevationPtr() = reinterpret_cast<uint64_t>(state.hostElevationScanBuffer.data());
            db.outputs.objectIdPtr() = reinterpret_cast<uint64_t>(state.hostObjectIdScanBuffer.data());
        }

        return true;
    }
    static void release(const NodeObj&)
    {
    }
};


REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
/*

        std::cout << "--------------------------------------------------\n"
                  << parameterHost->sync.currentSizeBuffer << " currentSizeBuffer\n"
                  << parameterHost->sync.maxSizeBuffer << " maxSizeBuffer\n"
                  << parameterHost->sync.numTicks << " numTicks\n"
                  << parameterHost->sync.scanStartTimeNs << " scanStartTimeNs\n"
                  << parameterHost->async.numTicks << " numTicks\n"
                  << parameterHost->async.scanFrequency << " scanFrequency\n"
                  << parameterHost->async.ticksPerScan << " ticksPerScan\n"
                  << parameterHost->async.maxSizeBuffer << " maxSizeBuffer\n"
                  << parameterHost->async.currentSizeBuffer << " currentSizeBuffer\n"
                  << parameterHost->async.numChannels << " numChannels\n"
                  << parameterHost->async.numEchos << " numEchos\n"
                  << parameterHost->async.startTimeNs << " startTimeNs\n"
                  << parameterHost->async.deltaTimeNs << " deltaTimeNs\n"
                  << parameterHost->async.scanStartTimeNs << " scanStartTimeNs\n"
                  << parameterHost->async.startTick << " startTick\n"
                  << parameterHost->async.frameStart << " frameStart\n"
                  << parameterHost->async.frameEnd << " frameEnd\n"
                  << state.pcScanBuffer.sizeInBytes() << " state.pcScanBuffer.sizeInBytes()\n"
                  ;
*/
