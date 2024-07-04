// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif
// clang-format off
#include <pch/UsdPCH.h>
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include "ContactSensor.h"

#include "../core/BaseSensorComponent.h"
#include "../core/BaseSensorManager.h"
#include "ContactManager.h"
#include "IsaacSensor.h"

#include <omni/isaac/utils/Pose.h>

namespace omni
{
namespace isaac
{
namespace sensor
{
ContactSensor::~ContactSensor()
{
    reset();
}

void ContactSensor::reset()
{
    mContactManagerPtr = nullptr;
    mCurrentTime = 0.0f;
    mSensorTime = 0.0f;
    mTimeSeconds = 0.0f;
    mTimeDelta = 0.0f;
    mReadingPair[0] = mReadingPair[1] = CsReading();
    mContactsRawData = nullptr;
}

CsRawData* ContactSensor::getRawData(size_t& size)
{
    CARB_LOG_WARN_ONCE("*** warning: get_contact_sensor_raw_data is deprecated and will replaced in the next release");

    if (mContactsRawData == nullptr)
    {
        size = 0;
    }
    else
    {
        size = 1;
    }
    return mContactsRawData;
}

CsReading ContactSensor::getSensorReading(const bool& getLatestValue)
{
    if (mProps.sensorPeriod > 0 && mProps.sensorPeriod < mTimeDelta && mTimeDelta - mProps.sensorPeriod > 0.001)
    {
        CARB_LOG_WARN_ONCE(
            "*** warning: contact sensor frequency is higher than physics frequency, returning the latest physics value");
    }

    CsReading sensorReading = CsReading();

    if (mEnabled)
    {
        // if sensor period is shorter than physics downtime, or user choose latest value return current value
        // or internal time + sensor period time is behind the last step time (something went wrong
        // i.e. sensor was disabled for a long time and then re-enabled)
        // get the latest time and measurement
        if (mProps.sensorPeriod <= mTimeDelta || mSensorTime + mProps.sensorPeriod < mReadingPair[!mCurrent].time ||
            getLatestValue)
        {
            sensorReading = mReadingPair[mCurrent];
            sensorReading.is_valid = true;
            if (mProps.sensorPeriod > 0 && mSensorTime + mProps.sensorPeriod < mReadingPair[!mCurrent].time)
            {
                CARB_LOG_WARN("*** warning Contact sensor time out of sync, using latest measurements");
            }
        }
        else
        {
            sensorReading = mSensorReading;
            sensorReading.is_valid = true;
        }
    }
    return sensorReading;
}

void ContactSensor::processRawContacts(CsRawData* rawContact, const size_t& size, const size_t& index, const double& time)
{
    CARB_PROFILE_ZONE(0, "Contact Sensor::processRawContacts");
    mReadingPair[index].value = 0.0f;
    mReadingPair[index].inContact = false;
    mReadingPair[index].time = static_cast<float>(time);
    if (rawContact == nullptr || rawContact->time == 0)
    {
        // CARB_LOG_INFO("Failed to process data, raw contact is null");
        return;
    }

    if (size > static_cast<size_t>(0))
    {
        usdrt::GfMatrix4d usdTransform =
            omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath());
        const double* sensor_pose = usdTransform.ExtractTranslation().GetArray();
        pxr::GfVec3d pose(sensor_pose[0], sensor_pose[1], sensor_pose[2]);
        pxr::GfVec3d totalImpulse(0.0, 0.0, 0.0);
        for (size_t i = 0; i < size; ++i)
        {
            pxr::GfVec3d contactPoint(rawContact[i].position.x, rawContact[i].position.y, rawContact[i].position.z);
            // CARB_LOG_WARN("contact Pose: %f %f %f", contactPoint[0], contactPoint[1], contactPoint[2]);
            // CARB_LOG_WARN("sensor Pose: %f %f %f", pose[0],pose[1], pose[2]);
            auto d = pxr::GfVec3d(0.0f); // dp*rawContact->dt; Pending update on physics contact position being delayed
                                         // a few frames dp is the linear vel of the parent
            auto distance = pose - contactPoint - d;
            // pose.GetLength(), mProps.radius);

            // Check if the distance from sensor to contact position is within sensor radius
            if (mProps.radius <= 0.0f || distance.GetLength() < static_cast<double>(mProps.radius))
            {
                mReadingPair[index].inContact = true;
                // compute force from impulse (F = i/dt) and add to sensor output
                totalImpulse += pxr::GfVec3d(static_cast<double>(rawContact[i].impulse.x),
                                             static_cast<double>(rawContact[i].impulse.y),
                                             static_cast<double>(rawContact[i].impulse.z));
                // CARB_LOG_WARN(
                //     "contact sensor value: %lu, %f, %lf", index, mReadingPair[index].value,
                //     pxr::GfVec3d(rawContact[i].impulse.x, rawContact[i].impulse.y,
                //     rawContact[i].impulse.z).GetLength());
            }
        }
        mReadingPair[index].value =
            std::min(static_cast<float>((totalImpulse.GetLength()) / rawContact[0].dt), mProps.maxThreshold);

        // if force reading is lower than the min threshold, override to no contact
        if (mReadingPair[index].value < mProps.minThreshold)
        {
            mReadingPair[index].value = 0;
            mReadingPair[index].inContact = false;
        }
    }
}

void ContactSensor::onPhysicsStep()
{
    CARB_PROFILE_ZONE(0, "ContactSensor::physics step");
    if (mContactManagerPtr == nullptr)
    {
        CARB_LOG_ERROR("*** error: ContactManager not found");
        return;
    }

    mContactsRawData = mContactManagerPtr->getCsRawData(asInt(mParentPrim.GetPath()), mSize);

    mCurrent = !mCurrent;
    processRawContacts(mContactsRawData, mSize, mCurrent, mTimeSeconds);

    // clear raw data if not in contact
    if (mReadingPair[mCurrent].inContact == false)
    {
        mContactsRawData = nullptr;
    }

    if (mProps.sensorPeriod <= mTimeDelta)
    {
        mSensorTime = mReadingPair[mCurrent].time;
    }
    else if (mSensorTime + mProps.sensorPeriod <= mReadingPair[mCurrent].time)
    {
        mSensorTime += mProps.sensorPeriod;
        // the sensor measurement is closer to current reading than the last reading
        if (abs(mReadingPair[mCurrent].time - mSensorTime) <= abs(mReadingPair[!mCurrent].time - mSensorTime))
        {
            mSensorReading = mReadingPair[mCurrent];
        }
        else
        {
            mSensorReading = mReadingPair[!mCurrent];
        }
        mSensorReading.time = mSensorTime;
    }
}

void ContactSensor::setContactReportApi()
{
    if (!mParentPrim.GetPrim().IsValid())
    {
        CARB_LOG_ERROR("*** error: failed to set Contact Report API, parent prim is invalid or not found");
        return;
    }

    pxr::PhysxSchemaPhysxContactReportAPI contactReportAPI =
        pxr::PhysxSchemaPhysxContactReportAPI::Get(mStage, mParentPrim.GetPath());

    if (!contactReportAPI)
    {
        CARB_LOG_ERROR(
            "*** error: %s parent prim is missing contact report API, automatically adding contact report API, stop and play the simulation for this change to take effect",
            this->mPrim.GetPath().GetString().c_str());
        contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Apply(mParentPrim.GetPrim());
    }
    if (!contactReportAPI.GetReportPairsRel())
    {
        contactReportAPI.CreateReportPairsRel();
    }
    contactReportAPI.GetThresholdAttr().Set(0.0f);

    pxr::PhysxSchemaPhysxRigidBodyAPI rigidBodyAPI =
        pxr::PhysxSchemaPhysxRigidBodyAPI::Get(mStage, mParentPrim.GetPath());

    if (rigidBodyAPI)
    {
        pxr::VtValue vtFloatValue(0);
        rigidBodyAPI.CreateSleepThresholdAttr(vtFloatValue);
    }
}

bool ContactSensor::findValidParent()
{
    pxr::UsdPrim tempPrim = this->mStage->GetPrimAtPath(this->mPrim.GetPath()).GetParent();
    while (tempPrim.IsValid() && tempPrim.GetName().GetString() != "/")
    {
        // check if it's a rigid body
        bool rigidBodyEnabled = false;
        tempPrim.GetAttribute(pxr::TfToken("physics:rigidBodyEnabled")).Get(&rigidBodyEnabled);
        if (rigidBodyEnabled)
        {
            mParentPrim = tempPrim;
            // findParentScale();
            setContactReportApi();
            return true;
        }
        // go to parent
        tempPrim = tempPrim.GetParent();
    }
    CARB_LOG_WARN("No valid parent for %s with a rigid body api was found, sensor will not be created",
                  this->mPrim.GetPath().GetString().c_str());
    return false;
}

void ContactSensor::onComponentChange()
{
    CARB_PROFILE_ZONE(0, "Contact Sensor - component change");
    IsaacSensorComponentBase::onComponentChange();
    float sensorPeriod = 0.0f;
    float radius = 0.0f;
    pxr::GfVec2f thresholdAttr = pxr::GfVec2f(0.01f, 100000.0f);

    // contact sensor onComponentChange
    const pxr::IsaacSensorIsaacContactSensor& typedPrim = (pxr::IsaacSensorIsaacContactSensor)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetThresholdAttr(), thresholdAttr);
    isaac::utils::safeGetAttribute(typedPrim.GetRadiusAttr(), radius);
    isaac::utils::safeGetAttribute(typedPrim.GetColorAttr(), mColor);
    isaac::utils::safeGetAttribute(typedPrim.GetSensorPeriodAttr(), sensorPeriod);

    setContactReportApi();
    const float* thresholds = thresholdAttr.GetArray();

    // contact sensor props
    mProps.maxThreshold = thresholds[1];
    mProps.minThreshold = thresholds[0];
    mProps.radius = radius;
    mProps.sensorPeriod = sensorPeriod;

    if (mPreviousEnabled != this->mEnabled)
    {
        if (mEnabled)
        {
            this->onPhysicsStep(); // force on physics step to run to get up to date value
            mReadingPair[!mCurrent] = mReadingPair[mCurrent]; // first step, copy latest values for both readingpairs
            mSensorTime = mReadingPair[mCurrent].time;
            mSensorReading = mReadingPair[mCurrent];
        }
        else
        {
            this->onStop();
        }
        mPreviousEnabled = this->mEnabled;
    }
}

void ContactSensor::onStop()
{
    mCurrentTime = 0.0f;
    mSensorTime = 0.0f;
    mTimeSeconds = 0.0f;
    mTimeDelta = 0.0f;
    mReadingPair[0] = mReadingPair[1] = CsReading();


    mContactsRawData = nullptr;
}

void ContactSensor::printRawData(CsRawData* data)
{
    if (data == nullptr)
    {
        CARB_LOG_WARN("Raw Data is NULL");
        return;
    }
    float time = data->time;

    uint64_t body0 = data->body0;
    uint64_t body1 = data->body1;

    float pos_x = data->position.x;
    float pos_y = data->position.y;
    float pos_z = data->position.z;

    float normal_x = data->normal.x;
    float normal_y = data->normal.y;
    float normal_z = data->normal.z;

    float impulse_x = data->impulse.x;
    float impulse_y = data->impulse.y;
    float impulse_z = data->impulse.z;

    CARB_LOG_INFO("Raw Data \n");
    CARB_LOG_INFO("Time: %f\n", time);
    CARB_LOG_INFO("Body 0: %s Body 1: %s \n", omni::isaac::utils::getSdfPathFromUint64(body0).GetString().c_str(),
                  omni::isaac::utils::getSdfPathFromUint64(body1).GetString().c_str());
    CARB_LOG_INFO("Position: %f, %f, %f \n", pos_x, pos_y, pos_z);
    CARB_LOG_INFO("Normal: %f, %f, %f \n", normal_x, normal_y, normal_z);
    CARB_LOG_INFO("Impulse: %f, %f, %f \n", impulse_x, impulse_y, impulse_z);
}

void ContactSensor::printReadingPair()
{
    CsReading reading0 = mReadingPair[0];
    float value0 = reading0.value;
    float time0 = reading0.time;

    CsReading reading1 = mReadingPair[1];
    float value1 = reading1.value;
    float time1 = reading1.time;

    CARB_LOG_INFO("Reading Pair\n");
    CARB_LOG_INFO("Reading 0: value: %f, time: %f \n", value0, time0);
    CARB_LOG_INFO("Reading 1: value: %f, time: %f \n", value1, time1);
}


}
}
}
#ifdef _WIN32
#    pragma warning(pop)
#endif
