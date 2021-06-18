// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
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

// #include <PxActor.h>
#include <limits>

namespace omni
{
namespace isaac
{
namespace contact_sensor
{
using CsHandle = uint64_t;

constexpr CsHandle kCsInvalidHandle = CsHandle(0);

/**
 * Properties of a Contact Sensor
 */
struct CsProperties
{
    carb::Float3 position; //<! Position relative to the parent body where the sensor is placed.
    float radius; //<! Radius from the sensor position. negative values indicate it's a full body sensor.
    float minThreshold; //<! Minimum force that the sensor can read. Forces below this value will not trigger a reading.
    float maxThreshold; //<! Maximum force that the sensor can register. Forces above this value will be clamped.
    float sensorPeriod; //<! Sensor reading speed, in seconds. Zero means sync with simulation timestep.
};
/**
 * Contact Sensor Reading
 */
struct CsReading
{
    float time{ 0.0f }; //<! Simulation Timestamp for contact sensor reading
    float value{ 0.0f }; //<! Reading value, in N
    bool inContact{ false }; //<! Flag that checks if the sensor is in contact with something or not
};

/**
 * Simulation Contact Raw Data
 */
struct CsRawData
{
    float time; //<! Simulation timestamp
    float dt; //<! Simulation time step for the impulse.
    char* body0; //<! First body on contact
    char* body1; //<! Second body on contact
    carb::Float3 position; //<! Contact Position, in world coordinates
    carb::Float3 normal; //<! Contact Normal, in world coordinates
    carb::Float3 impulse; //<! Contact Impulse, in world coordinates
};


}
}
}
