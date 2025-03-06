// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/BaseSensorComponent.h"

#include <isaacSensorSchema/isaacImuSensor.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <IPhysicsSensor.h>
#include <map>
#include <memory>
#include <vector>

namespace isaacsim
{
namespace sensors
{
namespace physics
{

/**
 * @class ImuSensor
 * @brief Implementation of an Inertial Measurement Unit (IMU) sensor component
 * @details This class provides functionality for simulating an IMU sensor in the Isaac environment.
 *          It handles acceleration, angular velocity, and orientation measurements, with support
 *          for raw data buffering and interpolation. The sensor supports configurable filtering
 *          for various measurements and maintains a history of readings for signal processing.
 */
class ImuSensor : public IsaacBaseSensorComponent
{
public:
    /**
     * @brief Default constructor for the IMU sensor
     * @details Initializes the raw data buffer and resets the sensor to its initial state
     */
    ImuSensor() : IsaacBaseSensorComponent()
    {
        mRawBuffer.resize(mRawBufferSize, IsRawData());
        reset();
    }

    /**
     * @brief Initializes the IMU sensor with a data buffer
     * @param[in] rigidBodyDataBuffer Pointer to the buffer storing rigid body data
     * @param[in,out] mDataBufferIndex Reference to the current buffer index
     */
    void initialize(std::vector<float>* rigidBodyDataBuffer, size_t& mDataBufferIndex);

    /**
     * @brief Virtual destructor for proper cleanup
     */
    virtual ~ImuSensor();

    /**
     * @brief Retrieves the current sensor reading with optional interpolation
     * @param[in] interpolateFunction Optional function for interpolating between readings
     * @param[in] getLatestValue Whether to return the most recent value without interpolation
     * @param[in] readGravity Whether to include gravity in the acceleration readings
     * @return The current IMU sensor reading
     */
    IsReading getSensorReading(const std::function<IsReading(std::vector<IsReading>, float)>& interpolateFunction = nullptr,
                               const bool& getLatestValue = false,
                               const bool& readGravity = true);

    /**
     * @brief Resets the sensor to its initial state
     * @details Clears all buffers and resets internal state variables to their default values
     */
    void reset();

    /**
     * @brief Called by component manager tick to update sensor data
     * @details Processes finite difference data in mRawReadingList and saves in mReadingPair
     */
    virtual void onPhysicsStep();

    /**
     * @brief Empty tick implementation as processing is done in onPhysicsStep
     */
    virtual void tick()
    {
    }

    /**
     * @brief Searches for and validates the parent rigid body for the IMU sensor
     * @return True if a valid parent is found, false otherwise
     */
    bool findValidParent();

    /**
     * @brief Handles component property changes
     * @details Updates sensor configuration when properties are modified through the interface
     */
    void onComponentChange();

    /**
     * @brief Called when simulation is stopped
     * @details The virtual onStop will clear everything on stop
     */
    virtual void onStop();

    /**
     * @brief Utility function to print IMU sensor reading data for debugging
     * @param[in] reading The sensor reading to print
     */
    void printIsReading(const IsReading& reading);

private:
    /** @brief Properties structure for the IMU sensor */
    IsProperties mProps;

    /** @brief Size of raw data buffer, must be larger than 2*mLinearAccelerationFilterSize */
    int mRawBufferSize = 20;

    /** @brief Current index in the data buffer */
    size_t mDataBufferIndex = 0;

    /** @brief Pointer to the rigid body data buffer */
    std::vector<float>* mRigidBodyDataBuffer = nullptr;

    /** @brief Initial buffer state */
    IsRawData mInitBuffer;

    /** @brief Raw velocities data array */
    std::vector<IsRawData> mRawBuffer;

    /** @brief Moving average window size for angular velocities */
    int mAngularVelocityFilterSize = 1;

    /** @brief Moving average window size for finite difference acceleration */
    int mLinearAccelerationFilterSize = 1;

    /** @brief Moving average window size for orientation values */
    int mOrientationFilterSize = 1;

    /** @brief IsReading at the measurement sensor period */
    std::vector<IsReading> mSensorReadingsSensorFrame;

    /** @brief Sensor readings in sensor timestamps */
    std::vector<IsReading> mSensorReadings;

    /** @brief Unit scale factor for measurements */
    double mUnitScale{ 1.0 };

    /** @brief Current sensor time */
    float mSensorTime{ 0 };

    /** @brief Previous enabled state */
    bool mPreviousEnabled{ true };

    /** @brief Gravity vector in sensor frame */
    omni::math::linalg::vec3d mGravitySensorFrame;

    /** @brief Gravity vector in world frame */
    omni::math::linalg::vec3d mGravity;
};


}
}
}
