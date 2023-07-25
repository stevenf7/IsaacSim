// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <internal/omni/sensors/lidar/LidarIntensityMapping.h>
#include <omni/sensors/cuda/CudaHelperMath.h>
#include <omni/sensors/lidar/ILidarPCConverter.h>
#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarPoint.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <omni/sensors/lidar/LidarReturn.h>

#include <cstdint>
#include <float.h>

namespace omni
{
namespace sensors
{
namespace nv
{
namespace lidar
{

//-----------------------------------------------------------------------------
inline bool isScanComplete(omni::sensors::lidar::LidarPCConverterContext* hContext,
                           const uint64_t scanEndTimeNs,
                           const uint64_t epsilonNs)
{
    return hContext->lastPointTimeNs >= (scanEndTimeNs - epsilonNs);
}

//-----------------------------------------------------------------------------
// For packet conversion
inline bool isScanComplete(const omni::sensors::lidar::LidarPointCloud& hpc,
                           const uint64_t testTimeNs,
                           const uint64_t scanEndTimeNs,
                           const uint64_t epsilonNs,
                           const uint32_t maxTicks)
{

    return hpc.accumulatedTicks == maxTicks || testTimeNs >= (scanEndTimeNs - epsilonNs);
}

inline void resetPC(omni::sensors::lidar::LidarPointCloud& hpc,
                    omni::sensors::lidar::LidarPoint* dPoints,
                    const uint32_t maxPoints,
                    void* cudaStream)
{
    if (hpc.points)
        memset(hpc.points, 0, maxPoints * sizeof(omni::sensors::lidar::LidarPoint));
    if (hpc.tickAzimuths)
    {
        memset(hpc.tickAzimuths, 0, hpc.accumulatedTicks * sizeof(float));
        memset(hpc.tickStates, 0, hpc.accumulatedTicks * sizeof(uint32_t));
        memset(hpc.tickTimestamps, 0, hpc.accumulatedTicks * sizeof(uint64_t));
    }
    hpc.accumulatedTicks = 0;
    hpc.numPoints = 0;
    if (dPoints)
    {
        cudaStream_t stream = reinterpret_cast<cudaStream_t>(cudaStream);
        CUDA_CALL(cudaMemsetAsync(dPoints, 0, maxPoints * sizeof(omni::sensors::lidar::LidarPoint), stream));
    }
}

NV_HOSTDEVICE inline void transformPoint(omni::sensors::lidar::LidarPoint& point,
                                         const omni::sensors::lidar::LidarPCConverterContext* context,
                                         const float3& rayOrigin)
{
    float3 newPos =
        make_float3(context->position[0], context->position[1], context->position[2]) +
        ConjugateVByQ({ point.x, point.y, point.z }, make_float4(context->orientation[0], context->orientation[1],
                                                                 context->orientation[2], context->orientation[3]));
    point.x = newPos.x;
    point.y = newPos.y;
    point.z = newPos.z;

    // only adjust other parameter if it was a meaningful point
    if (point.range > 0)
    {
        point.azimuth = atan2f(point.y - rayOrigin.y, point.x - rayOrigin.x);
        point.elevation = asinf((point.z - rayOrigin.z) / point.range);
    }
}

NV_HOSTDEVICE inline void setPointCommons(omni::sensors::lidar::LidarPoint& point,
                                          const LidarReturns& lidarReturns,
                                          const uint32_t returnIdx,
                                          const LidarTicks& lidarTicks,
                                          const uint32_t tickIdx,
                                          const uint32_t echoId,
                                          const LidarBaseProfile& profile,
                                          const omni::sensors::lidar::LidarPCConverterContext* context,
                                          const EmitterProfile& emitterProfile,
                                          const float inAzimuthDeg,
                                          const float elevationDeg,
                                          const bool rightHanded)
{
    const float azimuthDeg{ rightHanded ? (360.f - inAzimuthDeg) : inAzimuthDeg };
    point.timeStampNs = lidarTicks.timestamps[tickIdx] + lidarReturns.deltaTimes[returnIdx];

    memcpy(point.velocityMs, &lidarReturns.velocities[returnIdx * 3], sizeof(float) * 3);
    memcpy(point.hitPointNormal, &lidarReturns.hitPointNormals[returnIdx * 3], sizeof(float) * 3);
    point.echoId = echoId;
    point.emitterId = lidarReturns.emitterIds[returnIdx];
    point.laserId = lidarReturns.beamIds[returnIdx];
    point.materialId = lidarReturns.materialIds[returnIdx];
    point.objectId = lidarReturns.objectIds[returnIdx];

    const float beamOriginMX{ 0.f };
    const float beamOriginMY{ emitterProfile.horOffsetM };
    const float beamOriginMZ{ emitterProfile.vertOffsetM };
    float beamOriginDistM{ beamOriginMX * beamOriginMX + beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ };
    beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float distanceM = lidarReturns.distances[returnIdx] + emitterProfile.distanceCorrectionM;
    // Ray origin in meter
    const float3 rayOrigin{ cosAzimuth * beamOriginMX - sinAzimuth * beamOriginMY,
                            cosAzimuth * beamOriginMY + sinAzimuth * beamOriginMX, beamOriginMZ };

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    point.x = rayOrigin.x + rayDirectionX * distanceM;
    point.y = rayOrigin.y + rayDirectionY * distanceM;
    point.z = rayOrigin.z + rayDirectionZ * distanceM;

    point.intensity = static_cast<float>(omni::sensors::lidar::mapIntensity<uint16_t>(
                          profile, lidarReturns.intensities[returnIdx], true)) /
                      100.f;


    // Add beam origin distance directly? -> see differences in resim
    point.range = distanceM + beamOriginDistM;
    point.azimuth = azimuthRad;
    point.elevation = elevationRad;
    transformPoint(point, context, rayOrigin);

    if (rightHanded)
        point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // fit azimuth into [-PI, PI] ala atan2
    if (point.azimuth > Deg2Rad(180.f))
        point.azimuth -= Deg2Rad(360.f);
}

NV_HOSTDEVICE inline void convertReturnToPoint(omni::sensors::lidar::LidarPoint& point,
                                               const LidarTicks& lidarTicks,
                                               const uint32_t tickIdx,
                                               const LidarReturns& lidarReturns,
                                               const uint32_t returnIdx,
                                               const LidarRotaryProfile* profile,
                                               const omni::sensors::lidar::LidarPCConverterContext* context,
                                               const uint32_t echoId,
                                               const bool rightHanded)
{

    const auto& emitterProfile =
        profile->emitterStates[lidarTicks.states[tickIdx]].emitterProfiles[lidarReturns.emitterIds[returnIdx]];
    // const float azimuthDeg = (rightHanded ? (360.f - lidarReturn.azimuthDeg) : lidarReturn.azimuthDeg);
    // Use emitter profile angles + tickazimuth (=packet azimuth) as rotary does not communicate the angles
    const float azimuthDeg{ lidarTicks.azimuths[tickIdx] + emitterProfile.azimuthDeg };
    setPointCommons(point, lidarReturns, returnIdx, lidarTicks, tickIdx, echoId, *profile, context, emitterProfile,
                    azimuthDeg, emitterProfile.elevationDeg, rightHanded);
}

NV_HOSTDEVICE inline bool pointValid(const LidarReturns& lidarReturns, const uint32_t idx)
{
    return lidarReturns.intensities[idx] > 0.f || lidarReturns.azimuths[idx] > 0.f ||
           lidarReturns.elevations[idx] > 0.f || lidarReturns.deltaTimes[idx] > 0 || lidarReturns.emitterIds[idx] > 0 ||
           lidarReturns.beamIds[idx] > 0;
}

NV_HOSTDEVICE inline void convertReturnToPoint(omni::sensors::lidar::LidarPoint& point,
                                               const LidarTicks& lidarTicks,
                                               const uint32_t tickIdx,
                                               const LidarReturns& lidarReturns,
                                               const uint32_t returnIdx,
                                               const LidarBaseProfile* profile,
                                               const EmitterProfile* sostEmitters,
                                               const omni::sensors::lidar::LidarPCConverterContext* context,
                                               const uint32_t echoId,
                                               const bool rightHanded)
{
    const EmitterProfile& emitterProfile =
        sostEmitters[lidarTicks.states[tickIdx] * profile->numberOfEmitters + lidarReturns.emitterIds[returnIdx]];
    // TODO: maybe add option to use firing pattern angles
    setPointCommons(point, lidarReturns, returnIdx, lidarTicks, tickIdx, echoId, *profile, context, emitterProfile,
                    lidarReturns.azimuths[returnIdx], lidarReturns.elevations[returnIdx], rightHanded);
}

} // namespace lidar
} // namespace nv
} // namespace sensors
} // namespace omni
