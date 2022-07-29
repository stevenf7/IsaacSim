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

// #include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/BaseResetNode.h>
// #include <rangeSensorSchema/lidar.h>
#include <lidar/LidarParameterType.h>
#include <lidar/LidarReturnTypes.h>

#include <OgnIsaacReadRTXLidarPointCloudDatabase.h>
#include <math.h>
namespace omni
{
namespace isaac
{
namespace core_nodes
{
#define PI 3.141592653589f

inline constexpr float Deg2Rad(float deg)
{
    return (deg / 180.f) * PI;
}


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


inline void convertReturnToPoint(GfVec3f& point,
                                 const LidarTick& lidarTick,
                                 const LidarReturn& lidarReturn,
                                 //  const LidarRotaryProfile* profile,
                                 const uint32_t echoId,
                                 const bool rightHanded)
{
    // const auto& emitterProfile = profile->emitterStates[lidarTick.state].emitterProfiles[lidarReturn.emitterId];
    // const uint32_t rangeId{ emitterProfile->rangeId };
    // const float rangeNearMinM{ profile->ranges[rangeId].min };
    // const float rangeFarMaxM{ profile->ranges[rangeId].max };

    const float beamOriginMX{ 0.f };
    const float beamOriginMY{ 0.f }; // emitterProfile.horOffsetM };
    const float beamOriginMZ{ 0.f }; // emitterProfile.vertOffsetM };
    float beamOriginDistM{ beamOriginMX * beamOriginMX + beamOriginMY * beamOriginMY + beamOriginMZ * beamOriginMZ };
    beamOriginDistM = beamOriginDistM > FLT_EPSILON ? ::sqrtf(beamOriginDistM) : 0.f;


    const float azimuthDeg{ rightHanded ? (360.f - lidarReturn.azimuthDeg) : lidarReturn.azimuthDeg };
    const float elevationDeg{ lidarReturn.elevationDeg };

    const float azimuthRad{ Deg2Rad(azimuthDeg) };
    const float elevationRad{ Deg2Rad(elevationDeg) };

    const float sinAzimuth{ ::sinf(azimuthRad) };
    const float cosAzimuth{ ::cosf(azimuthRad) };
    const float sinElevation{ ::sinf(elevationRad) };
    const float cosElevation{ ::cosf(elevationRad) };

    const float rawDistanceM = lidarReturn.distance;

    // setPointCommons(point, lidarReturn, lidarTick, echoId);
    // if (rawDistanceM < rangeNearMinM || rawDistanceM > rangeFarMaxM)
    // {
    //     point.x = 0.f;
    //     point.y = 0.f;
    //     point.z = 0.f;
    //     point.intensity = 0.f;
    //     return;
    // }

    const float distanceM = rawDistanceM; //+ emitterProfile.distanceCorrectionM;

    // Ray origin in meter
    const float rayOriginMX{ cosAzimuth * beamOriginMX - sinAzimuth * beamOriginMY };
    const float rayOriginMY{ cosAzimuth * beamOriginMY + sinAzimuth * beamOriginMX };
    const float rayOriginMZ{ beamOriginMZ };

    // Ray direction in meter
    const float rayDirectionX{ cosElevation * cosAzimuth };
    const float rayDirectionY{ cosElevation * sinAzimuth };
    const float rayDirectionZ{ sinElevation };

    point.Set(rayOriginMX + rayDirectionX * distanceM, rayOriginMY + rayDirectionY * distanceM,
              rayOriginMZ + rayDirectionZ * distanceM);

    // // point.y = sign * (rayOriginMY + rayDirectionY * distanceM);
    // point.y = rayOriginMY + rayDirectionY * distanceM;
    // point.z = rayOriginMZ + rayDirectionZ * distanceM;

    // point.azimuth = azimuthRad;
    // point.elevation = elevationRad;
    // // Add beam origin distance directly? -> see differences in resim
    // point.range = distanceM + beamOriginDistM;
    // point.intensity = lidarReturn.intensity;

    // if (rightHanded)
    //     point.azimuth = Deg2Rad(360.f) - point.azimuth;
    // // fit azimuth into [-PI, PI] ala atan2
    // if (point.azimuth > Deg2Rad(180.f))
    //     point.azimuth -= Deg2Rad(360.f);
}


class OgnIsaacReadRTXLidarPointCloud : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadRTXLidarPointCloudDatabase::sInternalState<OgnIsaacReadRTXLidarPointCloud>(nodeObj);

        // state.mLidarSensorInterface = carb::getCachedInterface<omni::isaac::range_sensor::LidarSensorInterface>();

        // if (!state.mLidarSensorInterface)
        // {
        //     CARB_LOG_ERROR("Failed to acquire omni::isaac::range_sensor interface");
        //     return;
        // }
    }

    static bool compute(OgnIsaacReadRTXLidarPointCloudDatabase& db)
    {
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
        // std::cout << "TICKS: " << db.inputs.data.size() << " " << parameter->async.numTicks << " "
        //           << parameter->async.numChannels << std::endl;

        // std::cout << "TEST: " << (void*)(input) << " " << sizeof(LidarParameterType) << " " << sizeof(LidarTick) << "
        // "
        //           << sizeof(LidarReturn) << std::endl;

        const LidarTick* lidarTicks = reinterpret_cast<const LidarTick*>(input + sizeof(LidarParameterType));
        const LidarReturn* lidarReturns = reinterpret_cast<const LidarReturn*>(
            input + sizeof(LidarParameterType) + sizeof(LidarTick) * parameter->async.numTicks);

        db.outputs.pointCloudData().resize(parameter->async.numChannels * parameter->async.numEchos *
                                           parameter->async.numTicks);
        size_t numPoints = 0;
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
                    if (lidarReturn.distance > 0.f)
                    {
                        // sensors::lidar::LidarPoint& p = hpc.points[hpc.numPoints];
                        // p.tick = tick + hpc.accumulatedTicks;
                        // p.valid = lidarReturn.intensity > 0.f || lidarReturn.azimuthDeg > 0.f ||
                        //           lidarReturn.elevationDeg > 0.f || lidarReturn.deltaTimeNs > 0 ||
                        //           lidarReturn.emitterId > 0 || lidarReturn.beamId > 0;
                        convertReturnToPoint(
                            db.outputs.pointCloudData()[numPoints], lidarTick, lidarReturn, echoId, true);
                        // ++(hpc.numPoints);
                        ++numPoints;
                    }
                }
            }
        }
        db.outputs.pointCloudData().resize(numPoints);
        db.outputs.execOut() = kExecutionAttributeStateEnabled;

        return true;
    }

    virtual void reset()
    {
        mResetPCL = true;
        mFirstFrame = true;
    }


private:
    const char* mLidarPrimPath = nullptr;
    std::vector<GfVec3f> mPointsData;
    uint64_t mPrevSequenceNumber = 0;
    bool mResetPCL = true;
    size_t mNumBeamsRemainingPCL;
    bool mFirstFrame = true;
    double mUnitScale;
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
