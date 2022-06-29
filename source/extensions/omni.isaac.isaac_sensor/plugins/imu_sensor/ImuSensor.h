// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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
#include <omni/isaac/isaac_sensor/IsaacSensor.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>

#include <map>
#include <memory>
#include <vector>

namespace omni
{
namespace isaac
{
namespace isaac_sensor
{

class ImuSensor : public IsaacBaseSensorComponent
{
public:
    ImuSensor(omni::renderer::IDebugDraw* debugDraw, omni::physx::IPhysx* PhysXInterface)
        : IsaacBaseSensorComponent(debugDraw)
    {
        mPhysXInterface = PhysXInterface;
        reset();
    }

    virtual ~ImuSensor();

    void drawAxis(const pxr::GfVec3d& _position, const pxr::GfRotation& _orientation, const float& length);

    virtual void draw();

    size_t getNumReadings(); //<! Gets length of accumulated readings

    IsReading* getSensorReadings(size_t& num_readings); //<! Gets accumulated array of readings from last
                                                        // simulation step to current step.

    IsReading getSimSensorReading();

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
    void printIsReading(IsReading reading);

private:
    IsProperties mProps;
    // sensor signal processing constant
    // size of raw data, must be larger than 2*LIN_ACC_AVERAGE_NUM
    const static int RAW_BUFFER_SIZE = 10;

    IsRawData mInitBuffer;
    IsRawData mRawBuffer[RAW_BUFFER_SIZE]; // raw velocities data
    // moving average past n angular velocities
    const static int ANG_VEL_AVERAGE_NUM = 1;
    // moving average past n finite diff acc
    const static int LIN_ACC_AVERAGE_NUM = 2;
    // moving average past n orientation values
    const static int ORIENT_AVERAGE_NUM = 1;

    IsReading mInitPair; // Data obtained on simulation timestamp
    IsReading mReadingPair[2]; // Data obtained on simulation timestamp
    std::vector<IsReading> mSensorReadings; // Sensor readings in sensor timestamps
    double mUnitScale{ 1.0 };
    bool mCurrent{ 0 };
    float mCurrentTime;
    bool mProcessedReadings{ false };
    bool mProcessedRaw{ false };
    bool mFirst{ true };
    pxr::GfVec3d mGravity;
    omni::physx::IPhysx* mPhysXInterface = nullptr;
};


}
}
}
