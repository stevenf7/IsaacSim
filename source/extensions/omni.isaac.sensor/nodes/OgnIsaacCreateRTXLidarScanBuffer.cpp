// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
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
extern "C" void pointCloudWithTransform(
    float3* srcDest, const float* cosEle, const float* dist, const float3& accuracyError, const double* T, int N, int cdi);
extern "C" void timestamp(uint64_t* dest, const uint32_t* src, const uint64_t* tickSource, int tickSize, int N, int cdi);

template <class T>
void wrapCudaMemcpyAsync(T* dst, const T* src, uint32_t startLoc, uint32_t num, uint32_t numSpillover, cudaMemcpyKind kind)
{

    unsigned long dataSize = sizeof(T);
    cudaMemcpyAsync(dst + startLoc, src, num * dataSize, kind);
    cudaMemcpyAsync(dst, src + num, numSpillover * dataSize, kind);
}

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

    isaac::utils::HostBufferBase<float3> hostPcScanBuffer; // TODO pass out gpu or use managed memory.
    isaac::utils::HostBufferBase<float> hostDistanceScanBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityScanBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthScanBuffer;
    isaac::utils::HostBufferBase<float> hostElevationScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdScanBuffer;
    isaac::utils::HostBufferBase<float3> hostVelocityScanBuffer;
    isaac::utils::HostBufferBase<float3> hostNormalScanBuffer;
    isaac::utils::HostBufferBase<uint64_t> hostTimestampScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostEmitterIdScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostBeamIdScanBuffer;
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
    isaac::utils::HostBufferBase<uint64_t> hostTimestampShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostEmitterIdShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostBeamIdShrunkBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostMaterialIdShrunkBuffer;

    isaac::utils::DeviceBufferBase<float3> pcBuffer; // 3d point cloud
    isaac::utils::DeviceBufferBase<float> distanceBuffer;
    isaac::utils::DeviceBufferBase<float> intensityBuffer;
    isaac::utils::DeviceBufferBase<float> azimuthBuffer;
    isaac::utils::DeviceBufferBase<float> elevationBuffer;
    isaac::utils::DeviceBufferBase<uint32_t> deltaTimesBuffer;
    isaac::utils::DeviceBufferBase<uint64_t> tickTimestampBuffer;
    isaac::utils::DeviceBufferBase<uint64_t> timestampBuffer;

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
        db.outputs.beamIdPtr() = 0;
        db.outputs.beamIdBufferSize() = 0;
        db.outputs.materialIdPtr() = 0;
        db.outputs.materialIdBufferSize() = 0;

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
        auto& state = db.perInstanceState<OgnIsaacCreateRTXLidarScanBuffer>();

        // fill the structure of arrays
        LidarTicks lidarTicksHost;
        LidarReturns lidarReturnsHost;
        LidarParameterType* parameterHost = saferFillStructsFromBuffer(dataHost, lidarReturnsHost, lidarTicksHost);
        if (!parameterHost)
            return true;
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

        getTransformFromLidarAsyncParameter(parameterHost->async, matrixOutput); // TODOMTC interp moving transforms?

        // startLocFullScan is the location in a full scan buffer of first element in the incoming data.
        //   startTick is 0 for all solid state, so use the fist emitter Id.  This will usually be 0, unless one of the
        //   previous frames ran over, then it will start at the length of the run over.
        bool isSolidState = state.scanType == LidarScanType::kSolidState;
        const uint32_t startLocFullScan =
            numEchos * (isSolidState ? lidarReturnsHost.emitterIds[0] : parameterHost->async.startTick * numChannels);

        // numReturnsInput is the number returns held in the incoming data
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
        float3 accuracyErrorPosition =
            make_float3(db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                        db.inputs.accuracyErrorPosition()[2]);

        // std::cout << "Before resize  -------------------\n";
        // TODO PASS OUT A GPU INSTEAD OF USING THIS, OR AT LEAST USE MANAGED MEMORY.
        // These do nothing if the device and size are the same the last time we called this.
        state.hostPcScanBuffer.resize(numReturnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputDistance())
            state.hostDistanceScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputIntensity())
            state.hostIntensityScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputAzimuth())
            state.hostAzimuthScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputElevation())
            state.hostElevationScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputObjectId())
            state.hostObjectIdScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputVelocity())
            state.hostVelocityScanBuffer.resize(numReturnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputNormal())
            state.hostNormalScanBuffer.resize(numReturnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
        if (db.inputs.outputTimestamp())
            state.hostTimestampScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputEmitterId())
            state.hostEmitterIdScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputBeamId())
            state.hostBeamIdScanBuffer.resize(numReturnsPerScan, 0);
        if (db.inputs.outputMaterialId())
            state.hostMaterialIdScanBuffer.resize(numReturnsPerScan, 0);
        if (keepOnlyPositiveDistance)
        {
            state.hostIndexShrunkBuffer.resize(numReturnsPerScan, 0);
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
            state.tickTimestampBuffer.setDevice(cudaDeviceIndex);
            state.timestampBuffer.resize(numReturnsInput);
            state.deltaTimesBuffer.resize(numReturnsInput);
            state.tickTimestampBuffer.resize(numTicks);
        }

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
        {
            isaac::utils::ScopedDevice scopedDev(cudaDeviceIndex);
            if (db.inputs.outputTimestamp())
            {
                state.deltaTimesBuffer.copyAsync(lidarReturnsHost.deltaTimes, numReturnsInput, cudaMemcpyHostToDevice);
                state.tickTimestampBuffer.copyAsync(lidarTicksHost.timestamps, numTicks, cudaMemcpyHostToDevice);
                // uint64_t *dest, const uint32_t *src, const uint64_t *tickSource, int tickSize, int N, int cdi)
                timestamp(state.timestampBuffer.data(), state.deltaTimesBuffer.data(), state.tickTimestampBuffer.data(),
                          numEchos * numChannels, numReturnsInput, cudaDeviceIndex);
                wrapCudaMemcpyAsync(state.hostTimestampScanBuffer.data(), state.timestampBuffer.data(),
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyDeviceToHost);
            }
            state.elevationBuffer.copyAsync(lidarReturnsHost.elevations, numReturnsInput, cudaMemcpyHostToDevice);
            state.distanceBuffer.copyAsync(lidarReturnsHost.distances, numReturnsInput, cudaMemcpyHostToDevice);
            state.azimuthBuffer.copyAsync(lidarReturnsHost.azimuths, numReturnsInput, cudaMemcpyHostToDevice);

            if (db.inputs.outputDistance())
                wrapCudaMemcpyAsync(state.hostDistanceScanBuffer.data(), lidarReturnsHost.distances, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputVelocity())
                wrapCudaMemcpyAsync(state.hostVelocityScanBuffer.data(), (float3*)lidarReturnsHost.velocities,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputObjectId())
                wrapCudaMemcpyAsync(state.hostObjectIdScanBuffer.data(), lidarReturnsHost.objectIds, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputIntensity())
                wrapCudaMemcpyAsync(state.hostIntensityScanBuffer.data(), lidarReturnsHost.intensities,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputNormal())
                wrapCudaMemcpyAsync(state.hostNormalScanBuffer.data(), (float3*)lidarReturnsHost.hitPointNormals,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputEmitterId())
                wrapCudaMemcpyAsync(state.hostEmitterIdScanBuffer.data(), lidarReturnsHost.emitterIds, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputBeamId())
                wrapCudaMemcpyAsync(state.hostBeamIdScanBuffer.data(), lidarReturnsHost.beamIds, startLocFullScan,
                                    numReturns, numSpilloverReturns, cudaMemcpyHostToHost);
            if (db.inputs.outputMaterialId())
                wrapCudaMemcpyAsync(state.hostMaterialIdScanBuffer.data(), lidarReturnsHost.materialIds,
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyHostToHost);

            elevation(state.elevationBuffer.data(), state.pcBuffer.data(), state.intensityBuffer.data(),
                      accuracyErrorElevationDeg, numReturnsInput, cudaDeviceIndex);
            if (db.inputs.outputElevation())
                wrapCudaMemcpyAsync(state.hostElevationScanBuffer.data(), state.elevationBuffer.data(),
                                    startLocFullScan, numReturns, numSpilloverReturns, cudaMemcpyDeviceToHost);

            azimuthRightHanded(state.azimuthBuffer.data(), state.pcBuffer.data(), accuracyErrorAzimuthDeg,
                               numReturnsInput, cudaDeviceIndex);
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
        int outSize = numReturnsPerScan;
        if (keepOnlyPositiveDistance)
        {
            auto tasking = carb::getCachedInterface<carb::tasking::ITasking>();
            outSize = 0;
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
            if (db.inputs.outputBeamId())
                state.hostBeamIdShrunkBuffer.resize(outSize, 0);
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
            _GATHER_OUTPUT_IF(BeamId);
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
            db.outputs.beamIdPtr() = reinterpret_cast<uint64_t>(state.hostBeamIdShrunkBuffer.data());
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
            db.outputs.beamIdPtr() = reinterpret_cast<uint64_t>(state.hostBeamIdScanBuffer.data());
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
        if (db.inputs.outputBeamId())
            db.outputs.beamIdBufferSize() = outSize * sizeof(uint32_t);
        if (db.inputs.outputMaterialId())
            db.outputs.materialIdBufferSize() = outSize * sizeof(uint32_t);

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
