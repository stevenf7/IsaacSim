// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <omni/isaac/contact_sensor/ContactSensor.h>
#include <omni/physx/IPhysx.h>

#include <map>
#include <memory>
#include <vector>

namespace omni
{
namespace isaac
{
namespace contact_sensor
{

class ContactSensor
{
public:
    ContactSensor()
    {
    }
    ContactSensor(pxr::TfToken body);

    void initialize(CsProperties props);
    void reset();
    // void processRawContact(CsRawData rawData);
    void processRawContacts(CsRawData* rawData, const size_t& size);
    void update(float time); //<! Called on physics step by contact manager to update
    // internal readings

    size_t getNumReadings(); //<! Gets length of accumulated readings
    CsReading* getSensorReadings(size_t& num_readings); //<! Gets accumulated array of readings from last
                                                        // simulation step to current
                                                        // simulation step.
    inline CsReading getSimReading()
    {
        return mReadingPair[mCurrent];
    }

    inline pxr::TfToken getBody()
    {
        return bodyID;
    }

    inline bool processedRaw()
    {
        return mProcessedRaw;
    }
    inline void clearRawProcessFlag()
    {
        mProcessedRaw = false;
    }

private:
    pxr::TfToken bodyID;
    CsProperties mProps;
    CsReading mReadingPair[2]; // Data obtained on simulation timestamp
    std::vector<CsReading> mSensorReadings; // Sensor readings in sensor timestamps
    bool mCurrent{ 0 };
    float mCurrentTime;
    bool mProcessedReadings{ false };
    bool mProcessedRaw{ false };
};

struct ContactPair
{
    pxr::TfToken body0;
    pxr::TfToken body1;

    ContactPair(pxr::TfToken b0, pxr::TfToken b1) : body0(b0), body1(b1)
    {
        // keep body zero always the token with the smaller value
        if (b0 > b1)
        {
            body0 = b1;
            body1 = b0;
        }
    }
    ContactPair(pxr::SdfPath b0, pxr::SdfPath b1) : ContactPair(b0.GetToken(), b1.GetToken())
    {
    }
    ContactPair(CsRawData d) : ContactPair(pxr::SdfPath(d.body0), pxr::SdfPath(d.body1))
    {
    }


    bool operator==(ContactPair rhs) const
    {
        return body0 == rhs.body0 && body1 == rhs.body1;
    }
};
class ContactManager
{
public:
    ContactManager(omni::physx::IPhysx* physxInterface);
    void unSubscribeEvents(omni::physx::IPhysx* physxInterface);
    void onPhysicsStep(float timeElapsed); // to be called on a physics step to update time
    void resetSensors();
    void onContactReport(carb::events::IEvent* e);

    CsHandle addSensor(const char* usdPath, CsProperties props);
    CsHandle* getSensorsOnBody(const char* usdPath, size_t& num_sensors);
    bool removeSensor(CsHandle sensor);
    void removeAllSensorsFromBody(const char* usdPath);

    CsReading* getSensorReadings(CsHandle sensor, size_t& num_readings);
    CsReading getSensorSimReading(CsHandle sensor);
    CsRawData* getCsRawData(const char* usdPath, size_t& size);
    void removeRawData(const ContactPair p);
    void clearAllSensors();


private:
    CsRawData* getCsRawData(const pxr::TfToken token, size_t& size);
    std::map<pxr::TfToken, std::vector<CsHandle>> mPrimSensorMap;
    std::map<CsHandle, ContactSensor> mSensorHandleMap;
    std::vector<CsRawData> mContactRaw;
    std::map<pxr::TfToken, std::vector<CsRawData>> mContactRawMap; // Contacts filtered by each object (used for
                                                                   // object raw data)
    float mCurrentTime{ 0.0f };
    size_t mContactsToProcess{ 0 };
    size_t mContactsProcessed{ 0 };
    uint32_t mNextId{ 0 };
    bool mSensorsProcessed{ false };

    omni::physx::SubscriptionId mStepSubscription;
    omni::physx::SubscriptionId mEventSubscription;

    carb::events::ISubscriptionPtr mContactCallbackPtr;
};
}
}
}
