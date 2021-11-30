// Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/isaac/imu_sensor/IMUSensor.h>
#include <omni/physx/IPhysx.h>

#include <map>
#include <memory>
#include <vector>

namespace omni
{
namespace isaac
{
namespace imu_sensor
{

class IMUSensor
{
public:
    IMUSensor()
    {
    }
    IMUSensor(pxr::TfToken body);

    void initialize(IsProperties props);
    void reset();
    // finite diff data in mRawReadingList, save in mReadingPair
    void update(float time, float dt); //<! Called on physics step by contact manager to update
    // internal readings

    size_t getNumReadings(); //<! Gets length of accumulated readings
    IsReading* getSensorReadings(size_t& num_readings); //<! Gets accumulated array of readings from last
                                                        // simulation step to current
                                                        // simulation step.
    inline IsReading getSimReading()
    {
        return mReadingPair[mCurrent];
    }

    inline pxr::TfToken getBody()
    {
        return bodyID;
    }


private:
    pxr::TfToken bodyID;
    IsProperties mProps;
    // sensor signal processing constant
    // size of raw data, must larger than 2*LIN_ACC_AVERAGE_NUM
    const static int RAW_BUFFER_SIZE = 10;
    IsRawData mRawBuffer[RAW_BUFFER_SIZE]; // raw velocities data
    // moving average past n angular velocities
    const static int ANG_VEL_AVERAGE_NUM = 1;
    // moving average past n finite diff acc
    const static int LIN_ACC_AVERAGE_NUM = 2;
    IsReading mReadingPair[2]; // Data obtained on simulation timestamp
    std::vector<IsReading> mSensorReadings; // Sensor readings in sensor timestamps
    bool mCurrent{ 0 };
    float mCurrentTime;
    bool mProcessedReadings{ false };
    bool mProcessedRaw{ false };
    pxr::GfVec3d mGravity;
};

class IMUManager
{
public:
    IMUManager(omni::physx::IPhysx* physxInterface);
    void unSubscribeEvents(omni::physx::IPhysx* physxInterface);
    void onPhysicsStep(float timeElapsed); // to be called on a physics step to update time
    void resetSensors();

    IsHandle addSensor(const char* usdPath, IsProperties props);
    IsHandle* getSensorsOnBody(const char* usdPath, size_t& num_sensors);
    bool removeSensor(IsHandle sensor);
    void removeAllSensorsFromBody(const char* usdPath);

    IsReading* getSensorReadings(IsHandle sensor, size_t& num_readings);
    IsReading getSensorSimReading(IsHandle sensor);
    void clearAllSensors();


private:
    std::map<pxr::TfToken, std::vector<IsHandle>> mPrimSensorMap;
    std::map<IsHandle, IMUSensor> mSensorHandleMap;
    float mCurrentTime{ 0.0f };
    float mCurrentDt{ 0.0f };
    uint32_t mNextId{ 0 };

    omni::physx::SubscriptionId mStepSubscription;
    omni::physx::SubscriptionId mEventSubscription;
};
}
}
}
