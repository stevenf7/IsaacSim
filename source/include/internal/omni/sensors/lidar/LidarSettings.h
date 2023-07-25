// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/InterfaceUtils.h>
#include <carb/extras/Path.h>
#include <carb/settings/ISettings.h>
#include <carb/settings/SettingsUtils.h>
#include <carb/tokens/TokensUtils.h>

#include <internal/omni/sensors/Utils.h>
#include <omni/sensors/Settings.h>
namespace omni
{
namespace sensors
{
namespace nv
{
namespace lidar
{

inline std::string getProfileJsonAtPaths(const std::string& inSensorProfileName)
{
#ifdef BUILDING_FOR_ISAAC_SIM
    std::string sensorProfileName{ inSensorProfileName };
#else
    // Use example config if no config name is given
    std::string sensorProfileName{ inSensorProfileName == "" ? "Example_Rotary" : inSensorProfileName };
    //
#endif
    std::string json{ "" };

    carb::tokens::ITokens* tokens = carb::getCachedInterface<carb::tokens::ITokens>();
    if (!tokens)
    {
        CARB_LOG_ERROR("getProfileJsonAtPaths failed to get carb::tokens::ITokens");
    }
    // Use at least the default path.
    std::vector<std::string> paths;

    // Use this local function to resolve strings and create a json file name.
    const auto get_resolved_path = [](const std::string& path, carb::tokens::ITokens* tokens) {
        return carb::extras::Path(carb::tokens::resolveString(tokens, path.c_str()).c_str()).getNormalized().getString();
    };

    // If app.sensors.nv.lidar.profileBaseFolder is not empty get its strings.
    if (auto* iSettings = carb::getCachedInterface<carb::settings::ISettings>())
    {
        const size_t numPaths{ iSettings->getArrayLength(omni::sensors::nv::kLidarBaseFolderSetting) };
        for (size_t i = 0; i < numPaths; ++i)
        {
            // Add trailing / for folder path
            std::string directory = carb::settings::getStringAt(iSettings, omni::sensors::nv::kLidarBaseFolderSetting, i);
            if (directory.back() != '/')
            {
                directory += "/";
            }
            paths.push_back(directory);
        }
    }

    paths.push_back("${app}/../exts/omni.sensors.nv.lidar/data/");

    // Search all known paths for the LiDAR config file.
    for (const std::string& path : paths)
    {
        const std::string profilePath = get_resolved_path(path, tokens) + sensorProfileName + ".json";
        json = omni::sensors::nv::ReadWholeTextFile(profilePath);
        if (!json.empty())
        {
            break;
        }
    }

    // Use invalid profile to indicate wrong profile
    if (json.empty())
    {
        CARB_LOG_ERROR(
            "getProfileJsonAtPaths could not find LiDAR config file: \"%s\", in extension or in supplied paths:",
            sensorProfileName.c_str());
        for (const std::string& path : paths)
        {
            CARB_LOG_ERROR("\t%s", (get_resolved_path(path, tokens) + sensorProfileName + ".json").c_str());
        }
        CARB_LOG_ERROR("getProfileJsonAtPaths is creating a minimal lidar profile with only emitter");
        json =
            "{\"class\":\"sensor\",\"type\":\"lidar\",\"name\":\"Minimal Invalid\",\"driveWorksId\":\"INVALID\",\"profile\":{\"scanType\":\"solidState\",\"intensityProcessing\":\"normalization\",\"rayType\":\"IDEALIZED\",\"nearRangeM\":1.0,\"farRangeM\":2.0,\"startAzimuthDeg\":0.0,\"endAzimuthDeg\":1.0,\"upElevationDeg\":0.0,\"downElevationDeg\":-1.0,\"rangeResolutionM\":0.004,\"rangeAccuracyM\":0.02,\"avgPowerW\":0.002,\"wavelengthNm\":903.0,\"pulseTimeNs\":6,\"maxReturns\":1,\"reportRateBaseHz\":1,\"scanRateBaseHz\":1,\"numberOfEmitters\":1,\"reportTypes\":\"Strongest,Last,Dual\",\"scanRatesHz\":[1.0],\"emitters\":{\"azimuthDeg\":[0],\"elevationDeg\":[0],\"fireTimeNs\":[0]},\"intensityMappingType\":\"LINEAR\"}}";
    }
    return json;
}

} // namespace lidar
} // namespace nv
} // namespace sensors
} // namespace omni
