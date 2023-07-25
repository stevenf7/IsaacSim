// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
//! @file
//!
//! @brief LidarParameterType: Parameter for data stream of one simulated trace of the lidar simulation. Placed at the
//! begining of the data buffer (per trace)


#pragma once

#include <cstdint>

#pragma pack(push, 1) // Make sure we have consistent structure packing


/**
 * Lidar sync parameter for one data trace copied directly set -- 36 bytes
 */
struct LidarSyncParameter
{
    uint32_t numTicks; /**< number of ticks (sensor positions) in this trace data */
    std::size_t maxSizeBuffer; /**< maximum possible size of the lidar trace data in bytes (can be used for
                                * initialization)
                                */
    std::size_t currentSizeBuffer; /**< current size of the lidar trace data */
    uint64_t scanStartTimeNs; /**< start time of the corresponding scan (i.e. full rotation of a spinning lidar) */
    void* syncData{ nullptr }; /**<  sync data -- has to be set in the nodes to indicate that all async computation
                                      is ready if frames in flight == 1 */
};

struct SensorPose
{
    float posM[3]; /**< world space translation. [X, Y, Z] in m (trace begin) */
    float orientation[4]; /**<  world space rotation. [X, Y, Z, W] quaternion (trace begin) */
};

struct SensorPoseAtTime
{
    SensorPose pose{};
    uint64_t timeNs{ 0UL };
};

/**
 * Lidar async parameter for one data trace -- only safely accessible in async functions -- 55 bytes
 */
struct LidarAsyncParameter
{
    uint32_t numTicks; /**< number of ticks (sensor positions) in this trace data */
    float scanFrequency; /**< sensor frequency in hz */
    uint32_t ticksPerScan; /**< number of ticks of one full scan of the sensor */
    std::size_t maxSizeBuffer; /**< maximum possible size of the lidar trace data in bytes (can be used for
                                * initialization)
                                */
    std::size_t currentSizeBuffer; /**< current size of the lidar trace data */
    uint32_t numChannels; /**< number of channels (=detector) per tick */
    uint8_t numEchos; /**< number of echos per detector/laser */
    uint8_t padding[7];
    uint64_t startTimeNs; /**< start time of the trace data */
    uint64_t deltaTimeNs; /**< delta time of the trace data */
    uint64_t scanStartTimeNs; /**< start time of the corresponding scan (i.e. full rotation of a spinning lidar) */
    uint32_t startTick; /**< start tick of this frame/trace */
    SensorPose frameStart; /**< sensor transformation at frame start*/
    SensorPose frameEnd; /**< sensor transformation at frame end*/
};

/**
 * Lidar parameter for one data trace -- 91 bytes
 */
struct LidarParameterType
{
    LidarSyncParameter sync; /**< synchronous part of the parameter */
    LidarAsyncParameter async; /**< asynchronous part of the parameter */
};

#pragma pack(pop)
