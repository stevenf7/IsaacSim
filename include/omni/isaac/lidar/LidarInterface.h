// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace lidar
{
using LidarHandle = uint64_t;

constexpr LidarHandle kLidarInvalidHandle = LidarHandle(0);

struct LidarDebugData
{
    carb::Float3 startPos;
    carb::Float3 endPos;
    uint32_t color;
};

struct LidarInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::lidar::LidarInterface", 0, 1);


    int(CARB_ABI* getNumCols)(const char* lidarPath);
    int(CARB_ABI* getNumRows)(const char* lidarPath);
    int(CARB_ABI* getNumColsTicked)(const char* lidarPath);

    uint16_t*(CARB_ABI* getDepthData)(const char* lidarPath);
    float*(CARB_ABI* getLinearDepthData)(const char* lidarPath);
    uint8_t*(CARB_ABI* getIntensityData)(const char* lidarPath);
    float*(CARB_ABI* getZenithData)(const char* lidarPath);
    float*(CARB_ABI* getAzimuthData)(const char* lidarPath);
    carb::Float3*(CARB_ABI* getPointCloud)(const char* lidarPath);
    bool(CARB_ABI* isLidar)(const char* lidarPath);
};

}
}
}
