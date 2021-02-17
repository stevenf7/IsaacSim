// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
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
namespace range_sensor
{

using RangeSensorHandle = uint64_t;
constexpr RangeSensorHandle kInvalidHandle = RangeSensorHandle(0);

struct DebugData
{
    carb::Float3 startPos;
    carb::Float3 endPos;
    uint32_t color;
};

struct LidarSensorInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::range_sensor::LidarSensorInterface", 0, 1);


    int(CARB_ABI* getNumCols)(const char* sensorPath);
    int(CARB_ABI* getNumRows)(const char* sensorPath);
    int(CARB_ABI* getNumColsTicked)(const char* sensorPath);

    uint16_t*(CARB_ABI* getDepthData)(const char* sensorPath);
    float*(CARB_ABI* getLinearDepthData)(const char* sensorPath);
    uint8_t*(CARB_ABI* getIntensityData)(const char* sensorPath);
    float*(CARB_ABI* getZenithData)(const char* sensorPath);
    float*(CARB_ABI* getAzimuthData)(const char* sensorPath);
    carb::Float3*(CARB_ABI* getPointCloud)(const char* sensorPath);
    bool(CARB_ABI* isLidarSensor)(const char* sensorPath);
};

struct UltrasonicSensorInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::range_sensor::UltrasonicSensorInterface", 0, 1);
    bool(CARB_ABI* isUSS)(const char* sensorPath);
    int(CARB_ABI* getNumCols)(const char* sensorPath);
    int(CARB_ABI* getNumRows)(const char* sensorPath);
    int(CARB_ABI* getNumEmitters)(const char* sensorPath);
    int(CARB_ABI* getNumColsTicked)(const char* sensorPath);
    int(CARB_ABI* getNumBins)(const char* sensorPath);


    uint16_t*(CARB_ABI* getDepthData)(const char* sensorPath, int emitterIndex);
    float*(CARB_ABI* getLinearDepthData)(const char* sensorPath, int emitterIndex);
    float*(CARB_ABI* getEnvelope)(const char* sensorPath, int emitterIndex);
    std::vector<float>(CARB_ABI* getEnvelopeArrayFlattened)(const char* sensorPath);
    uint8_t*(CARB_ABI* getIntensityData)(const char* sensorPath, int emitterIndex);
    float*(CARB_ABI* getZenithData)(const char* sensorPath);
    float*(CARB_ABI* getAzimuthData)(const char* sensorPath);
    carb::Float3*(CARB_ABI* getPointCloud)(const char* sensorPath);
};

struct RadarSensorInterface
{
    CARB_PLUGIN_INTERFACE("omni::isaac::range_sensor::RadarSensorInterface", 0, 1);
    bool(CARB_ABI* isRadarSensor)(const char* sensorPath);
};

}
}
}
