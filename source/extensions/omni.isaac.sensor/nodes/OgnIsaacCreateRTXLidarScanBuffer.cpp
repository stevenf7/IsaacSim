// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "SensorNodeUtils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/tasking/ITasking.h>

#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/sensors/GenericModelOutput.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <thrust/copy.h>
#include <thrust/device_ptr.h>

#include <OgnIsaacCreateRTXLidarScanBufferDatabase.h>

extern "C" void azimuthDegToRad(float* srcDest, float3* scratch, float accuracyError, int N, int cdi);
extern "C" void elevation(float* srcDest, float3* scratch, float* scratch2, float accuracyError, int N, int cdi);
extern "C" void pointCloudWithTransform(
    float3* srcDest, const float* cosEle, const float* dist, const float3& accuracyError, const double* T, int N, int cdi);
extern "C" void timestamp(int32_t* dest, int32_t* src, uint64_t tickStartTime, int N, int cdi);


namespace omni
{
using namespace sensors;
namespace isaac
{
namespace sensor
{


// The idea of this node is to keep a larger copy of the rtx sensor buffer that holds
// a full 360 scan, updating the locations with the newest available one and keeping
// the rest of the angles the same.
// header
// TODOMTC stop assuming dataHost comes in as CPU when you can make GPU work!
// TODOMTC output GPU!
class OgnIsaacCreateRTXLidarScanBuffer : public LidarConfigHelper
{
private:
    isaac::utils::HostBufferBase<float3> hostPcScanBuffer; // TODO pass out gpu or use managed memory.
    isaac::utils::HostBufferBase<float> hostDistanceScanBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityScanBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthScanBuffer;
    isaac::utils::HostBufferBase<float> hostElevationScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdScanBuffer;
    isaac::utils::HostBufferBase<float3> hostVelocityScanBuffer;
    isaac::utils::HostBufferBase<float3> hostNormalScanBuffer;
    isaac::utils::HostBufferBase<int32_t> hostTimestampScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostEmitterIdScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostMaterialIdScanBuffer;

    // when keep only positive distance is true, we ouput smaller arrays.
    isaac::utils::HostBufferBase<uint32_t> hostIndexShrunkBuffer;
    isaac::utils::HostBufferBase<float3> hostPcShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostDistanceShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthShrunkBuffer;
    isaac::utils::HostBufferBase<float> hostElevationShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdShrunkBuffer;
    isaac::utils::HostBufferBase<float3> hostVelocityShrunkBuffer;
    isaac::utils::HostBufferBase<float3> hostNormalShrunkBuffer;
    isaac::utils::HostBufferBase<int32_t> hostTimestampShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostEmitterIdShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostMaterialIdShrunkBuffer;

    isaac::utils::DeviceBufferBase<float3> pcBuffer; // 3d point cloud
    isaac::utils::DeviceBufferBase<float> distanceBuffer;
    isaac::utils::DeviceBufferBase<float> intensityBuffer;
    isaac::utils::DeviceBufferBase<float> azimuthBuffer;
    isaac::utils::DeviceBufferBase<float> elevationBuffer;
    isaac::utils::DeviceBufferBase<int32_t> deltaTimesBuffer;
    isaac::utils::DeviceBufferBase<int32_t> timestampBuffer;

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

        db.outputs.indexPtr() = 0; // index only if keepOnlyPositiveDistance
        db.outputs.indexBufferSize() = 0;
        db.outputs.intensityPtr() = 0;
        db.outputs.intensityBufferSize() = 0;
        db.outputs.distancePtr() = 0;
        db.outputs.distanceBufferSize() = 0;
        db.outputs.azimuthPtr() = 0;
        db.outputs.azimuthBufferSize() = 0;
        db.outputs.elevationPtr() = 0;
        db.outputs.elevationBufferSize() = 0;
        db.outputs.objectIdPtr() = 0;
        db.outputs.objectIdBufferSize() = 0;
        db.outputs.velocityPtr() = 0;
        db.outputs.velocityBufferSize() = 0;
        db.outputs.normalPtr() = 0;
        db.outputs.normalBufferSize() = 0;
        db.outputs.timestampPtr() = 0;
        db.outputs.timestampBufferSize() = 0;
        db.outputs.emitterIdPtr() = 0;
        db.outputs.emitterIdBufferSize() = 0;
        db.outputs.materialIdPtr() = 0;
        db.outputs.materialIdBufferSize() = 0;

        db.outputs.numReturnsPerScan() = 0;
        db.outputs.ticksPerScan() = 0;
        db.outputs.numChannels() = 0;
        db.outputs.numEchos() = 0;
        db.outputs.renderProductPath() = db.inputs.renderProductPath();

        uint8_t* dataPtr = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataPtr)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacCreateRTXLidarScanBuffer>();

        GenericModelOutputHelper helper(dataPtr);
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, AuxType::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacCreateRTXLidarScanBuffer is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.m_gmo.numElements == 0)
        {
            return true;
        }

        // This is a GPU buffer generating node.  If the input cudaHandle is -1 (CPU), then just use the host device.
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
        // TODOMTC use the auxPoints->scanComplete flag to just build on this till a complete scan?
        state.updateLidarConfig(db.tokenToString(db.inputs.renderProductPath()));

        getTransformFromSensorPose(helper.m_gmo.frameEnd, matrixOutput); // TODOMTC interp moving transforms?

        const omni::sensors::LidarAuxiliaryData* auxPoints =
            static_cast<const omni::sensors::LidarAuxiliaryData*>(helper.m_gmo.auxiliaryData); // gpc.auxiliaryPoints);
        // startLocFullScan is the location in a full scan buffer of first element in the incoming data.
        //   startTick is 0 for all solid state, so use the fist emitter Id.  This will usually be 0, unless one of the
        //   previous frames ran over, then it will start at the length of the run over.
        bool isSolidState = state.scanType == LidarScanType::kSolidState;
        const uint32_t startLocFullScan =
            state.getNumEchos() * (isSolidState ? helper.getEmitterId(0) : helper.getTickId(0) * state.getNumChannels());

        //  numReturnsInput is the number returns held in the incoming data
        const uint32_t numReturnsInput = helper.m_gmo.numElements;

        db.outputs.numReturnsPerScan() = state.getReturnsPerScan();
        db.outputs.ticksPerScan() = state.getTicksPerScan();
        db.outputs.numChannels() = state.getNumChannels();
        db.outputs.numEchos() = state.getNumEchos();

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();
        float3 accuracyErrorPosition =
            make_float3(db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                        db.inputs.accuracyErrorPosition()[2]);

        // std::cout << "Before resize  -------------------\n";
        // TODO PASS OUT A GPU INSTEAD OF USING THIS, OR AT LEAST USE MANAGED MEMORY.
        // These do nothing if the device and size are the same the last time we called this.
        state.hostPcScanBuffer.resize(state.getReturnsPerScan(), make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputDistance())
            state.hostDistanceScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputIntensity())
            state.hostIntensityScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputAzimuth())
            state.hostAzimuthScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputElevation())
            state.hostElevationScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputObjectId())
            state.hostObjectIdScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputVelocity())
            state.hostVelocityScanBuffer.resize(state.getReturnsPerScan(), make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputNormal())
            state.hostNormalScanBuffer.resize(state.getReturnsPerScan(), make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputTimestamp())
            state.hostTimestampScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputEmitterId())
            state.hostEmitterIdScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (db.inputs.outputMaterialId())
            state.hostMaterialIdScanBuffer.resize(state.getReturnsPerScan(), 0);
        if (keepOnlyPositiveDistance)
        {
            state.hostIndexShrunkBuffer.resize(state.getReturnsPerScan(), 0);
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
        // to compute delta times we also need tick info
        if (db.inputs.outputTimestamp())
        {
            state.timestampBuffer.setDevice(cudaDeviceIndex);
            state.deltaTimesBuffer.setDevice(cudaDeviceIndex);

            state.timestampBuffer.resize(numReturnsInput);
            state.deltaTimesBuffer.resize(numReturnsInput);
        }

        // If the number or returns is greater then the returns left to fill in the scan, then we need to roll over the
        // remaining to the start
        uint32_t numReturns = numReturnsInput;
        uint32_t numSpilloverReturns = 0;
        if (startLocFullScan + numReturnsInput > state.getReturnsPerScan())
        {
            numReturns = state.getReturnsPerScan() - startLocFullScan;
            numSpilloverReturns = numReturnsInput - numReturns;
        }


        // std::cout << "Before cuda calls  -------------------\n";
        {
            isaac::utils::ScopedDevice scopedDev(cudaDeviceIndex);
            if (db.inputs.outputTimestamp())
            {
                state.deltaTimesBuffer.copyAsync(
                    helper.m_gmo.elements.timeOffsetNs, numReturnsInput, cudaMemcpyHostToDevice);
                // uint64_t *dest, const uint32_t *src, const uint64_t *tickSource, int tickSize, int N, int cdi)
                timestamp(state.timestampBuffer.data(), state.deltaTimesBuffer.data(),
                          helper.m_gmo.frameStart.timestampNs, numReturnsInput, cudaDeviceIndex);
                wrapCudaMemcpyAsync(state.hostTimestampScanBuffer.data(), state.timestampBuffer.data(),
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyDeviceToHost);
            }
            state.elevationBuffer.copyAsync(helper.m_gmo.elements.y, numReturnsInput, cudaMemcpyHostToDevice);
            state.distanceBuffer.copyAsync(helper.m_gmo.elements.z, numReturnsInput, cudaMemcpyHostToDevice);
            state.azimuthBuffer.copyAsync(helper.m_gmo.elements.x, numReturnsInput, cudaMemcpyHostToDevice);

            if (db.inputs.outputDistance())
                wrapCudaMemcpyAsync(state.hostDistanceScanBuffer.data(), helper.m_gmo.elements.z, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputVelocity() &&
                (auxPoints->filledAuxMembers & LidarAuxHas::VELOCITIES) == LidarAuxHas::VELOCITIES)
                wrapCudaMemcpyAsync(state.hostVelocityScanBuffer.data(), (float3*)auxPoints->velocities,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputObjectId())
                wrapCudaMemcpyAsync(state.hostObjectIdScanBuffer.data(), auxPoints->objId, startLocFullScan, numReturns,
                                    numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputIntensity())
                wrapCudaMemcpyAsync(state.hostIntensityScanBuffer.data(), helper.m_gmo.elements.scalar,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputNormal() &&
                (auxPoints->filledAuxMembers & LidarAuxHas::HIT_NORMALS) == LidarAuxHas::HIT_NORMALS)
                wrapCudaMemcpyAsync(state.hostNormalScanBuffer.data(), (float3*)auxPoints->hitNormals, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputEmitterId())
                wrapCudaMemcpyAsync(state.hostEmitterIdScanBuffer.data(), auxPoints->emitterId, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputMaterialId())
                wrapCudaMemcpyAsync(state.hostMaterialIdScanBuffer.data(), auxPoints->matId, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);

            elevation(state.elevationBuffer.data(), state.pcBuffer.data(), state.intensityBuffer.data(),
                      accuracyErrorElevationDeg, numReturnsInput, cudaDeviceIndex);
            if (db.inputs.outputElevation())
                wrapCudaMemcpyAsync(state.hostElevationScanBuffer.data(), state.elevationBuffer.data(),
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyDeviceToHost);

            azimuthDegToRad(state.azimuthBuffer.data(), state.pcBuffer.data(), accuracyErrorAzimuthDeg, numReturnsInput,
                            cudaDeviceIndex);
            if (db.inputs.outputAzimuth())
                wrapCudaMemcpyAsync(state.hostAzimuthScanBuffer.data(), state.azimuthBuffer.data(), startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyDeviceToHost);

            pointCloudWithTransform(state.pcBuffer.data(), state.intensityBuffer.data(), state.distanceBuffer.data(),
                                    accuracyErrorPosition, db.inputs.transformPoints() ? matrixOutput.data() : nullptr,
                                    numReturnsInput, cudaDeviceIndex);
            wrapCudaMemcpyAsync(state.hostPcScanBuffer.data(), state.pcBuffer.data(), startLocFullScan, numReturns,
                                numSpilloverReturns, cudaMemcpyDeviceToHost);

            cudaDeviceSynchronize();
        }
        db.outputs.exec() = db.inputs.exec();
        // TODOMTC Move this to the GPU
        // TODOMTC output GPU data.
        int outSize = state.getReturnsPerScan();
        if (keepOnlyPositiveDistance)
        {
            CARB_PROFILE_ZONE(0, "Create RTX Lidar Scan Buffer keepOnlyPositiveDistance ");
            auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();
            outSize = 0;
            const float* distScan = state.hostDistanceScanBuffer.data();
            uint32_t* ib = state.hostIndexShrunkBuffer.data(); // index buffer
            // preform sequential stream compaction
            const int rps = state.getReturnsPerScan();
            for (int i = 0; i < rps; ++i) // starts as max size.
            {
                if (distScan[i] > 0.f)
                {
                    ib[outSize] = i;
                    ++outSize;
                }
            }
            // Could move the rest of these to dynamic but may cause hickups?
            state.hostPcShrunkBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
            if (db.inputs.outputDistance())
                state.hostDistanceShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputIntensity())
                state.hostIntensityShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputAzimuth())
                state.hostAzimuthShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputElevation())
                state.hostElevationShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputObjectId())
                state.hostObjectIdShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputVelocity())
                state.hostVelocityShrunkBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
            if (db.inputs.outputNormal())
                state.hostNormalShrunkBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
            if (db.inputs.outputTimestamp())
                state.hostTimestampShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputEmitterId())
                state.hostEmitterIdShrunkBuffer.resize(outSize, 0);
            if (db.inputs.outputMaterialId())
                state.hostMaterialIdShrunkBuffer.resize(outSize, 0);
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
#define _GATHER_OUTPUT_IF(BUFF_NAME)                                                                                   \
    if (db.inputs.output##BUFF_NAME())                                                                                 \
    _GATHER_OUTPUT(BUFF_NAME)


#define _GATHER_OUTPUT_SEQUENTIAL(BUFF_NAME)                                                                           \
    {                                                                                                                  \
        const auto* scanBuffer = state.host##BUFF_NAME##ScanBuffer.data();                                             \
        auto* shrunkBuff = state.host##BUFF_NAME##ShrunkBuffer.data();                                                 \
        for (int i = 0; i < outSize; ++i)                                                                              \
        {                                                                                                              \
            shrunkBuff[i] = scanBuffer[ib[i]];                                                                         \
        }                                                                                                              \
    }
#define _GATHER_OUTPUT_SEQUENTIAL_IF(BUFF_NAME)                                                                        \
    if (db.inputs.output##BUFF_NAME())                                                                                 \
    _GATHER_OUTPUT_SEQUENTIAL(BUFF_NAME)

            _GATHER_OUTPUT(Pc);
            _GATHER_OUTPUT_IF(Distance);
            _GATHER_OUTPUT_IF(Intensity);
            _GATHER_OUTPUT_IF(Azimuth);
            _GATHER_OUTPUT_IF(Elevation);
            _GATHER_OUTPUT_IF(ObjectId);
            _GATHER_OUTPUT_IF(Velocity);
            _GATHER_OUTPUT_IF(Normal);
            _GATHER_OUTPUT_IF(Timestamp);
            _GATHER_OUTPUT_IF(EmitterId);
            _GATHER_OUTPUT_IF(MaterialId);

#undef _GATHER_OUTPUT
#undef _GATHER_OUTPUT_SEQUENTIAL

            db.outputs.indexPtr() = reinterpret_cast<uint64_t>(ib);
            db.outputs.indexBufferSize() = outSize * sizeof(uint32_t);

            db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcShrunkBuffer.data());
            db.outputs.distancePtr() = reinterpret_cast<uint64_t>(state.hostDistanceShrunkBuffer.data());
            db.outputs.intensityPtr() = reinterpret_cast<uint64_t>(state.hostIntensityShrunkBuffer.data());
            db.outputs.azimuthPtr() = reinterpret_cast<uint64_t>(state.hostAzimuthShrunkBuffer.data());
            db.outputs.elevationPtr() = reinterpret_cast<uint64_t>(state.hostElevationShrunkBuffer.data());
            db.outputs.objectIdPtr() = reinterpret_cast<uint64_t>(state.hostObjectIdShrunkBuffer.data());
            db.outputs.velocityPtr() = reinterpret_cast<uint64_t>(state.hostVelocityShrunkBuffer.data());
            db.outputs.normalPtr() = reinterpret_cast<uint64_t>(state.hostNormalShrunkBuffer.data());
            db.outputs.timestampPtr() = reinterpret_cast<uint64_t>(state.hostTimestampShrunkBuffer.data());
            db.outputs.emitterIdPtr() = reinterpret_cast<uint64_t>(state.hostEmitterIdShrunkBuffer.data());
            db.outputs.materialIdPtr() = reinterpret_cast<uint64_t>(state.hostMaterialIdShrunkBuffer.data());
        }
        else
        {
            db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcScanBuffer.data());
            db.outputs.distancePtr() = reinterpret_cast<uint64_t>(state.hostDistanceScanBuffer.data());
            db.outputs.intensityPtr() = reinterpret_cast<uint64_t>(state.hostIntensityScanBuffer.data());
            db.outputs.azimuthPtr() = reinterpret_cast<uint64_t>(state.hostAzimuthScanBuffer.data());
            db.outputs.elevationPtr() = reinterpret_cast<uint64_t>(state.hostElevationScanBuffer.data());
            db.outputs.objectIdPtr() = reinterpret_cast<uint64_t>(state.hostObjectIdScanBuffer.data());
            db.outputs.velocityPtr() = reinterpret_cast<uint64_t>(state.hostVelocityScanBuffer.data());
            db.outputs.normalPtr() = reinterpret_cast<uint64_t>(state.hostNormalScanBuffer.data());
            db.outputs.timestampPtr() = reinterpret_cast<uint64_t>(state.hostTimestampScanBuffer.data());
            db.outputs.emitterIdPtr() = reinterpret_cast<uint64_t>(state.hostEmitterIdScanBuffer.data());
            db.outputs.materialIdPtr() = reinterpret_cast<uint64_t>(state.hostMaterialIdScanBuffer.data());
        }
        db.outputs.width() = static_cast<uint32_t>(outSize);
        db.outputs.bufferSize() = outSize * sizeof(float3);
        if (db.inputs.outputDistance())
            db.outputs.distanceBufferSize() = outSize * sizeof(float);
        if (db.inputs.outputIntensity())
            db.outputs.intensityBufferSize() = outSize * sizeof(float);
        if (db.inputs.outputAzimuth())
            db.outputs.azimuthBufferSize() = outSize * sizeof(float);
        if (db.inputs.outputElevation())
            db.outputs.elevationBufferSize() = outSize * sizeof(float);
        if (db.inputs.outputObjectId())
            db.outputs.objectIdBufferSize() = outSize * sizeof(uint32_t);
        if (db.inputs.outputVelocity())
            db.outputs.velocityBufferSize() = outSize * sizeof(float3);
        if (db.inputs.outputNormal())
            db.outputs.normalBufferSize() = outSize * sizeof(float3);
        if (db.inputs.outputTimestamp())
            db.outputs.timestampBufferSize() = outSize * sizeof(uint64_t);
        if (db.inputs.outputEmitterId())
            db.outputs.emitterIdBufferSize() = outSize * sizeof(uint32_t);
        if (db.inputs.outputMaterialId())
            db.outputs.materialIdBufferSize() = outSize * sizeof(uint32_t);

        return true;
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
