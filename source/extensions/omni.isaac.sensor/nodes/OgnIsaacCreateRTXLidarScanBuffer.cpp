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

#include <internal/omni/sensors/lidar/LidarReturnHelper.h>
#include <omni/isaac/utils/Buffer.h>
#include <omni/isaac/utils/ScopedCudaDevice.h>
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

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
    // xxxScanBuffer holds the whole scan, and xxxBuffer holds only the current data from dataPtr()
    // isaac::utils::DeviceBufferBase<float3> pcScanBuffer; // 3d point cloud
    // isaac::utils::DeviceBufferBase<float> distanceScanBuffer; // pass through but needed to compute pc
    // isaac::utils::DeviceBufferBase<float> intensityScanBuffer; // pass through
    // isaac::utils::DeviceBufferBase<float> azimuthScanBuffer;
    // isaac::utils::DeviceBufferBase<float> elevationScanBuffer;
    // isaac::utils::DeviceBufferBase<uint32_t> objectIdScanBuffer; // pass through
    // isaac::utils::DeviceBufferBase<uint32_t> indexScanBuffer;

    isaac::utils::HostBufferBase<float3> hostPcScanBuffer; // TODO pass out gpu or use managed memory.
    isaac::utils::HostBufferBase<float> hostDistanceScanBuffer;
    isaac::utils::HostBufferBase<float> hostIntensityScanBuffer;
    isaac::utils::HostBufferBase<float> hostAzimuthScanBuffer;
    isaac::utils::HostBufferBase<float> hostElevationScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostObjectIdScanBuffer;
    isaac::utils::HostBufferBase<uint32_t> hostIndexScanBuffer;

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
        CARB_PROFILE_ZONE(0, "Create RTX Lidar 360 Buffer");
        // safe or passthrough values so we can return without worry anywhere in compute.
        db.outputs.exec() = db.inputs.exec();
        db.outputs.dataPtr() = 0;
        db.outputs.cudaDeviceIndex() = -1; // db.inputs.cudaDeviceIndex();
        db.outputs.bufferSize() = 0;
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        matrixOutput.SetIdentity();

        db.outputs.intensityPtr() = 0;
        db.outputs.distancePtr() = 0;
        db.outputs.azimuthPtr() = 0;
        db.outputs.elevationPtr() = 0;
        db.outputs.objectIdPtr() = 0;
        db.outputs.indexPtr() = 0; // only if keepOnlyPositiveDistance

        db.outputs.returnsPerScan() = 0;
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
        const uint32_t startTick = parameterHost->async.startTick;
        uint32_t numTicks = parameterHost->async.numTicks;
        const uint32_t numChannels = parameterHost->async.numChannels;
        const uint32_t numEchos = parameterHost->async.numEchos;
        // is there ever a buffer that is part in this scan and part in the next?  If so, truncate and lose data.
        if (numTicks + startTick > ticksPerScan)
        {
            numTicks = ticksPerScan - startTick;
            CARB_LOG_WARN("WARNING -  You lost a little scan data!");
        }
        const uint32_t numReturns = numTicks * numChannels * numEchos;
        const uint32_t returnsPerScan = ticksPerScan * numChannels * numEchos;
        const uint32_t scanLoc = startTick * numChannels * numEchos;
        // TODOMTC MAKE THIS WORK.
        // You can shrink into an earlier scan location by using the index. So to write a first set of scans...
        // or just only shrink at the end

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

        // async.pose is [X, Y, Z, W].
        // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
        omni::math::linalg::vec3d posM{ parameterHost->async.frameEnd.posM[0], parameterHost->async.frameEnd.posM[1],
                                        parameterHost->async.frameEnd.posM[2] };
        omni::math::linalg::quatd pose{ parameterHost->async.frameEnd.orientation[3],
                                        parameterHost->async.frameEnd.orientation[0],
                                        parameterHost->async.frameEnd.orientation[1],
                                        parameterHost->async.frameEnd.orientation[2] };
        matrixOutput.SetRotateOnly(pose);
        matrixOutput.SetTranslateOnly(posM);

        db.outputs.returnsPerScan() = returnsPerScan;
        db.outputs.ticksPerScan() = ticksPerScan;
        db.outputs.numChannels() = numChannels;
        db.outputs.numEchos() = numEchos;
        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();
        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };

        // std::cout << "Before resize  -------------------\n";
        // TODO PASS OUT A GPU INSTEAD OF USING THIS, OR AT LEAST USE MANAGED MEMORY.
        state.hostPcScanBuffer.resize(returnsPerScan, make_float3(0.0f, 0.0f, 0.0f));
        state.hostDistanceScanBuffer.resize(returnsPerScan, 0);
        state.hostIntensityScanBuffer.resize(returnsPerScan, 0);
        state.hostAzimuthScanBuffer.resize(returnsPerScan, 0);
        state.hostElevationScanBuffer.resize(returnsPerScan, 0);
        state.hostObjectIdScanBuffer.resize(returnsPerScan, 0);
        if (keepOnlyPositiveDistance)
            state.hostIndexScanBuffer.resize(returnsPerScan, 0);

        // these should be noop if buffers are not changed in size or cuda device.
        // state.pcScanBuffer.setDevice(cudaDeviceIndex);
        // state.distanceScanBuffer.setDevice(cudaDeviceIndex);
        // state.intensityScanBuffer.setDevice(cudaDeviceIndex);
        // state.azimuthScanBuffer.setDevice(cudaDeviceIndex);
        // state.elevationScanBuffer.setDevice(cudaDeviceIndex);
        // state.objectIdScanBuffer.setDevice(cudaDeviceIndex);
        // state.indexScanBuffer.setDevice(cudaDeviceIndex);

        state.pcBuffer.setDevice(cudaDeviceIndex);
        state.distanceBuffer.setDevice(cudaDeviceIndex);
        state.intensityBuffer.setDevice(cudaDeviceIndex);
        state.azimuthBuffer.setDevice(cudaDeviceIndex);
        state.elevationBuffer.setDevice(cudaDeviceIndex);

        // state.pcScanBuffer.resize(returnsPerScan);
        // state.distanceScanBuffer.resize(returnsPerScan);
        // state.intensityScanBuffer.resize(returnsPerScan);
        // state.azimuthScanBuffer.resize(returnsPerScan);
        // state.elevationScanBuffer.resize(returnsPerScan);
        // state.objectIdScanBuffer.resize(returnsPerScan);
        // state.indexScanBuffer.resize(returnsPerScan);

        state.pcBuffer.resize(numReturns);
        state.distanceBuffer.resize(numReturns);
        state.intensityBuffer.resize(numReturns);
        state.azimuthBuffer.resize(numReturns);
        state.elevationBuffer.resize(numReturns);

        // std::cout << "Before cuda calls  -------------------\n";
        // These do nothing if the device and size are the same the last time we called this.
        {
            isaac::utils::ScopedDevice scopedDevice(cudaDeviceIndex);
            state.distanceBuffer.copyAsync(lidarReturnsHost.distances, numReturns, cudaMemcpyHostToDevice);
            // objectId
            cudaMemcpyAsync(&state.hostObjectIdScanBuffer.data()[scanLoc], lidarReturnsHost.objectIds,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);
            // distance
            cudaMemcpyAsync(&state.hostDistanceScanBuffer.data()[scanLoc], lidarReturnsHost.distances,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);
            // intensity
            // TODOMTC Map intensity?
            cudaMemcpyAsync(&state.hostIntensityScanBuffer.data()[scanLoc], lidarReturnsHost.intensities,
                            numReturns * sizeof(float), cudaMemcpyHostToHost);

            state.elevationBuffer.copyAsync(lidarReturnsHost.elevations, numReturns, cudaMemcpyHostToDevice);
            elevation(state.elevationBuffer.data(), state.pcBuffer.data(), state.intensityBuffer.data(),
                      accuracyErrorElevationDeg, numReturns, cudaDeviceIndex);
            // elevation
            cudaMemcpyAsync(&state.hostElevationScanBuffer.data()[scanLoc], state.elevationBuffer.data(),
                            numReturns * sizeof(float), cudaMemcpyDeviceToHost);

            state.azimuthBuffer.copyAsync(lidarReturnsHost.azimuths, numReturns, cudaMemcpyHostToDevice);
            azimuthRightHanded(state.azimuthBuffer.data(), state.pcBuffer.data(), accuracyErrorAzimuthDeg, numReturns,
                               cudaDeviceIndex);
            // azimuth
            cudaMemcpyAsync(&state.hostAzimuthScanBuffer.data()[scanLoc], state.azimuthBuffer.data(),
                            numReturns * sizeof(float), cudaMemcpyDeviceToHost);


            pointCloud(state.pcBuffer.data(), state.intensityBuffer.data(), state.distanceBuffer.data(), numReturns,
                       cudaDeviceIndex);
            // point cloud
            cudaMemcpyAsync(&state.hostPcScanBuffer.data()[scanLoc], state.pcBuffer.data(), numReturns * sizeof(float3),
                            cudaMemcpyDeviceToHost);

            cudaDeviceSynchronize();
        }
        db.outputs.exec() = db.inputs.exec();
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcScanBuffer.data());
        db.outputs.bufferSize() = state.hostPcScanBuffer.sizeInBytes();
        db.outputs.intensityPtr() = reinterpret_cast<uint64_t>(state.hostIntensityScanBuffer.data());
        db.outputs.distancePtr() = reinterpret_cast<uint64_t>(state.hostDistanceScanBuffer.data());
        db.outputs.azimuthPtr() = reinterpret_cast<uint64_t>(state.hostAzimuthScanBuffer.data());
        db.outputs.elevationPtr() = reinterpret_cast<uint64_t>(state.hostElevationScanBuffer.data());
        db.outputs.objectIdPtr() = reinterpret_cast<uint64_t>(state.hostObjectIdScanBuffer.data());
        if (keepOnlyPositiveDistance)
            db.outputs.indexPtr() = reinterpret_cast<uint64_t>(state.hostIndexScanBuffer.data());

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
