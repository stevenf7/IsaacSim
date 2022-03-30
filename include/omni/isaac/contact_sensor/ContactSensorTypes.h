// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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
namespace isaac_sensor
{
/**
 * Properties of a Contact Sensor
 */
struct CsProperties
{
    carb::Float3 position{ 0.0f, 0.0f, 0.0f }; //<! Position relative to the parent body where the sensor is placed.
    float radius{ 0.0f }; //<! Radius from the sensor position. negative values indicate it's a full body sensor.
    float minThreshold{ 0.0f }; //<! Minimum force that the sensor can read. Forces below this value will not trigger a
                                // reading.
    float maxThreshold{ 0.0f }; //<! Maximum force that the sensor can register. Forces above this value will be
                                // clamped.
    float sensorPeriod{ 0.0f }; //<! Sensor reading speed, in seconds. Zero means sync with simulation timestep.
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
    float time{ 0.0f }; //<! Simulation timestamp
    float dt{ 0.0f }; //<! Simulation time step for the impulse.
    char* body0; //<! First body on contact
    char* body1; //<! Second body on contact
    carb::Float3 position{ 0.0f, 0.0f, 0.0f }; //<! Contact Position, in world coordinates
    carb::Float3 normal{ 0.0f, 0.0f, 0.0f }; //<! Contact Normal, in world coordinates
    carb::Float3 impulse{ 0.0f, 0.0f, 0.0f }; //<! Contact Impulse, in world coordinates
};


}
}
}
