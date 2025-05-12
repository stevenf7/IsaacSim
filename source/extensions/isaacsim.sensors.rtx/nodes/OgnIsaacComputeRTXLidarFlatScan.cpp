// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.
#include <pch/UsdPCH.h>
// clang-format on

#include "GenericModelOutput.h"
#include "OgnIsaacComputeRTXLidarFlatScanDatabase.h"
#include "SensorNodeUtils.h"
#include "isaacsim/core/includes/Buffer.h"
#include "isaacsim/core/includes/ScopedCudaDevice.h"
#include "isaacsim/core/includes/UsdUtilities.h"

#include <math.h>

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

class OgnIsaacComputeRTXLidarFlatScan : public LidarConfigHelper
{
private:
    bool warnDeprecated = false;

public:
    static bool compute(OgnIsaacComputeRTXLidarFlatScanDatabase& db)
    {
        // Disable downstream execution by default
        db.outputs.exec() = kExecutionAttributeStateDisabled;

        uint8_t* dataPtr = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        // no reason to update the scan buffer if there is no dataHost
        if (!dataPtr)
        {
            CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: dataPtr input is empty.");
            return false;
        }
        // This is a GPU buffer generating node.  If the input cudaHandle is -1 (CPU), then just use the host device.
        int cudaDeviceIndex = db.inputs.cudaDeviceIndex();
        cudaDeviceProp cudaDeviceProperties;
        if (cudaDeviceIndex != -1 &&
            cudaGetDeviceProperties(&cudaDeviceProperties, cudaDeviceIndex) != cudaError::cudaSuccess)
        {
            CARB_LOG_ERROR("IsaacComputeRTXLidarFlatScan can't find CUDA device %d.", cudaDeviceIndex);
            return false;
        }

        // Retrieve GMO struct from buffer, then validate it
        omni::sensors::GenericModelOutput* gmo = omni::sensors::getModelOutputPtrFromBuffer(dataPtr);
        if (gmo->numElements == 0)
        {
            CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: gmo->numElements is 0. Skipping execution.");
            return false;
        }

        // Verify that we have a supported modality
        if (gmo->modality != omni::sensors::Modality::LIDAR)
        {
            CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: Unsupported sensor modality: %d. Only LIDAR is supported.",
                          static_cast<int>(gmo->modality));
            return false;
        }

        // Retrieve lidar prim from render product path, then validate its attributes
        const std::string renderProductPath = std::string(db.tokenToString(db.inputs.renderProductPath()));
        if (renderProductPath.length() == 0)
        {
            CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: renderProductPath input is empty. Skipping execution.");
            return false;
        }
        float rotationRate, horizontalFov, horizontalResolution, azimuthRangeStart, azimuthRangeEnd, nearRangeM,
            farRangeM;
        pxr::UsdPrim lidarPrim = isaacsim::core::includes::getCameraPrimFromRenderProduct(renderProductPath);
        if (lidarPrim.IsA<pxr::UsdGeomCamera>())
        {
            auto& state = db.perInstanceState<OgnIsaacComputeRTXLidarFlatScan>();
            CARB_LOG_WARN_ONCE(
                "RTX sensors as camera prims are deprecated as of Isaac Sim 5.0, and support will be removed in a future release. Please use an OmniLidar prim with the new OmniSensorGenericLidarCoreAPI schema.");
            bool updatedConfig = state.updateLidarConfig(renderProductPath.c_str());
            if (state.scanType == LidarScanType::kUnknown)
            {
                if (updatedConfig)
                {
                    CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: Lidar prim is not a valid Lidar. Skipping execution.");
                }
                return false;
            }
            if (!state.is2D)
            {
                if (updatedConfig)
                {
                    CARB_LOG_WARN("IsaacComputeRTXLidarFlatScan: Lidar prim is not a 2D Lidar. Skipping execution.");
                }
                return false;
            }
            if (state.scanType == LidarScanType::kSolidState)
            {
                azimuthRangeStart = state.azimuthStartDeg;
                azimuthRangeEnd = state.azimuthEndDeg;
                horizontalFov = azimuthRangeStart - azimuthRangeEnd;
                horizontalResolution = horizontalFov / static_cast<float>(state.numberOfEmitters);
            }
            else
            {
                horizontalResolution = 360.0f * state.scanRateBaseHz / state.reportRateBaseHz;
                azimuthRangeStart = -180.0f;
                azimuthRangeEnd = 180.0f - horizontalResolution;
                horizontalFov = 360.0f;
            }
            nearRangeM = state.nearRangeM;
            farRangeM = state.farRangeM;
            rotationRate = static_cast<float>(state.scanRateBaseHz);
        }
        else
        {
            pxr::TfToken elementsCoordsType;
            if (lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:elementsCoordsType")).Get(&elementsCoordsType) &&
                elementsCoordsType != pxr::TfToken("SPHERICAL"))
            {
                CARB_LOG_WARN(
                    "IsaacComputeRTXLidarFlatScan: Lidar prim elementsCoordsType is not set to SPHERICAL. Skipping execution.");
                return false;
            }
            pxr::VtFloatArray elevationDeg;
            if (lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:emitterState:s001:elevationDeg")).Get(&elevationDeg))
            {
                const float epsilon = 1e-3f; // Tolerance of 0.001 degrees
                for (const float elev : elevationDeg)
                {
                    if (::fabs(elev) > epsilon)
                    {
                        CARB_LOG_WARN(
                            "IsaacComputeRTXLidarFlatScan: Lidar prim elevationDeg contains nonzero value %f, indicating a 3D lidar. Skipping execution.",
                            elev);
                        return false;
                    }
                }
            }
            // Populate any prim-specific outputs
            uint32_t rotationRateAsInt;
            lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:scanRateBaseHz")).Get(&rotationRateAsInt);
            rotationRate = static_cast<float>(rotationRateAsInt);
            lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:nearRangeM")).Get(&nearRangeM);
            lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:farRangeM")).Get(&farRangeM);

            pxr::TfToken outputType;
            lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:scanType")).Get(&outputType);
            if (outputType == pxr::TfToken("SOLID_STATE"))
            {
                pxr::VtFloatArray azimuthDeg;
                lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:emitterState:s001:azimuthDeg")).Get(&azimuthDeg);

                azimuthRangeStart = *std::min_element(azimuthDeg.begin(), azimuthDeg.end());
                azimuthRangeEnd = *std::max_element(azimuthDeg.begin(), azimuthDeg.end());
                horizontalFov = azimuthRangeEnd - azimuthRangeStart;
                horizontalResolution = horizontalFov / static_cast<float>(azimuthDeg.size());
            }
            else
            {
                // Set useful state variables
                uint32_t reportRateBaseHzAsInt;
                lidarPrim.GetAttribute(pxr::TfToken("omni:sensor:Core:reportRateBaseHz")).Get(&reportRateBaseHzAsInt);
                float reportRateBaseHz = static_cast<float>(reportRateBaseHzAsInt);
                horizontalResolution = 360.0f * rotationRate / reportRateBaseHz;

                azimuthRangeStart = -180.0f;
                azimuthRangeEnd = 180.0f - horizontalResolution;
                horizontalFov = 360.0;
            }
        }

        db.outputs.horizontalFov() = horizontalFov;
        db.outputs.horizontalResolution() = horizontalResolution;
        db.outputs.azimuthRange() = { azimuthRangeStart, azimuthRangeEnd };
        db.outputs.rotationRate() = rotationRate;
        db.outputs.depthRange() = { nearRangeM, farRangeM };
        db.outputs.numRows() = 1;
        db.outputs.numCols() = gmo->numElements;

        // Populate output buffers
        db.outputs.linearDepthData().resize(gmo->numElements);
        db.outputs.intensitiesData().resize(gmo->numElements);
        if (cudaDeviceIndex == -1)
        {
            // Create a map of azimuth to depth and intensity, to automatically sort by azimuth
            std::map<float, std::pair<float, uint8_t>> azimuthToDepthAndIntensity;
            for (size_t i = 0; i < gmo->numElements; i++)
            {
                // Skip invalid returns
                if ((gmo->elements.flags[i] & omni::sensors::ElementFlags::VALID) != omni::sensors::ElementFlags::VALID)
                {
                    continue;
                }
                azimuthToDepthAndIntensity[gmo->elements.x[i]] = {
                    gmo->elements.z[i], static_cast<uint8_t>(gmo->elements.scalar[i] * 255.0f)
                };
            }
            // Copy sorted values into output buffers
            db.outputs.linearDepthData().resize(azimuthToDepthAndIntensity.size());
            db.outputs.intensitiesData().resize(azimuthToDepthAndIntensity.size());
            db.outputs.numCols() = static_cast<int>(azimuthToDepthAndIntensity.size());
            size_t index = 0;
            for (const auto& [azimuth, depthAndIntensity] : azimuthToDepthAndIntensity)
            {
                db.outputs.linearDepthData()[index] = depthAndIntensity.first;
                db.outputs.intensitiesData()[index] = depthAndIntensity.second;
                index++;
            }
        }
        else
        {
            isaacsim::core::includes::ScopedDevice scopedDev(cudaDeviceIndex);

            cudaMemcpyAsync(db.outputs.linearDepthData().data(), gmo->elements.z, gmo->numElements * sizeof(float),
                            cudaMemcpyDeviceToHost, 0);
            cudaMemcpyAsync(db.outputs.intensitiesData().data(), gmo->elements.scalar, gmo->numElements * sizeof(float),
                            cudaMemcpyDeviceToHost, 0);

            cudaDeviceSynchronize();
        }

        // Return success and enable downstream execution
        db.outputs.exec() = kExecutionAttributeStateEnabled;
        return true;
    }
};

REGISTER_OGN_NODE()
} // rtx
} // sensors
} // isaacsim
