// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <memory>
#include <string>
#include <vector>

struct Ros2QoSTimeType
{
    uint64_t sec;
    uint64_t nsec;
};

enum class Ros2QoSHistoryPolicyType
{
    eSystemDefault,
    eKeepLast,
    eKeepAll,
    eUnknown
};

enum class Ros2QoSReliabilityPolicyType
{
    eSystemDefault,
    eReliable,
    eBestEffort,
    eUnknown
};

enum class Ros2QoSDurabilityPolicyType
{
    eSystemDefault,
    eTransientLocal,
    eVolatile,
    eUnknown
};

enum class Ros2QoSLivelinessPolicyType
{
    eSystemDefault,
    eAutomatic,
    eManualByNode, // Deprecated
    eManualByTopic,
    eUnknown
};

struct Ros2QoSProfile
{
    Ros2QoSHistoryPolicyType history;
    size_t depth;
    Ros2QoSReliabilityPolicyType reliability;
    Ros2QoSDurabilityPolicyType durability;
    Ros2QoSTimeType deadline;
    Ros2QoSTimeType lifespan;
    Ros2QoSLivelinessPolicyType liveliness;
    Ros2QoSTimeType livelinessLeaseDuration;
    bool avoid_ros_namespace_conventions;

    Ros2QoSProfile()
    {
        // NOTE : These are the values from rmw_qos_profile_default, which match in both Foxy and Humble
        history = Ros2QoSHistoryPolicyType::eKeepLast;
        depth = 10;
        reliability = Ros2QoSReliabilityPolicyType::eReliable;
        durability = Ros2QoSDurabilityPolicyType::eVolatile;
        deadline = { 0, 0 };
        lifespan = { 0, 0 };
        liveliness = Ros2QoSLivelinessPolicyType::eSystemDefault;
        livelinessLeaseDuration = { 0, 0 };
        avoid_ros_namespace_conventions = false;
    }
};
