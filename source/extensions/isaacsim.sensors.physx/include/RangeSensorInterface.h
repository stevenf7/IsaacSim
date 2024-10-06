// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <usdrt/gf/matrix.h>

namespace isaacsim
{
namespace sensors
{
namespace physx
{

using RangeSensorHandle = uint64_t;
constexpr RangeSensorHandle kInvalidHandle = RangeSensorHandle(0);

struct LidarSensorInterface
{
    CARB_PLUGIN_INTERFACE("isaacsim::sensors::physx::LidarSensorInterface", 0, 1);


    int(CARB_ABI* getNumCols)(const char* sensorPath);
    int(CARB_ABI* getNumRows)(const char* sensorPath);
    int(CARB_ABI* getNumColsTicked)(const char* sensorPath);

    uint16_t*(CARB_ABI* getDepthData)(const char* sensorPath);
    float*(CARB_ABI* getBeamTimeData)(const char* sensorPath);
    float*(CARB_ABI* getLinearDepthData)(const char* sensorPath);
    uint8_t*(CARB_ABI* getIntensityData)(const char* sensorPath);
    float*(CARB_ABI* getZenithData)(const char* sensorPath);
    float*(CARB_ABI* getAzimuthData)(const char* sensorPath);
    carb::Float3*(CARB_ABI* getPointCloud)(const char* sensorPath);
    std::vector<std::string>(CARB_ABI* getPrimData)(const char* sensorPath);
    bool(CARB_ABI* isLidarSensor)(const char* sensorPath);
    uint64_t(CARB_ABI* getSequenceNumber)(const char* sensorPath);
    carb::Float2(CARB_ABI* getAzimuthRange)(const char* sensorPath);
    carb::Float2(CARB_ABI* getZenithRange)(const char* sensorPath);
};

struct RadarSensorInterface
{
    CARB_PLUGIN_INTERFACE("isaacsim::sensors::physx::RadarSensorInterface", 0, 1);
    bool(CARB_ABI* isRadarSensor)(const char* sensorPath);
};

struct GenericSensorInterface
{
    CARB_PLUGIN_INTERFACE("isaacsim::sensors::physx::GenericSensorInterface", 0, 1);
    bool(CARB_ABI* isGenericSensor)(const char* sensorPath);

    int(CARB_ABI* getNumSamplesTicked)(const char* sensorPath);
    uint16_t*(CARB_ABI* getDepthData)(const char* sensorPath);
    float*(CARB_ABI* getLinearDepthData)(const char* sensorPath);
    uint8_t*(CARB_ABI* getIntensityData)(const char* sensorPath);
    float*(CARB_ABI* getZenithData)(const char* sensorPath);
    float*(CARB_ABI* getAzimuthData)(const char* sensorPath);
    carb::Float3*(CARB_ABI* getPointCloud)(const char* sensorPath);
    carb::Float3*(CARB_ABI* getOffsetData)(const char* sensorPath);

    bool(CARB_ABI* sendNextBatch)(const char* sensorPath);
    void(CARB_ABI* setNextBatchRays)(const char* sensorPath,
                                     const float* azimuth_angles,
                                     const float* zenith_angles,
                                     const int sample_length);

    void(CARB_ABI* setNextBatchOffsets)(const char* sensorPath, const float* origin_offsets, const int sample_length);
};

struct LightBeamSensorInterface
{
    CARB_PLUGIN_INTERFACE("isaacsim::sensors::physx::LightBeamSensorInterface", 0, 1);

    //! Check is Prim a LightBeamSensorSchema
    /*! Return True for is, False for is not an LightBeamSensorSchema
     * \param usdPath sensor prim path
     * \return true for is, false for is not an LightBeamSensorSchema
     */
    bool(CARB_ABI* isLightBeamSensor)(const char* usdPath);
    float*(CARB_ABI* getLinearDepthData)(const char* usdPath);
    int(CARB_ABI* getNumRays)(const char* usdPath);
    uint8_t*(CARB_ABI* getBeamHitData)(const char* usdPath);
    carb::Float3*(CARB_ABI* getHitPosData)(const char* usdPath);
    void(CARB_ABI* getTransformData)(const char* usdPath, omni::math::linalg::matrix4d& matrixOutput);
    carb::Float3*(CARB_ABI* getBeamOrigins)(const char* usdPath);
    carb::Float3*(CARB_ABI* getBeamEndPoints)(const char* usdPath);
};


}
}
}
