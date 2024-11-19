// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/** @file
 * @brief ROS 2 Quality of Service (QoS) related definitions.
 */
#pragma once

#include <nlohmann/json.hpp>

#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace isaacsim
{
namespace ros2
{
namespace bridge
{

/**
 * Enumerations of ROS 2 QoS History policy
 *
 * See [QoS policies](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html).
 */
enum class Ros2QoSHistoryPolicy
{
    eSystemDefault,
    eKeepLast,
    eKeepAll,
    eUnknown
};

/**
 * Enumerations of ROS 2 QoS Reliability policy
 *
 * See [QoS policies](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html).
 */
enum class Ros2QoSReliabilityPolicy
{
    eSystemDefault,
    eReliable,
    eBestEffort,
    eUnknown
};

/**
 * Enumerations of ROS 2 QoS Durability policy
 *
 * See [QoS policies](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html).
 */
enum class Ros2QoSDurabilityPolicy
{
    eSystemDefault,
    eTransientLocal,
    eVolatile,
    eUnknown
};

/**
 * Enumerations of ROS 2 QoS Liveliness policy
 *
 * See [QoS policies](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html).
 */
enum class Ros2QoSLivelinessPolicy
{
    eSystemDefault,
    eAutomatic,
    eManualByNode, // Deprecated
    eManualByTopic,
    eUnknown
};

/**
 * ROS 2 QoS Time
 */
struct Ros2QoSTime
{
    uint64_t sec; //!< Seconds.
    uint64_t nsec; //!< Nanoseconds.
};

/**
 * ROS 2 QoS Profile
 */
struct Ros2QoSProfile
{
    Ros2QoSHistoryPolicy history; //!< History QoS policy setting.
    size_t depth; //!< Size of the message queue.
    Ros2QoSReliabilityPolicy reliability; //!< Reliability QoS policy setting.
    Ros2QoSDurabilityPolicy durability; //!< Durability QoS policy setting.
    Ros2QoSTime deadline; //!< Period at which messages are expected to be sent/received.
    Ros2QoSTime lifespan; //!< Age at which messages are considered expired/no longer valid.
    Ros2QoSLivelinessPolicy liveliness; //!< Liveliness QoS policy setting.
    Ros2QoSTime livelinessLeaseDuration; //!< Time within which the RMW node or publisher must show that it is alive.
    bool avoidRosNamespaceConventions; //!< Whether to circumvent any ROS 2-specific namespacing conventions.

    /**
     * Constructor to system default values.
     */
    Ros2QoSProfile()
    {
        // These are the values from the `rmw_qos_profile_default`
        history = Ros2QoSHistoryPolicy::eKeepLast;
        depth = 10;
        reliability = Ros2QoSReliabilityPolicy::eReliable;
        durability = Ros2QoSDurabilityPolicy::eVolatile;
        deadline = { 0, 0 };
        lifespan = { 0, 0 };
        liveliness = Ros2QoSLivelinessPolicy::eSystemDefault;
        livelinessLeaseDuration = { 0, 0 };
        avoidRosNamespaceConventions = false;
    }
};

namespace
{

const std::map<std::string, Ros2QoSHistoryPolicy> Ros2QoSHistoryString2PolicyMap = {
    { "systemDefault", Ros2QoSHistoryPolicy::eSystemDefault },
    { "keepLast", Ros2QoSHistoryPolicy::eKeepLast },
    { "keepAll", Ros2QoSHistoryPolicy::eKeepAll },
    { "unknown", Ros2QoSHistoryPolicy::eUnknown }
};

const std::map<std::string, Ros2QoSReliabilityPolicy> Ros2QoSReliabilityString2PolicyMap = {
    { "systemDefault", Ros2QoSReliabilityPolicy::eSystemDefault },
    { "reliable", Ros2QoSReliabilityPolicy::eReliable },
    { "bestEffort", Ros2QoSReliabilityPolicy::eBestEffort },
    { "unknown", Ros2QoSReliabilityPolicy::eUnknown }
};

const std::map<std::string, Ros2QoSDurabilityPolicy> Ros2QoSDurabilityString2PolicyMap = {
    { "systemDefault", Ros2QoSDurabilityPolicy::eSystemDefault },
    { "transientLocal", Ros2QoSDurabilityPolicy::eTransientLocal },
    { "volatile", Ros2QoSDurabilityPolicy::eVolatile },
    { "unknown", Ros2QoSDurabilityPolicy::eUnknown }
};

const std::map<std::string, Ros2QoSLivelinessPolicy> Ros2QoSLivelinessString2PolicyMap = {
    { "systemDefault", Ros2QoSLivelinessPolicy::eSystemDefault },
    { "automatic", Ros2QoSLivelinessPolicy::eAutomatic },

    // manualByNode deprecated
    //  {"manualByNode", Ros2QoSLivelinessPolicy::eManualByNode},
    { "manualByTopic", Ros2QoSLivelinessPolicy::eManualByTopic },
    { "unknown", Ros2QoSLivelinessPolicy::eUnknown }
};

} // namespace anonymous

/**
 * Convert a QoS profile formatted as JSON to \ref Ros2QoSProfile.
 *
 * @param qos \ref Ros2QoSProfile instance where to storage the converted data.
 * @param jsonString JSON formatted string.
 * @returns Whether the conversion has been successfully completed.
 */
inline static const bool jsonToRos2QoSProfile(Ros2QoSProfile& qos, const std::string& jsonString)
{
    // Define the required keys and their expected types
    std::map<std::string, std::function<bool(const nlohmann::json&)>> requiredKeys = {
        { "history", [](const nlohmann::json& json) { return json.is_string(); } },
        { "depth", [](const nlohmann::json& json) { return json.is_number_integer() && json.get<int>() >= 0; } },
        { "reliability", [](const nlohmann::json& json) { return json.is_string(); } },
        { "durability", [](const nlohmann::json& json) { return json.is_string(); } },
        { "deadline", [](const nlohmann::json& json) { return json.is_number_float() && json.get<double>() >= 0; } },
        { "lifespan", [](const nlohmann::json& json) { return json.is_number_float() && json.get<double>() >= 0; } },
        { "liveliness", [](const nlohmann::json& json) { return json.is_string(); } },
        { "leaseDuration", [](const nlohmann::json& json) { return json.is_number_float() && json.get<double>() >= 0; } }
    };

    // Parse the JSON string
    nlohmann::json json;
    try
    {
        json = nlohmann::json::parse(jsonString);
    }
    catch (nlohmann::json::parse_error& e)
    {

        std::cerr << "Parsing error: " << e.what() << '\n';
        return false;
    }

    // Check for the presence and type of required keys
    for (const auto& [key, validator] : requiredKeys)
    {
        if (!json.contains(key) || !validator(json[key]))
        {
            std::cerr << "Missing key: " << key << " Or invalid value: " << json[key] << '\n';
            return false;
        }
    }

    // Validate that the values for the keys exist in the corresponding maps
    if (Ros2QoSHistoryString2PolicyMap.find(json["history"].get<std::string>()) == Ros2QoSHistoryString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'history'\n";
        return false;
    }
    if (Ros2QoSReliabilityString2PolicyMap.find(json["reliability"].get<std::string>()) ==
        Ros2QoSReliabilityString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'reliability'\n";
        return false;
    }
    if (Ros2QoSDurabilityString2PolicyMap.find(json["durability"].get<std::string>()) ==
        Ros2QoSDurabilityString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'durability'\n";
        return false;
    }
    if (Ros2QoSLivelinessString2PolicyMap.find(json["liveliness"].get<std::string>()) ==
        Ros2QoSLivelinessString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'liveliness'\n";
        return false;
    }

    // Function to create and return a Ros2QoSTime struct from a double representing seconds
    auto createRos2QoSTimeType = [](double totalSeconds) -> Ros2QoSTime
    {
        uint64_t secs = static_cast<uint64_t>(totalSeconds);
        uint64_t nanoseconds = static_cast<uint64_t>((totalSeconds - secs) * 1e9);
        return Ros2QoSTime{ secs, nanoseconds };
    };

    qos.history = Ros2QoSHistoryString2PolicyMap.at(json["history"].get<std::string>());
    qos.depth = json["depth"];
    qos.reliability = Ros2QoSReliabilityString2PolicyMap.at(json["reliability"].get<std::string>());
    qos.durability = Ros2QoSDurabilityString2PolicyMap.at(json["durability"].get<std::string>());
    qos.deadline = createRos2QoSTimeType(json["deadline"]);
    qos.lifespan = createRos2QoSTimeType(json["lifespan"]);
    qos.liveliness = Ros2QoSLivelinessString2PolicyMap.at(json["liveliness"].get<std::string>());
    qos.livelinessLeaseDuration = createRos2QoSTimeType(json["leaseDuration"]);
    qos.avoidRosNamespaceConventions = false;
    return true;
}

} // namespace bridge
} // namespace ros2
} // namespace isaacsim
