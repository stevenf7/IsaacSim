// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Defines.h>

namespace omni
{
namespace isaac
{
namespace lidar
{
using LidarHandle = uint64_t;

constexpr LidarHandle kLidarInvalidHandle = LidarHandle(0);


struct LidarInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::lidar::LidarInterface", 0, 1);

    LidarHandle(CARB_ABI* getLidarHandle)(const char* usdPath);

    float(CARB_ABI* getHorizontalFov)(LidarHandle handle);
    float(CARB_ABI* getVerticalFov)(LidarHandle handle);
    float(CARB_ABI* getRotationRate)(LidarHandle handle);
    float(CARB_ABI* getHorizontalResolution)(LidarHandle handle);
    float(CARB_ABI* getVerticalResolution)(LidarHandle handle);
    float(CARB_ABI* getMinRange)(LidarHandle handle);
    float(CARB_ABI* getMaxRange)(LidarHandle handle);
    bool(CARB_ABI* getHighLod)(LidarHandle handle);
    bool(CARB_ABI* getDrawLidarPoints)(LidarHandle handle);

    void(CARB_ABI* setHorizontalFov)(LidarHandle handle, const float& horizontalFov);
    void(CARB_ABI* setVerticalFov)(LidarHandle handle, const float& verticalFov);
    void(CARB_ABI* setRotationRate)(LidarHandle handle, const float& rotationRate);
    void(CARB_ABI* setHorizontalResolution)(LidarHandle handle, const float& horizontalResolution);
    void(CARB_ABI* setVerticalResolution)(LidarHandle handle, const float& verticalResolution);
    void(CARB_ABI* setMinRange)(LidarHandle handle, const float& minRange);
    void(CARB_ABI* setMaxRange)(LidarHandle handle, const float& maxRange);
    void(CARB_ABI* setHighLod)(LidarHandle handle, const bool& highLod);
    void(CARB_ABI* setDrawLidarPoints)(LidarHandle handle, const bool& drawLidarPoints);

    int(CARB_ABI* getNumCols)(LidarHandle handle);
    int(CARB_ABI* getNumRows)(LidarHandle handle);

    int(CARB_ABI* getNumColsTicked)(LidarHandle handle);

    uint16_t*(CARB_ABI* getDepthData)(LidarHandle handle);
    uint8_t*(CARB_ABI* getIntensityData)(LidarHandle handle);
    float*(CARB_ABI* getZenithData)(LidarHandle handle);
    float*(CARB_ABI* getAzimuthData)(LidarHandle handle);
};

}
}
}
