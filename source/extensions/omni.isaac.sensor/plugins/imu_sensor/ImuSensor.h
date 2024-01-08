// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include <IsaacSensor.h>
#include <map>
#include <memory>
#include <vector>

namespace omni
{
namespace isaac
{
namespace sensor
{

class ImuSensor : public IsaacBaseSensorComponent
{
public:
    ImuSensor(omni::renderer::IDebugDraw* debugDraw, omni::physx::IPhysx* PhysXInterface)
        : IsaacBaseSensorComponent(debugDraw)
    {
        mPhysXInterface = PhysXInterface;
        mRawBuffer.resize(mRawBufferSize, IsRawData());

        reset();
    }

    virtual ~ImuSensor();

    void drawAxis(const usdrt::GfMatrix4d& usdTransform, const float& length);

    virtual void draw();

    size_t getNumReadings(); //<! Gets length of accumulated readings

    IsReading getSensorReadings(size_t& numReadings, const bool& readGravity = true); //<! Gets accumulated array of
                                                                                      // readings from last
                                                                                      // simulation step to current
                                                                                      // step.

    IsReading getSensorReading(const std::function<IsReading(std::vector<IsReading>, float)>& interpolateFunction = nullptr,
                               const bool& getLatestValue = false,
                               const bool& readGravity = true);

    IsReading getSimSensorReading(const bool& readGravity = true);

    void reset();
    // finite diff data in mRawReadingList, save in mReadingPair
    virtual void onPhysicsStep(); //<! Called by component manager tick

    virtual void tick()
    {
    }

    bool findValidParent();

    void onComponentChange();

    // the virtual onstop will clear everything on stop, the overloaded onstop will redraw the sensor after stop
    virtual void onStop();

    // internal debug function
    void printIsReading(const IsReading& reading);

private:
    IsProperties mProps;
    // sensor signal processing constant
    // size of raw data, must be larger than 2*mLinearAccelerationFilterSize
    int mRawBufferSize = 20;

    IsRawData mInitBuffer;
    std::vector<IsRawData> mRawBuffer; // raw velocities data array
    // moving average past n angular velocities
    int mAngularVelocityFilterSize = 1;
    // moving average past n finite diff acc
    int mLinearAccelerationFilterSize = 1;
    // moving average past n orientation values
    int mOrientationFilterSize = 1;

    // Data obtained at the last sensor period frame for intnerpolation
    std::vector<IsReading> mSensorReadingsSensorFrame; // IsReading at the measurement sensorperiod

    std::vector<IsReading> mSensorReadings; // Sensor readings in sensor timestamps
    double mUnitScale{ 1.0 };
    float mSensorTime{ 0 };
    bool mPreviousEnabled{ true };
    omni::math::linalg::vec3d mGravitySensorFrame;
    omni::math::linalg::vec3d mGravity;
    omni::physx::IPhysx* mPhysXInterface = nullptr;
};


}
}
}
