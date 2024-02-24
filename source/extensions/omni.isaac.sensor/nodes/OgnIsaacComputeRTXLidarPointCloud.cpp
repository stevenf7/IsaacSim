// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/utils/Buffer.h>
#include <omni/math/linalg/matrix.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarPoint.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

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

inline void convertReturnToPoint(unsigned int idx,
                                 omni::sensors::lidar::LidarPoint& point,
                                 const LidarReturns& lidarReturns,
                                 const LidarBaseProfile* profile,
                                 const EmitterProfile* emitterProfile,
                                 float accuracyErrorAzimuthDeg,
                                 float accuracyErrorElevationDeg)
{
    // const float azimuthDeg = (rightHanded ? (360.f - lidarReturn.azimuthDeg) : lidarReturn.azimuthDeg);
    const float azimuthDeg = 360.f - lidarReturns.azimuths[idx] + accuracyErrorAzimuthDeg;
    const float elevationDeg{ lidarReturns.elevations[idx] + accuracyErrorElevationDeg };

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = lidarReturns.distances[idx];

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
    if (emitterProfile)
    {
        distanceCorrectionM = emitterProfile->distanceCorrectionM;
        beamOriginMY = emitterProfile->horOffsetM;
        beamOriginMZ = emitterProfile->vertOffsetM;
        rayOrigin = { -sinAzimuth * beamOriginMY, cosAzimuth * beamOriginMY, beamOriginMZ };
        beamOriginDistM = beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ;
        beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;
    }

    const float distanceM = rawDistanceM + distanceCorrectionM;

    point.x = rayOrigin.x + rayDirectionX * distanceM;
    point.y = rayOrigin.y + rayDirectionY * distanceM;
    point.z = rayOrigin.z + rayDirectionZ * distanceM;

    // Add beam origin distance directly? -> see differences in resim
    point.range = distanceM + beamOriginDistM;
    point.intensity = lidarReturns.intensities[idx];
    if (profile)
        point.intensity *= profile->intensityScalePercent / 100.f;


    point.azimuth = azimuthRad;
    point.elevation = elevationRad;

    // if (rightHanded)
    point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // fit azimuth into [-PI, PI] ala atan2
    if (point.azimuth > Deg2Rad(180.f))
        point.azimuth -= Deg2Rad(360.f);
}

class OgnIsaacComputeRTXLidarPointCloud
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

        // fill the structure of arrays
        LidarTicks lidarTicks;
        LidarReturns lidarReturns;
        LidarParameterType* parameter = saferFillStructsFromBuffer(input, lidarReturns, lidarTicks);
        if (!parameter)
            return true;
        const uint32_t numTicks = parameter->sync.numTicks;
        const uint32_t numChannels = parameter->async.numChannels;
        const uint32_t numEchos = parameter->async.numEchos;

        const size_t maxSize = numChannels * numEchos * numTicks;

        if (numTicks == 0 || numChannels * numEchos == 0)
        {
            return true;
        }

        std::string curConfig = "";
        pxr::UsdAttribute configAttr = omni::isaac::utils::getCameraAttributeFromRenderProduct(
            "sensorModelConfig", db.tokenToString(db.inputs.renderProductPath()));
        if (configAttr.IsValid())
        {
            omni::isaac::utils::safeGetAttribute(configAttr, curConfig);
        }
        updateLidarConfig(curConfig, state.config, state.scanType, state.rotaryProfile, state.solidStateProfile);

        if (state.scanType == LidarScanType::kUnknown)
        {
            if (curConfig == "")
            {
                CARB_LOG_WARN_ONCE("A Compute RTX Lidar PointCloud node can't get the lidar configuration file.");
            }
            else
            {
                CARB_LOG_WARN_ONCE(
                    "A Compute RTX Lidar PointCloud node tried to read a corrupt or missing profile named %s.",
                    curConfig.c_str());
            }
        }

        getTransformFromLidarAsyncParameter(parameter->async, matrixOutput);

        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();
        size_t outSize = maxSize;
        if (keepOnlyPositiveDistance)
        {
            outSize = 0;
            for (size_t i = 0; i < maxSize; ++i)
            {
                if (lidarReturns.distances[i] > 0.f)
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

        // const bool rightHanded = true; // TODO How should we decide this?
        // Solid state lidar only give out points for one tick at a time. see:
        //     drivesim code base LidarPCConverterHelper.h
        // NOTE: in Drivesim code, Solid State lidar does not use profile or emitterProfile ATM.
        const LidarBaseProfile* profile = state.scanType == LidarScanType::kRotary ?
                                              reinterpret_cast<const LidarBaseProfile*>(&state.rotaryProfile) :
                                              nullptr;
        // uint32_t numTicks = state.scanType == LidarScanType::kRotary ? numTicks : 1;
        uint32_t atomicOutIdx = 0;
        for (uint32_t tick = 0; tick < numTicks; tick++)
        {
            for (uint32_t channelId = 0; channelId < numChannels; ++channelId)
            {
                for (uint32_t echoId = 0; echoId < numEchos; ++echoId)
                {
                    const uint32_t pointIdx{ idxOfReturn(channelId, echoId, numEchos, numChannels, tick) };

                    // This is just for runtime efficiency
                    omni::sensors::lidar::LidarPoint p;
                    if (!keepOnlyPositiveDistance || lidarReturns.distances[pointIdx] > 0.f)
                    {
                        const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;
                        // NOTE: in drivesim, emitterProfile is not used for Solid State lidar.
                        const EmitterProfile* emitterProfile =
                            state.scanType == LidarScanType::kRotary ?
                                &state.rotaryProfile.emitterStates[lidarTicks.states[tick]]
                                     .emitterProfiles[lidarReturns.emitterIds[pointIdx]] :
                                nullptr;

                        convertReturnToPoint(pointIdx, p, lidarReturns, profile, emitterProfile,
                                             accuracyErrorAzimuthDeg, accuracyErrorElevationDeg);
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
            }
        }


        return true;
    }


private:
    isaac::utils::HostBufferBase<float3> hostPcBuffer;
    std::string config;
    LidarScanType scanType{ LidarScanType::kUnknown };
    LidarSolidStateProfile solidStateProfile;
    LidarRotaryProfile rotaryProfile;
};

REGISTER_OGN_NODE()
} // sensor
} // isaac
} // omni
