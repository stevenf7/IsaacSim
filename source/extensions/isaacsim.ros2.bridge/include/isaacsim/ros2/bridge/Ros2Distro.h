// Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <optional>
#include <string>

namespace isaacsim::ros2::bridge
{

enum class Ros2Distro
{
    eHumble,
    eJazzy,
    // Add new distros here
    eCount // Keep this last
};

namespace
{

struct Ros2DistroInfo
{
    const char* name;
    Ros2Distro distro;
};

constexpr std::array<Ros2DistroInfo, 2> kDistroMapping{ { { "humble", Ros2Distro::eHumble },
                                                          { "jazzy", Ros2Distro::eJazzy } } };

inline std::string toLower(const std::string& input)
{
    std::string result{ input };
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return result;
}

inline std::optional<Ros2Distro> stringToRos2Distro(const std::string& lowerDistro)
{
    auto it = std::find_if(kDistroMapping.begin(), kDistroMapping.end(),
                           [&lowerDistro](const auto& info) { return lowerDistro == info.name; });

    if (it != kDistroMapping.end())
    {
        return it->distro;
    }
    return std::nullopt;
}

} // namespace

inline bool isRos2DistroSupported(const std::string& distro)
{
    const std::string lowerDistro = toLower(distro);
    return stringToRos2Distro(lowerDistro).has_value();
}

} // namespace isaacsim::ros2::bridge
