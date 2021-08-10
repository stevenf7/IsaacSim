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
namespace imu_sensor
{
using IsHandle = uint64_t;

constexpr IsHandle kIsInvalidHandle = IsHandle(0);

/**
 * Properties of a IMU Sensor
 */
struct IsProperties
{
    carb::Float3 position; //<! Position relative to the parent body where the sensor is placed.
    carb::Float4 orientation; //<! quaternion orientation relative to the parent body where the sensor is placed.
    float sensorPeriod; //<! Sensor reading speed, in seconds. Zero means sync with simulation timestep.
};
/**
 * IMU Sensor Reading
 */
struct IsReading
{
    float time{ 0.0f }; //<! Simulation Timestamp for IMU sensor reading
    float lin_acc_x{ 0.0f }; //<! Accelerometer reading value x axis, in m/s^2
    float lin_acc_y{ 0.0f }; //<! Accelerometer reading value y axis, in m/s^2
    float lin_acc_z{ 0.0f }; //<! Accelerometer reading value z axis, in m/s^2
    float ang_vel_x{ 0.0f }; //<! Gyroscope reading value x axis, in rad/s
    float ang_vel_y{ 0.0f }; //<! Gyroscope reading value y axis, in rad/s
    float ang_vel_z{ 0.0f }; //<! Gyroscope reading value z axis, in rad/s
};

/**
 * Simulation IMU Raw Data
 */
struct IsRawData
{
    float time; //<! Simulation timestamp
    float dt; //<! Simulation time step for the impulse.
    float lin_vel_x; //<! linear velocity x raw reading value, in m/s
    float lin_vel_y; //<! linear velocity y raw reading value, in m/s
    float lin_vel_z; //<! linear velocity z raw reading value, in m/s
    float ang_vel_x; //<! angular velocity x raw reading value, in rad/s
    float ang_vel_y; //<! angular velocity y raw reading value, in rad/s
    float ang_vel_z; //<! angular velocity z raw reading value, in rad/s
};


}
}
}
