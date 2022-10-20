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
#include <omni/math/linalg/matrix.h>
#include <omni/math/linalg/quat.h>
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
                                 const carb::Float3& accuracyErrorPosition,
                                 float accuracyErrorAzimuthDeg,
                                 float accuracyErrorElevationDeg)
{
    // const auto& emitterProfile = profile->emitterStates[lidarTick.state].emitterProfiles[lidarReturn.emitterId];
    // const uint32_t rangeId{ emitterProfile->rangeId };
    // const float rangeNearMinM{ profile->ranges[rangeId].min };
    // const float rangeFarMaxM{ profile->ranges[rangeId].max };

    // const float beamOriginMX{ 0.0f };
    // const float beamOriginMY{ 0.0f }; // + emitterProfile.horOffsetM };
    // const float beamOriginMZ{ 0.0f }; // + emitterProfile.vertOffsetM };
    // float beamOriginDistM{ beamOriginMX * beamOriginMX + beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ };
    // beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;

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

    setPointCommons(point, lidarReturn, lidarTick, echoId);


    const float distanceM = rawDistanceM; //+ emitterProfile.distanceCorrectionM;

    // Ray origin in meter
    // const float rayOriginMX{cosAzimuth * beamOriginMX - sinAzimuth * beamOriginMY };
    // const float rayOriginMY{cosAzimuth * beamOriginMY + sinAzimuth * beamOriginMX };
    // const float rayOriginMZ{beamOriginMZ };

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    carb::Float3 p{ /*rayOriginMX4 + */ rayDirectionX * distanceM, /*rayOriginMY +*/ rayDirectionY * distanceM,
                    /*rayOriginMZ + */ rayDirectionZ * distanceM };


    // p = posM + rotatePointByQuat(p, pose);
    point.x = accuracyErrorPosition.x + p.x;
    point.y = accuracyErrorPosition.y + p.y;
    point.z = accuracyErrorPosition.z + p.z;

    point.azimuth = distanceM > 0.f ? atan2f(point.y /*- rayOriginMY*/, point.x /*- rayOriginMX*/) : azimuthRad;
    point.elevation = distanceM > 0.f ? acosf((point.z /*- rayOriginMZ*/) / distanceM) : elevationRad;

    // Add beam origin distance directly? -> see differences in resim
    point.range = distanceM; // + beamOriginDistM;
    point.intensity = lidarReturn.intensity; //<float>(sensors::lidar::mapIntensity<uint16_t>(*profile,
    // lidarReturn.intensity)) / 100.f;

    if (rightHanded)
        point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // fit azimuth into [-PI, PI] ala atan2
    if (point.azimuth > Deg2Rad(180.f))
        point.azimuth -= Deg2Rad(360.f);
}


class OgnIsaacReadRTXLidarPointCloud : public BaseResetNode
{
    inline static bool needOutput(const NodeObj& nodeObj, NameToken attrName)
    {
        const AttributeObj attr = nodeObj.iNode->getAttributeByToken(nodeObj, attrName);
        return attr.iAttribute->getDownstreamConnectionCount(attr);
    }

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
        // async.pose is [X, Y, Z, W].
        // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
        omni::math::linalg::vec3d posM{ parameter->async.posM[0], parameter->async.posM[1], parameter->async.posM[2] };
        omni::math::linalg::quatd pose{ parameter->async.pose[3], parameter->async.pose[0], parameter->async.pose[1],
                                        parameter->async.pose[2] };
        auto& matrixOutput = *reinterpret_cast<omni::math::linalg::matrix4d*>(&db.outputs.toWorldMatrix());
        matrixOutput.SetIdentity();
        matrixOutput.SetRotateOnly(pose);
        matrixOutput.SetTranslateOnly(posM);

        const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);

        auto& nodeObj = db.abi_node();
        size_t maxSize = parameter->async.numChannels * parameter->async.numEchos * parameter->async.numTicks;

        bool outputNeeded = false;

#define _DEFINE_OUTPUT_VARS(outputName)                                                                                \
    auto& db_outputs_##outputName = db.outputs.outputName();                                                           \
    bool needed_##outputName = needOutput(nodeObj, outputs::outputName.m_token);                                       \
    outputNeeded |= needed_##outputName

        _DEFINE_OUTPUT_VARS(pointCloudData);
        _DEFINE_OUTPUT_VARS(intensity);
        _DEFINE_OUTPUT_VARS(range);
        _DEFINE_OUTPUT_VARS(azimuth);
        _DEFINE_OUTPUT_VARS(elevation);
        _DEFINE_OUTPUT_VARS(velocityMs);
        _DEFINE_OUTPUT_VARS(echoId);
        _DEFINE_OUTPUT_VARS(emitterId);
        _DEFINE_OUTPUT_VARS(laserId);
        _DEFINE_OUTPUT_VARS(materialId);
        _DEFINE_OUTPUT_VARS(semanticId);
        _DEFINE_OUTPUT_VARS(tick);
        _DEFINE_OUTPUT_VARS(objectId);
        _DEFINE_OUTPUT_VARS(timeStampNs);
        _DEFINE_OUTPUT_VARS(valid);
#undef _DEFINE_OUTPUT_VARS

        if (!outputNeeded)
        {
            db.outputs.execOut() = kExecutionAttributeStateEnabled;
            return true;
        }
        // allocate mem for the output#define
#define _RESIZE_IF_NEEDED(outputName, size)                                                                            \
    if (needed_##outputName)                                                                                           \
    db_outputs_##outputName.resize(size)

        _RESIZE_IF_NEEDED(pointCloudData, maxSize);
        _RESIZE_IF_NEEDED(intensity, maxSize);
        _RESIZE_IF_NEEDED(range, maxSize);
        _RESIZE_IF_NEEDED(azimuth, maxSize);
        _RESIZE_IF_NEEDED(elevation, maxSize);
        _RESIZE_IF_NEEDED(velocityMs, maxSize);
        _RESIZE_IF_NEEDED(echoId, maxSize);
        _RESIZE_IF_NEEDED(emitterId, maxSize);
        _RESIZE_IF_NEEDED(laserId, maxSize);
        _RESIZE_IF_NEEDED(materialId, maxSize);
        _RESIZE_IF_NEEDED(semanticId, maxSize);
        _RESIZE_IF_NEEDED(tick, maxSize);
        _RESIZE_IF_NEEDED(objectId, maxSize);
        _RESIZE_IF_NEEDED(timeStampNs, maxSize);
        _RESIZE_IF_NEEDED(valid, maxSize);

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
                        p.tick = tick; // + hpc.accumulatedTicks;
                        p.valid = lidarReturn.intensity > 0.f || lidarReturn.azimuthDeg > 0.f ||
                                  lidarReturn.elevationDeg > 0.f || lidarReturn.deltaTimeNs > 0 ||
                                  lidarReturn.emitterId > 0 || lidarReturn.beamId > 0;
                        convertReturnToPoint( // TODO: Get the horizontal and vertical offset of the emitter
                                              // "horOffsetM" "vertOffsetM"
                            p, lidarTick, lidarReturn, echoId, true, accuracyErrorPosition, accuracyErrorAzimuthDeg,
                            accuracyErrorElevationDeg);

#define _ASSIGN_IF_NEEDED(outputName, index, comp, src)                                                                \
    if (needed_##outputName)                                                                                           \
    db_outputs_##outputName[index] comp = p.src

                        _ASSIGN_IF_NEEDED(pointCloudData, outIdx, [0], x);
                        _ASSIGN_IF_NEEDED(pointCloudData, outIdx, [1], y);
                        _ASSIGN_IF_NEEDED(pointCloudData, outIdx, [2], z);
                        _ASSIGN_IF_NEEDED(intensity, outIdx, , intensity);
                        _ASSIGN_IF_NEEDED(range, outIdx, , range);
                        _ASSIGN_IF_NEEDED(azimuth, outIdx, , azimuth);
                        _ASSIGN_IF_NEEDED(elevation, outIdx, , elevation);
                        _ASSIGN_IF_NEEDED(velocityMs, outIdx, [0], velocityMs[0]);
                        _ASSIGN_IF_NEEDED(velocityMs, outIdx, [1], velocityMs[1]);
                        _ASSIGN_IF_NEEDED(velocityMs, outIdx, [2], velocityMs[2]);
                        _ASSIGN_IF_NEEDED(echoId, outIdx, , echoId);
                        _ASSIGN_IF_NEEDED(emitterId, outIdx, , emitterId);
                        _ASSIGN_IF_NEEDED(laserId, outIdx, , laserId);
                        _ASSIGN_IF_NEEDED(materialId, outIdx, , materialId);
                        _ASSIGN_IF_NEEDED(semanticId, outIdx, , semanticId);
                        _ASSIGN_IF_NEEDED(tick, outIdx, , tick);
                        _ASSIGN_IF_NEEDED(objectId, outIdx, , objectId);
                        _ASSIGN_IF_NEEDED(timeStampNs, outIdx, , timeStampNs);
                        _ASSIGN_IF_NEEDED(valid, outIdx, , valid);

#undef _ASSIGN_IF_NEEDED
                    }
                }
            }
        } // });

        if (keepOnlyPositiveDistance)
        {
            _RESIZE_IF_NEEDED(pointCloudData, atomicOutIdx);
            _RESIZE_IF_NEEDED(intensity, atomicOutIdx);
            _RESIZE_IF_NEEDED(range, atomicOutIdx);
            _RESIZE_IF_NEEDED(azimuth, atomicOutIdx);
            _RESIZE_IF_NEEDED(elevation, atomicOutIdx);
            _RESIZE_IF_NEEDED(velocityMs, atomicOutIdx);
            _RESIZE_IF_NEEDED(echoId, atomicOutIdx);
            _RESIZE_IF_NEEDED(emitterId, atomicOutIdx);
            _RESIZE_IF_NEEDED(laserId, atomicOutIdx);
            _RESIZE_IF_NEEDED(materialId, atomicOutIdx);
            _RESIZE_IF_NEEDED(semanticId, atomicOutIdx);
            _RESIZE_IF_NEEDED(tick, atomicOutIdx);
            _RESIZE_IF_NEEDED(objectId, atomicOutIdx);
            _RESIZE_IF_NEEDED(timeStampNs, atomicOutIdx);
            _RESIZE_IF_NEEDED(valid, atomicOutIdx);
#undef _RESIZE_IF_NEEDED
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
