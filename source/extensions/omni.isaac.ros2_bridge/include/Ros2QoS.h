// Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <nlohmann/json.hpp>

#include <iostream>
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

const std::map<std::string, Ros2QoSHistoryPolicyType> Ros2QoSHistoryString2PolicyMap = {
    { "systemDefault", Ros2QoSHistoryPolicyType::eSystemDefault },
    { "keepLast", Ros2QoSHistoryPolicyType::eKeepLast },
    { "keepAll", Ros2QoSHistoryPolicyType::eKeepAll },
    { "unknown", Ros2QoSHistoryPolicyType::eUnknown }
};

const std::map<std::string, Ros2QoSReliabilityPolicyType> Ros2QoSReliabilityString2PolicyMap = {
    { "systemDefault", Ros2QoSReliabilityPolicyType::eSystemDefault },
    { "reliable", Ros2QoSReliabilityPolicyType::eReliable },
    { "bestEffort", Ros2QoSReliabilityPolicyType::eBestEffort },
    { "unknown", Ros2QoSReliabilityPolicyType::eUnknown }
};

const std::map<std::string, Ros2QoSDurabilityPolicyType> Ros2QoSDurabilityString2PolicyMap = {
    { "systemDefault", Ros2QoSDurabilityPolicyType::eSystemDefault },
    { "transientLocal", Ros2QoSDurabilityPolicyType::eTransientLocal },
    { "volatile", Ros2QoSDurabilityPolicyType::eVolatile },
    { "unknown", Ros2QoSDurabilityPolicyType::eUnknown }
};

const std::map<std::string, Ros2QoSLivelinessPolicyType> Ros2QoSLivelinessString2PolicyMap = {
    { "systemDefault", Ros2QoSLivelinessPolicyType::eSystemDefault },
    { "automatic", Ros2QoSLivelinessPolicyType::eAutomatic },

    // manualByNode deprecated
    //  {"manualByNode", Ros2QoSLivelinessPolicyType::eManualByNode},
    { "manualByTopic", Ros2QoSLivelinessPolicyType::eManualByTopic },
    { "unknown", Ros2QoSLivelinessPolicyType::eUnknown }
};


using json = nlohmann::json;

// Function to validate the JSON string and check for required keys
inline static const bool jsonToRos2QoSProfile(Ros2QoSProfile& qos, const std::string& jsonString)
{
    // Define the required keys and their expected types
    std::map<std::string, std::function<bool(const json&)>> requiredKeys = {
        { "history", [](const json& j) { return j.is_string(); } },
        { "depth", [](const json& j) { return j.is_number_integer() && j.get<int>() >= 0; } },
        { "reliability", [](const json& j) { return j.is_string(); } },
        { "durability", [](const json& j) { return j.is_string(); } },
        { "deadline", [](const json& j) { return j.is_number_float() && j.get<double>() >= 0; } },
        { "lifespan", [](const json& j) { return j.is_number_float() && j.get<double>() >= 0; } },
        { "liveliness", [](const json& j) { return j.is_string(); } },
        { "leaseDuration", [](const json& j) { return j.is_number_float() && j.get<double>() >= 0; } }
    };

    // Parse the JSON string
    json j;
    try
    {
        j = json::parse(jsonString);
    }
    catch (json::parse_error& e)
    {

        std::cerr << "Parsing error: " << e.what() << '\n';
        return false;
    }

    // Check for the presence and type of required keys
    for (const auto& [key, validator] : requiredKeys)
    {
        if (!j.contains(key) || !validator(j[key]))
        {
            std::cerr << "Missing key: " << key << " Or invalid value: " << j[key] << '\n';
            return false;
        }
    }

    // Validate that the values for the keys exist in the corresponding maps
    if (Ros2QoSHistoryString2PolicyMap.find(j["history"].get<std::string>()) == Ros2QoSHistoryString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'history'\n";
        return false;
    }
    if (Ros2QoSReliabilityString2PolicyMap.find(j["reliability"].get<std::string>()) ==
        Ros2QoSReliabilityString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'reliability'\n";
        return false;
    }
    if (Ros2QoSDurabilityString2PolicyMap.find(j["durability"].get<std::string>()) ==
        Ros2QoSDurabilityString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'durability'\n";
        return false;
    }
    if (Ros2QoSLivelinessString2PolicyMap.find(j["liveliness"].get<std::string>()) ==
        Ros2QoSLivelinessString2PolicyMap.end())
    {
        std::cerr << "Invalid value for 'liveliness'\n";
        return false;
    }

    // Function to create and return a Ros2QoSTimeType struct from a double representing seconds
    auto createRos2QoSTimeType = [](double totalSeconds) -> Ros2QoSTimeType
    {
        uint64_t secs = static_cast<uint64_t>(totalSeconds);
        uint64_t nanoseconds = static_cast<uint64_t>((totalSeconds - secs) * 1e9);
        return Ros2QoSTimeType{ secs, nanoseconds };
    };

    qos.history = Ros2QoSHistoryString2PolicyMap.at(j["history"].get<std::string>());
    qos.depth = j["depth"];
    qos.reliability = Ros2QoSReliabilityString2PolicyMap.at(j["reliability"].get<std::string>());
    qos.durability = Ros2QoSDurabilityString2PolicyMap.at(j["durability"].get<std::string>());
    qos.deadline = createRos2QoSTimeType(j["deadline"]);
    qos.lifespan = createRos2QoSTimeType(j["lifespan"]);
    qos.liveliness = Ros2QoSLivelinessString2PolicyMap.at(j["liveliness"].get<std::string>());
    qos.livelinessLeaseDuration = createRos2QoSTimeType(j["leaseDuration"]);
    qos.avoid_ros_namespace_conventions = false;
    return true;
}
