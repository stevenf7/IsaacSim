// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/utils/Buffer.h>
#include <omni/math/linalg/matrix.h>
#include <omni/sensors/GenericModelOutput.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>

// #include <tbb/atomic.h>
// #include <tbb/parallel_for.h>

#include <OgnIsaacComputeRTXLidarPointCloudDatabase.h>
#include <iostream>
#include <math.h>
#define __DEBUG_PRINT_ON 0

namespace omni
{
namespace isaac
{
namespace sensor
{

struct LidarPoint
{
    float x{ 0.0 }, y{ 0.0 }, z{ 0.0 }, azimuth{ 0.0 }, elevation{ 0.0 }, range{ 0.0 }, intensity{ 0.0 };
};
inline void convertReturnToPoint(const unsigned int idx,
                                 const omni::sensors::GenericModelOutput& gmo,
                                 const LidarProfile* profile,
                                 const uint32_t emitterId,
                                 const float accuracyErrorAzimuthDeg,
                                 const float accuracyErrorElevationDeg,
                                 LidarPoint& point)
{
    const float azimuthDeg = gmo.elements.x[idx] + accuracyErrorAzimuthDeg;
    const float elevationDeg{ gmo.elements.y[idx] + accuracyErrorElevationDeg };

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = gmo.elements.z[idx];

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    // Ray origin in meter
    float3 rayOrigin{ 0, 0, 0 };

    float distanceCorrectionM = 0.0f;
    float beamOriginMY = 0.0f;
    float beamOriginMZ = 0.0f;
    float beamOriginDistM = 0.0f;
    if (0 <= emitterId && emitterId < profile->emitterStateCount * profile->numberOfEmitters)
    {
        distanceCorrectionM = profile->emitterProfileSoA.distanceCorrectionM[emitterId];
        beamOriginMY = profile->emitterProfileSoA.horOffsetM[emitterId];
        beamOriginMZ = profile->emitterProfileSoA.vertOffsetM[emitterId];
        rayOrigin = { -sinAzimuth * beamOriginMY, cosAzimuth * beamOriginMY, beamOriginMZ };
        beamOriginDistM = beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ;
        beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;
    }

    const float distanceM = rawDistanceM + distanceCorrectionM;

    point.x = rayOrigin.x + rayDirectionX * distanceM;
    point.y = rayOrigin.y + rayDirectionY * distanceM;
    point.z = rayOrigin.z + rayDirectionZ * distanceM;

    // Add beam origin distance directly? -> see differences in resim
    point.range = rawDistanceM;
    point.intensity = gmo.elements.scalar[idx] * profile->intensityMapping.intensityScalePercent / 100.f;

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
        if (!helper.isValid(OutputType::POINTCLOUD, CoordsType::SPHERICAL, AuxType::LIDAR))
        {
            CARB_LOG_WARN(
                "Input to IsaacComputeRTXLidarPointCloud is not a valid LIDAR POINTCLOUD type. Buffer will not be parsed.");
            return true;
        }
        if (helper.m_gmo.numElements == 0)
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

        getTransformFromSensorPose(helper.m_gmo.frameEnd, matrixOutput);

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = helper.m_gmo.numElements;
        const float* distances = helper.m_gmo.elements.z;
        if (keepOnlyPositiveDistance)
        {
            outSize = 0;
            for (size_t i = 0; i < helper.m_gmo.numElements; ++i)
            {
                if (distances[i] > 0.f)
                {
                    ++outSize;
                }
            }
        }

        state.hostPcBuffer.resize(outSize, make_float3(0.0f, 0.0f, 0.0f));
        float3* dataPtr = state.hostPcBuffer.data();
        db.outputs.dataPtr() = reinterpret_cast<uint64_t>(dataPtr);
        db.outputs.bufferSize() = outSize * sizeof(pxr::GfVec3f);
        db.outputs.cudaDeviceIndex() = -1; // TODO
        db.outputs.width() = static_cast<uint32_t>(outSize);
        db.outputs.height() = 1;

#define _DEF_OUT_VAR(outName)                                                                                          \
    auto& db_outputs_##outName = db.outputs.outName();                                                                 \
    db_outputs_##outName.resize(outSize)
        _DEF_OUT_VAR(intensity);
        _DEF_OUT_VAR(range);
        _DEF_OUT_VAR(azimuth);
        _DEF_OUT_VAR(elevation);
#undef _DEF_OUT_VAR

        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();

        uint32_t atomicOutIdx = 0; // not atomic, but it will need to be if you parallelize this
        const omni::sensors::LidarAuxiliaryData* auxPoints =
            static_cast<const omni::sensors::LidarAuxiliaryData*>(helper.m_gmo.auxiliaryData);
        for (uint32_t pointIdx = 0; pointIdx < helper.m_gmo.numElements; pointIdx++)
        {

            // This is just for runtime efficiency
            if (!keepOnlyPositiveDistance || distances[pointIdx] > 0.f)
            {
                const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;
                LidarPoint p;
                convertReturnToPoint(pointIdx, helper.m_gmo, state.profile, auxPoints->emitterId[pointIdx],
                                     accuracyErrorAzimuthDeg, accuracyErrorElevationDeg, p);
                p.x += accuracyErrorPosition.x;
                p.y += accuracyErrorPosition.y;
                p.z += accuracyErrorPosition.z;
                dataPtr[outIdx].x = p.x;
                dataPtr[outIdx].y = p.y;
                dataPtr[outIdx].z = p.z;

#define _ASSIGN_OUT(outputName, index, comp, src) db_outputs_##outputName[index] comp = p.src

                _ASSIGN_OUT(intensity, outIdx, , intensity);
                _ASSIGN_OUT(range, outIdx, , range);
                _ASSIGN_OUT(azimuth, outIdx, , azimuth);
                _ASSIGN_OUT(elevation, outIdx, , elevation);

#undef _ASSIGN_OUT
            }
        }


        return true;
    }


private:
    isaac::utils::HostBufferBase<float3> hostPcBuffer;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
