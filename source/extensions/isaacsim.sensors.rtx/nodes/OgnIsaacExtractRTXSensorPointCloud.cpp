// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "GenericModelOutput.h"
#include "OgnIsaacExtractRTXSensorPointCloudDatabase.h"
#include "SensorNodeUtils.h"
#include "isaacsim/core/includes/Buffer.h"
#include "isaacsim/core/includes/ScopedCudaDevice.h"
#include "isaacsim/core/includes/UsdUtilities.h"

extern "C" void azimuthDegToRad(float* srcDest, float3* scratch, float accuracyError, int n, int cdi);
extern "C" void elevation(float* srcDest, float3* scratch, float* scratch2, float accuracyError, int n, int cdi);
extern "C" void pointCloudWithTransform(
    float3* srcDest, const float* cosEle, const float* dist, const float3& accuracyError, const double* t, int n, int cdi);

extern "C" void cartesianToSpherical(float3* srcDest, float* azimuth, float* elevation, float* range, int N, int cdi);

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

class OgnIsaacExtractRTXSensorPointCloud
{
private:
    isaacsim::core::includes::HostBufferBase<float3> hostPcBuffer;
    isaacsim::core::includes::DeviceBufferBase<float3> m_pcBuffer; // 3d point cloud
    isaacsim::core::includes::DeviceBufferBase<float> m_scratchBuffer1;
    isaacsim::core::includes::DeviceBufferBase<float> m_scratchBuffer2;
    isaacsim::core::includes::DeviceBufferBase<float> m_scratchBuffer3;
    isaacsim::core::includes::DeviceBufferBase<float> m_scratchBuffer4;

public:
    static bool compute(OgnIsaacExtractRTXSensorPointCloudDatabase& db)
    {
        // Disable downstream execution by default
        db.outputs.exec() = kExecutionAttributeStateDisabled;

        uint8_t* gmoBufferPointer = reinterpret_cast<uint8_t*>(db.inputs.gmoBufferPointer());
        // no reason to update the scan buffer if there is no dataHost
        if (!gmoBufferPointer)
        {
            CARB_LOG_WARN("IsaacExtractRTXSensorPointCloud: gmoBufferPointer input is empty.");
            return false;
        }
        // This is a GPU buffer generating node.  If the input cudaHandle is -1 (CPU), then just use the host device.
        int gmoDeviceIndex = db.inputs.gmoDeviceIndex();
        cudaDeviceProp cudaDeviceProperties;
        if (gmoDeviceIndex != -1 &&
            cudaGetDeviceProperties(&cudaDeviceProperties, gmoDeviceIndex) != cudaError::cudaSuccess)
        {
            CARB_LOG_ERROR("IsaacComputeRTXLidarFlatScan can't find CUDA device %d.", gmoDeviceIndex);
            return false;
        }

        // Retrieve GMO struct from buffer, then validate it
        omni::sensors::GenericModelOutput* gmo = omni::sensors::getModelOutputPtrFromBuffer(gmoBufferPointer);
        if (gmo->numElements == 0)
        {
            CARB_LOG_WARN("IsaacTransformRTXSensorReturns: gmo->numElements is 0. Skipping execution.");
            return false;
        }
        if (gmo->modality != omni::sensors::Modality::LIDAR && gmo->modality != omni::sensors::Modality::RADAR)
        {
            CARB_LOG_WARN(
                "IsaacExtractRTXSensorPointCloud: gmoBufferPointer input is not from a Lidar or Radar prim. Buffer will not be parsed.");
            return false;
        }
        auto& state = db.perInstanceState<OgnIsaacExtractRTXSensorPointCloud>();

        // Reference to output transform matrix
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        getTransformFromSensorPose(gmo->frameEnd, matrixOutput);

        // If the source GMO buffer is on the host, we'll use the first device (0) for the scratch buffers
        int localGmoDeviceIndex = gmoDeviceIndex == -1 ? 0 : gmoDeviceIndex;
        // Set cudaMemcpyKinds based on whether the source GMO buffer is on the host or device
        cudaMemcpyKind cudaMemcpyKindInput = gmoDeviceIndex == -1 ? cudaMemcpyHostToDevice : cudaMemcpyDeviceToDevice;
        cudaMemcpyKind cudaMemcpyKindOutput = gmoDeviceIndex == -1 ? cudaMemcpyDeviceToHost : cudaMemcpyDeviceToDevice;

        isaacsim::core::includes::ScopedDevice scopedDev(localGmoDeviceIndex);

        state.m_pcBuffer.setDevice(localGmoDeviceIndex);
        state.m_scratchBuffer1.setDevice(localGmoDeviceIndex);
        state.m_scratchBuffer2.setDevice(localGmoDeviceIndex);
        state.m_scratchBuffer3.setDevice(localGmoDeviceIndex);
        state.m_scratchBuffer4.setDevice(localGmoDeviceIndex);

        state.hostPcBuffer.resize(gmo->numElements, make_float3(0.0f, 0.0f, 0.0f));
        state.m_pcBuffer.resize(gmo->numElements);
        state.m_scratchBuffer1.resize(gmo->numElements);
        state.m_scratchBuffer2.resize(gmo->numElements);
        state.m_scratchBuffer3.resize(gmo->numElements);
        state.m_scratchBuffer4.resize(gmo->numElements);

        db.outputs.azimuth().resize(gmo->numElements);
        db.outputs.elevation().resize(gmo->numElements);
        db.outputs.range().resize(gmo->numElements);

        if (gmo->elementsCoordsType == omni::sensors::CoordsType::SPHERICAL)
        {

            // TODO (adevalla): Assumes incoming GMO is on host, but that's not guaranteed
            // Copy x, y, z to scratch buffers (az/el/dist)
            state.m_scratchBuffer1.copyAsync(gmo->elements.x, gmo->numElements, cudaMemcpyKindInput);
            state.m_scratchBuffer2.copyAsync(gmo->elements.y, gmo->numElements, cudaMemcpyKindInput);
            state.m_scratchBuffer3.copyAsync(gmo->elements.z, gmo->numElements, cudaMemcpyKindInput);

            // Copy azimuth to host
            cudaMemcpyAsync(db.outputs.azimuth().data(), state.m_scratchBuffer1.data(),
                            gmo->numElements * sizeof(float), cudaMemcpyKindOutput);

            // Copy elevation to host
            cudaMemcpyAsync(db.outputs.elevation().data(), state.m_scratchBuffer2.data(),
                            gmo->numElements * sizeof(float), cudaMemcpyKindOutput);

            // Copy range to host
            cudaMemcpyAsync(db.outputs.range().data(), state.m_scratchBuffer3.data(), gmo->numElements * sizeof(float),
                            cudaMemcpyKindOutput);

            // Store sin(elevation) in pcBuffer.z, and cos(elevation) in scratchBuffer4
            elevation(state.m_scratchBuffer2.data(), state.m_pcBuffer.data(), state.m_scratchBuffer4.data(), 0.0f,
                      gmo->numElements, localGmoDeviceIndex);

            // Store sin(azimuth) in pcBuffer.x, and cos(azimuth) in pcBuffer.y
            azimuthDegToRad(
                state.m_scratchBuffer1.data(), state.m_pcBuffer.data(), 0.0f, gmo->numElements, localGmoDeviceIndex);

            // Store transformed Cartesian points in pcBuffer
            pointCloudWithTransform(state.m_pcBuffer.data(), state.m_scratchBuffer4.data(), state.m_scratchBuffer3.data(),
                                    make_float3(0.0f, 0.0f, 0.0f), nullptr, gmo->numElements, localGmoDeviceIndex);

            // Copy pcBuffer to host
            // TODO (adevalla): Keep buffer on device
            cudaMemcpyAsync(state.hostPcBuffer.data(), state.m_pcBuffer.data(), gmo->numElements * sizeof(float3),
                            cudaMemcpyKindOutput);
        }
        else
        {
            // TODO (adevalla): Assumes incoming GMO is on host, but that's not guaranteed
            for (size_t i = 0; i < gmo->numElements; i++)
            {
                // // skip invalid points
                // if ((gmo->elements.flags[i] & omni::sensors::ElementFlags::VALID) !=
                // omni::sensors::ElementFlags::VALID)
                // {
                //     continue;
                // }
                state.m_pcBuffer.data()[i] = make_float3(gmo->elements.x[i], gmo->elements.y[i], gmo->elements.z[i]);
            }

            cartesianToSpherical(state.m_pcBuffer.data(), state.m_scratchBuffer1.data(), state.m_scratchBuffer2.data(),
                                 state.m_scratchBuffer3.data(), gmo->numElements, localGmoDeviceIndex);
            cudaMemcpyAsync(db.outputs.azimuth().data(), state.m_scratchBuffer1.data(),
                            gmo->numElements * sizeof(float), cudaMemcpyDeviceToHost);
            cudaMemcpyAsync(db.outputs.elevation().data(), state.m_scratchBuffer2.data(),
                            gmo->numElements * sizeof(float), cudaMemcpyDeviceToHost);
            cudaMemcpyAsync(db.outputs.range().data(), state.m_scratchBuffer3.data(), gmo->numElements * sizeof(float),
                            cudaMemcpyDeviceToHost);
        }

        cudaDeviceSynchronize();

        // Set output metadata
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(state.hostPcBuffer.data());
        db.outputs.sensorOutputBuffer() = db.inputs.gmoBufferPointer();
        db.outputs.cudaDeviceIndex() = gmoDeviceIndex;
        db.outputs.bufferSize() = gmo->numElements * sizeof(float3);
        db.outputs.width() = gmo->numElements;
        db.outputs.height() = 1;

        // Return success and enable downstream execution
        db.outputs.exec() = kExecutionAttributeStateEnabled;
        return true;
    }
};

REGISTER_OGN_NODE()
} // rtx
} // sensors
} // isaacsim
