// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "Ros2Foxy.h"

#include <include/Ros2Macros.h>
#include <rcl/rcl.h>


const std::map<Ros2QoSHistoryPolicyType, rmw_qos_history_policy_t> ros2QoSHistoryMap = {
    { Ros2QoSHistoryPolicyType::eSystemDefault, RMW_QOS_POLICY_HISTORY_SYSTEM_DEFAULT },
    { Ros2QoSHistoryPolicyType::eKeepLast, RMW_QOS_POLICY_HISTORY_KEEP_LAST },
    { Ros2QoSHistoryPolicyType::eKeepAll, RMW_QOS_POLICY_HISTORY_KEEP_ALL },
    { Ros2QoSHistoryPolicyType::eUnknown, RMW_QOS_POLICY_HISTORY_UNKNOWN }
};


const std::map<Ros2QoSReliabilityPolicyType, rmw_qos_reliability_policy_t> ros2QoSReliabilityMap = {
    { Ros2QoSReliabilityPolicyType::eSystemDefault, RMW_QOS_POLICY_RELIABILITY_SYSTEM_DEFAULT },
    { Ros2QoSReliabilityPolicyType::eReliable, RMW_QOS_POLICY_RELIABILITY_RELIABLE },
    { Ros2QoSReliabilityPolicyType::eBestEffort, RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT },
    { Ros2QoSReliabilityPolicyType::eUnknown, RMW_QOS_POLICY_RELIABILITY_UNKNOWN }
};


const std::map<Ros2QoSDurabilityPolicyType, rmw_qos_durability_policy_t> ros2QoSDurabilityMap = {
    { Ros2QoSDurabilityPolicyType::eSystemDefault, RMW_QOS_POLICY_DURABILITY_SYSTEM_DEFAULT },
    { Ros2QoSDurabilityPolicyType::eTransientLocal, RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL },
    { Ros2QoSDurabilityPolicyType::eVolatile, RMW_QOS_POLICY_DURABILITY_VOLATILE },
    { Ros2QoSDurabilityPolicyType::eUnknown, RMW_QOS_POLICY_DURABILITY_UNKNOWN }
};

// NOTE : RMW_QOS_POLICY_LIVELINESS_MANUAL_BY_NODE is deprecated and throws compiler errors,
//        so we handle this by just using the system default
const std::map<Ros2QoSLivelinessPolicyType, rmw_qos_liveliness_policy_t> ros2QoSLivelinessMap = {
    { Ros2QoSLivelinessPolicyType::eSystemDefault, RMW_QOS_POLICY_LIVELINESS_SYSTEM_DEFAULT },
    { Ros2QoSLivelinessPolicyType::eAutomatic, RMW_QOS_POLICY_LIVELINESS_AUTOMATIC },
    { Ros2QoSLivelinessPolicyType::eManualByNode, RMW_QOS_POLICY_LIVELINESS_SYSTEM_DEFAULT },
    { Ros2QoSLivelinessPolicyType::eManualByTopic, RMW_QOS_POLICY_LIVELINESS_MANUAL_BY_TOPIC },
    { Ros2QoSLivelinessPolicyType::eUnknown, RMW_QOS_POLICY_LIVELINESS_UNKNOWN }
};

rmw_time_t convertRos2QosTimeToFoxy(const Ros2QoSTimeType& ros2Time)
{
    return { ros2Time.sec, ros2Time.nsec };
}

rmw_qos_profile_t Ros2QoSProfileFoxyConverter::convert(const Ros2QoSProfile& qos)
{
    rmw_qos_profile_t profile;

    profile.history = ros2QoSHistoryMap.at(qos.history);
    profile.depth = qos.depth;
    profile.reliability = ros2QoSReliabilityMap.at(qos.reliability);
    profile.durability = ros2QoSDurabilityMap.at(qos.durability);
    profile.deadline = convertRos2QosTimeToFoxy(qos.deadline);
    profile.lifespan = convertRos2QosTimeToFoxy(qos.lifespan);
    profile.liveliness = ros2QoSLivelinessMap.at(qos.liveliness);
    profile.liveliness_lease_duration = convertRos2QosTimeToFoxy(qos.livelinessLeaseDuration);
    profile.avoid_ros_namespace_conventions = qos.avoid_ros_namespace_conventions;

    return profile;
}
