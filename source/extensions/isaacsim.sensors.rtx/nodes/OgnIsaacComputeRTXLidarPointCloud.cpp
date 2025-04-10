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

#include "SensorNodeUtils.h"
#include "isaacsim/core/includes/UsdUtilities.h"

#include <isaacsim/core/includes/Buffer.h>
#include <omni/math/linalg/matrix.h>

#include <GenericModelOutput.h>

// #include <tbb/atomic.h>
// #include <tbb/parallel_for.h>

#include <OgnIsaacComputeRTXLidarPointCloudDatabase.h>
#include <iostream>
#include <math.h>
#define DEBUG_PRINT_ON 0

namespace isaacsim
{
namespace sensors
{
namespace rtx
{

struct LidarPoint
{
    float x{ 0.0 }, y{ 0.0 }, z{ 0.0 }, azimuth{ 0.0 }, elevation{ 0.0 }, range{ 0.0 }, intensity{ 0.0 };
};
inline void convertReturnToPoint(const unsigned int idx,
                                 const omni::sensors::GenericModelOutput& gmo,
                                 const float accuracyErrorAzimuthDeg,
                                 const float accuracyErrorElevationDeg,
                                 LidarPoint& point)
{
    const float azimuthDeg = gmo.elements.x[idx] + accuracyErrorAzimuthDeg;
    const float elevationDeg{ gmo.elements.y[idx] + accuracyErrorElevationDeg };

    const float azimuthRad{ deg2Rad(azimuthDeg) };
    const float elevationRad{ deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = gmo.elements.z[idx];

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    point.x = rayDirectionX * rawDistanceM;
    point.y = rayDirectionY * rawDistanceM;
    point.z = rayDirectionZ * rawDistanceM;

    // Add beam origin distance directly? -> see differences in resim
    point.range = rawDistanceM;
    point.intensity = gmo.elements.scalar[idx];

    point.azimuth = azimuthRad;
    point.elevation = elevationRad;
}

class OgnIsaacComputeRTXLidarPointCloud : public LidarConfigHelper
{
public:
    static bool compute(OgnIsaacComputeRTXLidarPointCloudDatabase& db)
    {
        CARB_PROFILE_ZONE(0, "Compute RTX Lidar PointCloud");
        // safe or passthrough values so we can return without worry anywhere in compute.
        db.outputs.exec() = db.inputs.exec();
        db.outputs.dataPtr() = 0;
        db.outputs.cudaDeviceIndex() = -1; // db.inputs.cudaDeviceIndex();
        db.outputs.bufferSize() = 0;
        db.outputs.width() = 0;
        db.outputs.height() = 1;
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.transform());
        matrixOutput.SetIdentity();

        db.outputs.intensity().resize(0);
        db.outputs.range().resize(0);
        db.outputs.azimuth().resize(0);
        db.outputs.elevation().resize(0);

        uint8_t* input = reinterpret_cast<uint8_t*>(db.inputs.dataPtr());
        if (!input)
        {
            return true;
        }
        auto& state = db.perInstanceState<OgnIsaacComputeRTXLidarPointCloud>();

        GenericModelOutputHelper helper(input);
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, Modality::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXLidarPointCloud is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.mGmo.numElements == 0)
        {
            return true;
        }

        // Update lidar configuration, if necessary
        state.updateLidarConfig(db.tokenToString(db.inputs.renderProductPath()));

        if (state.scanType == LidarScanType::kUnknown)
        {
            if (state.config == "")
            {
                CARB_LOG_WARN_ONCE("A Compute RTX Lidar PointCloud node can't get the lidar configuration file.");
            }
            else
            {
                CARB_LOG_WARN_ONCE(
                    "A Compute RTX Lidar PointCloud node tried to read a corrupt or missing profile named %s.",
                    state.config.c_str());
            }
        }

        getTransformFromSensorPose(helper.mGmo.frameEnd, matrixOutput);

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = helper.mGmo.numElements;
        const float* distances = helper.mGmo.elements.z;
        if (keepOnlyPositiveDistance)
        {
            outSize = 0;
            for (size_t i = 0; i < helper.mGmo.numElements; ++i)
            {
                if (distances[i] > 0.f)
                {
                    ++outSize;
                }
            }
        }

        state.m_hostPcBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
        float3* dataPtr = state.m_hostPcBuffer.data();
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(dataPtr);
        db.outputs.bufferSize() = outSize * sizeof(pxr::GfVec3f);
        db.outputs.cudaDeviceIndex() = -1; // TODO
        db.outputs.width() = static_cast<uint32_t>(outSize);
        db.outputs.height() = 1;

#define DEF_OUT_VAR(outName)                                                                                           \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(outSize)
        DEF_OUT_VAR(intensity);
        DEF_OUT_VAR(range);
        DEF_OUT_VAR(azimuth);
        DEF_OUT_VAR(elevation);
#undef DEF_OUT_VAR

        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();

        uint32_t atomicOutIdx = 0; // not atomic, but it will need to be if you parallelize this
        for (uint32_t pointIdx = 0; pointIdx < helper.mGmo.numElements; pointIdx++)
        {

            // Test for point validiy
            if ((helper.mGmo.elements.flags[pointIdx] & ElementFlags::VALID) != ElementFlags::VALID)
            {
                continue;
            }
            // This is just for runtime efficiency
            if (!keepOnlyPositiveDistance || distances[pointIdx] > 0.f)
            {
                const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;
                LidarPoint p;
                convertReturnToPoint(pointIdx, helper.mGmo, accuracyErrorAzimuthDeg, accuracyErrorElevationDeg, p);
                p.x += accuracyErrorPosition.x;
                p.y += accuracyErrorPosition.y;
                p.z += accuracyErrorPosition.z;
                dataPtr[outIdx].x = p.x;
                dataPtr[outIdx].y = p.y;
                dataPtr[outIdx].z = p.z;

#define ASSIGN_OUT(outputName, index, comp, src) db_outputs_##outputName[index] comp = p.src

                ASSIGN_OUT(intensity, outIdx, , intensity);
                ASSIGN_OUT(range, outIdx, , range);
                ASSIGN_OUT(azimuth, outIdx, , azimuth);
                ASSIGN_OUT(elevation, outIdx, , elevation);

#undef ASSIGN_OUT
            }
        }


        return true;
    }


private:
    isaacsim::core::includes::HostBufferBase<float3> m_hostPcBuffer;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
