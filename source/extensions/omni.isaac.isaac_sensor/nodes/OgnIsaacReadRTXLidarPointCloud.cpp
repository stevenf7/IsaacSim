// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/InterfaceUtils.h>

#include <lidar/LidarParameterType.h>
#include <lidar/LidarReturnTypes.h>
#include <omni/drivesim/sensors/utils/HelperMath.h>
#include <omni/isaac/utils/BaseResetNode.h>
// #include <tbb/atomic.h>
// #include <tbb/parallel_for.h>

#include <OgnIsaacReadRTXLidarPointCloudDatabase.h>
#include <iostream>
#include <math.h>
namespace omni
{
namespace isaac
{
namespace core_nodes
{

static inline uint32_t idxOfReturn(const uint32_t beamId,
                                   const uint32_t echoId,
                                   const uint32_t numEchos,
                                   const uint32_t numBeams = 0,
                                   const uint32_t tick = 0)
{
    return beamId * numEchos + echoId + tick * numEchos * numBeams;
}

struct LidarPoint
{
    float x{ 0 }; /**< x in m (sensor coordinates) */
    float y{ 0 }; /**< y in m (sensor coordinates) */
    float z{ 0 }; /**< z in m (sensor coordinates) */
    float intensity{ 0 }; /**< intensity [0,1] */
    float range{ 0 }; /**< range in m */
    // horizontal angle
    float azimuth{ 0 }; /**< azimuth in rad [-pi,pi] */
    // vertical angle
    float elevation{ 0 }; /**< elevation in rad [-pi/2, pi/2] */
    float velocityMs[3]; /**< velocity at hit point in sensor coordinates [m/s] */
    uint32_t echoId{ 0 }; /**< echo id in ascending order */
    uint32_t emitterId{ 0 }; /**<  beam/laser detector id */
    uint32_t laserId{ 0 }; /**<  beam/laser detector id */
    uint32_t materialId{ 0 }; /**< hit point material id */
    uint32_t semanticId{ 0 }; /**< hit point semantic id */
    uint32_t tick{ 0 }; /**< tick of point */
    uint64_t objectId{ 0 }; /**< hit point object id */
    uint64_t timeStampNs{ 0 }; /**< absolute timeStamp in nano seconds */
    bool valid{ false }; /**< validity of the point */
};

/**
 * LidarPointCloud
 */
struct LidarPointCloud
{
    uint32_t numPoints{ 0 }; /**< number of points in the array */
    uint32_t accumulatedTicks{ 0 }; /**< accumulated ticks of the points */
    LidarPoint* points{ nullptr }; /**< points array */
    LidarTick* ticks{ nullptr }; /**< ticks array */
};

inline void setPointCommons(LidarPoint& point,
                            const LidarReturn& lidarReturn,
                            const LidarTick& lidarTick,
                            const uint32_t echoId)
{
    point.timeStampNs = lidarTick.timeStampNs + lidarReturn.deltaTimeNs;

    memcpy(point.velocityMs, lidarReturn.velocityMs, sizeof(float) * 3);
    point.echoId = echoId;
    point.emitterId = lidarReturn.emitterId;
    point.laserId = lidarReturn.beamId;
    point.materialId = lidarReturn.materialId;
    point.semanticId = lidarReturn.semanticId;
    point.objectId = lidarReturn.objectId;
}

inline void convertReturnToPoint(LidarPoint& point,
                                 const LidarTick& lidarTick,
                                 const LidarReturn& lidarReturn,
                                 //  const LidarRotaryProfile* profile,
                                 const uint32_t echoId,
                                 const bool rightHanded,
                                 const carb::Float3& posM,
                                 const carb::Float4& pose,
                                 const carb::Float3& accuracyErrorPosition,
                                 float accuracyErrorAzimuthDeg,
                                 float accuracyErrorElevationDeg)
{
    // const auto& emitterProfile = profile->emitterStates[lidarTick.state].emitterProfiles[lidarReturn.emitterId];
    // const uint32_t rangeId{ emitterProfile->rangeId };
    // const float rangeNearMinM{ profile->ranges[rangeId].min };
    // const float rangeFarMaxM{ profile->ranges[rangeId].max };

    const float beamOriginMX{ 0 };
    const float beamOriginMY{ 0 }; // emitterProfile.horOffsetM };
    const float beamOriginMZ{ 0 }; // emitterProfile.vertOffsetM };
    float beamOriginDistM{ beamOriginMX * beamOriginMX + beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ };
    beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;

    // NOTE: not sure non right handed is correct.
    const float azimuthDeg{ (rightHanded ? (360.f - lidarReturn.azimuthDeg) : lidarReturn.azimuthDeg) +
                            accuracyErrorAzimuthDeg };
    const float elevationDeg{ lidarReturn.elevationDeg + accuracyErrorElevationDeg };

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = lidarReturn.distance;

    // setPointCommons(point, lidarReturn, lidarTick, echoId);


    const float distanceM = rawDistanceM; //+ emitterProfile.distanceCorrectionM;

    // Ray origin in meter
    const float rayOriginMX{ cosAzimuth * beamOriginMX - sinAzimuth * beamOriginMY };
    const float rayOriginMY{ cosAzimuth * beamOriginMY + sinAzimuth * beamOriginMX };
    const float rayOriginMZ{ beamOriginMZ };

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    carb::Float3 p{ rayOriginMX + rayDirectionX * distanceM, rayOriginMY + rayDirectionY * distanceM,
                    rayOriginMZ + rayDirectionZ * distanceM };

    p = posM + rotatePointByQuat(p, pose);
    point.x = p.x + accuracyErrorPosition.x;
    point.y = p.y + accuracyErrorPosition.y;
    point.z = p.z + accuracyErrorPosition.z;

    // point.azimuth = distanceM > 0.f ? atan2f(point.y - rayOriginMY, point.x - rayOriginMX) : azimuthRad;
    // point.elevation = distanceM > 0.f ? acosf((point.z - rayOriginMZ) / distanceM) : elevationRad;

    // Add beam origin distance directly? -> see differences in resim
    // point.range = distanceM + beamOriginDistM;
    point.intensity = lidarReturn.intensity; //<float>(sensors::lidar::mapIntensity<uint16_t>(*profile,
    // lidarReturn.intensity)) / 100.f;

    // if (rightHanded)
    //    point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // fit azimuth into [-PI, PI] ala atan2
    // if (point.azimuth > Deg2Rad(180.f))
    //    point.azimuth -= Deg2Rad(360.f);
}


class OgnIsaacReadRTXLidarPointCloud : public BaseResetNode
{
public:
    static bool compute(OgnIsaacReadRTXLidarPointCloudDatabase& db)
    {

        CARB_PROFILE_ZONE(0, "Read RTX Lidar PointCloud");
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacReadRTXLidarPointCloud>();
        if (db.inputs.data.size() == 0)
        {
            return true;
        }
        const uint8_t* input = db.inputs.data().data();
        const LidarParameterType* parameter{ reinterpret_cast<const LidarParameterType*>(input) };

        if (parameter->async.numTicks == 0 || parameter->async.numChannels * parameter->async.numEchos == 0)
        {
            return true;
        }
        carb::Float3 posM{ parameter->async.posM[0], parameter->async.posM[1], parameter->async.posM[2] };
        carb::Float4 pose{ parameter->async.pose[0], parameter->async.pose[1], parameter->async.pose[2],
                           parameter->async.pose[3] };

        const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);

        // allocate mem for the output
        auto& db_outputs_pointCloudData = db.outputs.pointCloudData();
        auto& db_outputs_intensity = db.outputs.intensity();
        /*
        auto& db_outputs_range = db.outputs.range();
        auto& db_outputs_azimuth = db.outputs.azimuth();
        auto& db_outputs_elevation = db.outputs.elevation();
        auto& db_outputs_velocityMs = db.outputs.velocityMs();
        auto& db_outputs_echoId = db.outputs.echoId();
        auto& db_outputs_emitterId = db.outputs.emitterId();
        auto& db_outputs_laserId = db.outputs.laserId();
        auto& db_outputs_materialId = db.outputs.materialId();db.outputs.
        auto& db_outputs_semanticId = db.outputs.semanticId();
        auto& db_outputs_tick = db.outputs.tick();
        auto& db_outputs_objectId = db.outputs.objectId();
        auto& db_outputs_timeStampNs = db.outputs.timeStampNs();
        auto& db_outputs_valid = db.outputs.valid();
        */
        size_t maxSize = parameter->async.numChannels * parameter->async.numEchos * parameter->async.numTicks;
        db_outputs_pointCloudData.resize(maxSize);
        db_outputs_intensity.resize(maxSize);
        /*
        db_outputs_range.resize(maxSize);
        db_outputs_azimuth.resize(maxSize);
        db_outputs_elevation.resize(maxSize);
        db_outputs_velocityMs.resize(maxSize);
        db_outputs_echoId.resize(maxSize);
        db_outputs_emitterId.resize(maxSize);
        db_outputs_laserId.resize(maxSize);
        db_outputs_materialId.resize(maxSize);
        db_outputs_semanticId.resize(maxSize);
        db_outputs_tick.resize(maxSize);
        db_outputs_objectId.resize(maxSize);
        db_outputs_timeStampNs.resize(maxSize);
        db_outputs_valid.resize(maxSize);
        */

        size_t numPoints = 0;
        bool keepOnlyPositiveDistance = db.inputs.keepOnlyPositiveDistance();

        carb::Float3 accuracyErrorPosition{ db.inputs.accuracyErrorPosition()[0], db.inputs.accuracyErrorPosition()[1],
                                            db.inputs.accuracyErrorPosition()[2] };
        float accuracyErrorAzimuthDeg = db.inputs.accuracyErrorAzimuthDeg();
        float accuracyErrorElevationDeg = db.inputs.accuracyErrorElevationDeg();
        // tbb::atomic<uint32_t> atomicOutIdx = 0;
        uint32_t atomicOutIdx = 0;
        // tbb::parallel_for(tbb::blocked_range<uint32_t>(0, parameter->async.numTicks),
        // [&](tbb::blocked_range<uint32_t> r) { for (uint32_t tick = r.begin(); tick < r.end(); tick++)
        for (uint32_t tick = 0; tick < parameter->async.numTicks; tick++)
        {
            const LidarTick& lidarTick = lidarTicks[tick];
            for (uint32_t channelId = 0; channelId < parameter->async.numChannels; ++channelId)
            {
                for (uint32_t echoId = 0; echoId < parameter->async.numEchos; ++echoId)
                {
                    const uint32_t pointIdx{ idxOfReturn(
                        channelId, echoId, parameter->async.numEchos, parameter->async.numChannels, tick) };
                    const LidarReturn& lidarReturn = lidarReturns[pointIdx];
                    // This is just for runtime efficiency
                    LidarPoint p;
                    if (!keepOnlyPositiveDistance || lidarReturn.distance > 0.f)
                    {
                        const uint32_t outIdx = keepOnlyPositiveDistance ? atomicOutIdx++ : pointIdx;
                        // p.tick = tick;// + hpc.accumulatedTicks;
                        p.valid = lidarReturn.intensity > 0.f || lidarReturn.azimuthDeg > 0.f ||
                                  lidarReturn.elevationDeg > 0.f || lidarReturn.deltaTimeNs > 0 ||
                                  lidarReturn.emitterId > 0 || lidarReturn.beamId > 0;
                        convertReturnToPoint( // TODO: Get the horizontal and vertical offset of the emitter
                                              // "horOffsetM" "vertOffsetM"
                            p, lidarTick, lidarReturn, echoId, true, posM, pose, accuracyErrorPosition,
                            accuracyErrorAzimuthDeg, accuracyErrorElevationDeg);
                        db_outputs_pointCloudData[outIdx][0] = p.x;
                        db_outputs_pointCloudData[outIdx][1] = p.y;
                        db_outputs_pointCloudData[outIdx][2] = p.z;
                        db_outputs_intensity[outIdx] = p.intensity;
                        /*
                        db_outputs_range[outIdx] = p.range;
                        db_outputs_azimuth[outIdx] = p.azimuth;
                        db_outputs_elevation[outIdx] = p.elevation;
                        db_outputs_velocityMs[outIdx][0] = p.velocityMs[0];
                        db_outputs_velocityMs[outIdx][1] = p.velocityMs[1];
                        db_outputs_velocityMs[outIdx][2] = p.velocityMs[2];
                        db_outputs_echoId[outIdx] = p.echoId;
                        db_outputs_emitterId[outIdx] = p.emitterId;
                        db_outputs_laserId[outIdx] = p.laserId;
                        db_outputs_materialId[outIdx] = p.materialId;
                        db_outputs_semanticId[outIdx] = p.semanticId;
                        db_outputs_tick[outIdx] = p.tick;
                        db_outputs_objectId[outIdx] = p.objectId;
                        db_outputs_timeStampNs[outIdx] = p.timeStampNs;
                        db_outputs_valid[outIdx] = p.valid;
                        */
                    }
                }
            }
        } // });
        if (keepOnlyPositiveDistance)
        {
            db_outputs_pointCloudData.resize(atomicOutIdx);
            db_outputs_intensity.resize(atomicOutIdx);
            /*
            db_outputs_range.resize(atomicOutIdx);
            db_outputs_azimuth.resize(atomicOutIdx);
            db_outputs_elevation.resize(atomicOutIdx);
            db_outputs_velocityMs.resize(atomicOutIdx);
            db_outputs_echoId.resize(atomicOutIdx);
            db_outputs_emitterId.resize(atomicOutIdx);
            db_outputs_laserId.resize(atomicOutIdx);
            db_outputs_materialId.resize(atomicOutIdx);
            db_outputs_semanticId.resize(atomicOutIdx);
            db_outputs_tick.resize(atomicOutIdx);
            db_outputs_objectId.resize(atomicOutIdx);
            db_outputs_timeStampNs.resize(atomicOutIdx);
            db_outputs_valid.resize(atomicOutIdx);
            */
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;

        return true;
    }

    virtual void reset()
    {
    }
};

REGISTER_OGN_NODE()
} // core_nodes
} // isaac
} // omni
