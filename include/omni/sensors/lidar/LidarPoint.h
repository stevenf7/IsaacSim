// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

//! @file
//!
//! @brief Definitions for lidar point cloud types

#include <omni/sensors/lidar/LidarParameterType.h>
#include <omni/sensors/lidar/LidarReturnTypes.h>

#include <cstdint>

namespace omni
{
namespace sensors
{
namespace lidar
{

#pragma pack(push, 1)

/**
 * LidarPoint, one lidar detection/measurement
 */
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
    uint32_t emitterId{ 0 }; /**<  emitter id */
    uint32_t laserId{ 0 }; /**<  beam/laser detector id */
    uint32_t materialId{ 0 }; /**< hit point material id */
    float hitPointNormal[3]; /**< hit point normal */
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
    SensorPoseAtTime frameStart; /**< sensor transformation at frame start*/
    SensorPoseAtTime frameEnd; /**< sensor transformation at frame end*/
    uint32_t numPoints{ 0 }; /**< number of points in the array */
    uint32_t accumulatedTicks{ 0 }; /**< accumulated ticks of the points */
    LidarPoint* points{ nullptr }; /**< points array */
    float* tickAzimuths{ nullptr }; /**< ticks array */
    uint32_t* tickStates{ nullptr }; /**< ticks array */
    uint64_t* tickTimestamps{ nullptr }; /**< ticks array */
};

#pragma pack(pop)

} // namespace lidar
} // namespace sensors
} // namespace omni
