// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include "ContactSensor.h"

#include "../core/BaseSensorComponent.h"
#include "../core/BaseSensorManager.h"
#include "ContactManager.h"
#include "omni/isaac/isaac_sensor/IsaacSensor.h"


namespace omni
{
namespace isaac
{
namespace isaac_sensor
{
ContactSensor::~ContactSensor()
{
    reset();
}

void ContactSensor::reset()
{
    mContactManagerPtr = nullptr;
    mCurrentTime = 0.0f;
    mTimeSeconds = 0.0f;
    mTimeDelta = 0.0f;
    mReadingPair[0] = mReadingPair[1] = CsReading();
    mSensorReadings.clear();
    mContacts = nullptr;
}

void ContactSensor::drawCircle(const pxr::GfVec3d& _pose, const int& nsegment)
{
    // will not visualize if the visualize flag is off or if radius is <=0 (full body sensor)
    if (!mVisualize || mProp.radius <= 0)
    {
        return;
    }

    float step = static_cast<float>(2 * PI / nsegment);
    float angle = 0.0f;

    const double* pose = _pose.GetArray();
    float x = static_cast<float>(pose[0]);
    float y = static_cast<float>(pose[1]);
    float z = static_cast<float>(pose[2]);

    // CARB_LOG_WARN("Draw for pose (%f %f %f)", x, y, z);
    const float* color = mColor.GetArray();
    carb::scenerenderer::PrimitiveVertex data;

    for (int i = 0; i < nsegment; i++, angle += step)
    {
        data.position.x = mProp.radius * cos(angle) + x;
        data.position.y = mProp.radius * sin(angle) + y;
        data.position.z = z;

        data.color = carb::ColorRgba{ color[0], color[1], color[2], color[3] };
        data.width = 0.1f;
        mLineDrawing->addVertex(data);
    }
    angle = 0.0f;

    for (int i = 0; i < nsegment; i++, angle += step)
    {
        data.position.x = x;
        data.position.y = mProp.radius * cos(angle) + y;
        data.position.z = mProp.radius * sin(angle) + z;

        data.color = carb::ColorRgba{ color[0], color[1], color[2], color[3] };
        data.width = 0.1f;

        mLineDrawing->addVertex(data);
    }
    angle = 0.0f;

    for (int i = 0; i < nsegment; i++, angle += step)
    {
        data.position.x = mProp.radius * cos(angle) + x;
        data.position.y = y;
        data.position.z = mProp.radius * sin(angle) + z;

        data.color = carb::ColorRgba{ color[0], color[1], color[2], color[3] };
        data.width = 0.1f;

        mLineDrawing->addVertex(data);
    }

    mLineDrawing->draw();
}

void ContactSensor::draw()
{
    pxr::GfMatrix4d usdTransform = omni::usd::UsdUtils::getWorldTransformMatrix(mPrim.GetPrim());
    pxr::GfVec3d translation = usdTransform.ExtractTranslation();
    drawCircle(translation, 96);
}

CsRawData* ContactSensor::getRawData(size_t& size)
{
    size = mSize;
    return mContacts;
}

CsReading ContactSensor::getSimSensorReading()
{
    size_t index = 1;
    processRawContacts(mContacts, mSize, index, mTimeSeconds);
    return mReadingPair[index];
}

CsReading* ContactSensor::getSensorReadings(size_t& num_readings)
{
    CARB_PROFILE_ZONE(0, "ContactSensor::getSensorReadings");
    // when mContactsOld's time is 0, then it's the first frame and we return 0.
    if (mContacts == nullptr || mContactsOld.time == 0)
    {
        mSensorReadings.clear();
        mReadingPair[1].time = mContactManagerPtr->getCurrentTime();
        mSensorReadings.push_back(mReadingPair[1]);
        // CARB_LOG_WARN("mSensorReadings.size(): %zu", mSensorReadings.size());
        num_readings = 1;
        return mSensorReadings.data();
    }
    // store processed old data to index 0
    double delTime = (mTimeSeconds - mTimeDelta < 0) ? 0.0 : mTimeSeconds - mTimeDelta;
    processRawContacts(&mContactsOld, mSizeOld, 0, delTime);

    // store processed new data to index 1
    processRawContacts(mContacts, mSize, 1, mTimeSeconds);

    if (mProp.sensorPeriod > 0)
    {
        float start = mReadingPair[0].time;
        float end = mReadingPair[1].time;
        mSensorReadings.clear();

        while (mCurrentTime < end)
        {
            if (mCurrentTime >= start)
            {
                float time_pos = (mCurrentTime - start) / (end - start);
                CsReading reading;
                reading.time = mCurrentTime;
                reading.value = lerp(mReadingPair[0].value, mReadingPair[1].value, time_pos);
                if (reading.value < mProp.minThreshold)
                {
                    reading.value = 0.0f;
                }
                reading.inContact = reading.value > 0.0f;
                mSensorReadings.push_back(reading);
            }
            mCurrentTime += mProp.sensorPeriod;
        }
    }
    else
    {
        mSensorReadings.clear();
        mSensorReadings.push_back(mReadingPair[1]);
        if (mSensorReadings.back().value < mProp.minThreshold)
        {
            mSensorReadings.back().value = 0.0f;
            mSensorReadings.back().inContact = false;
        }
    }
    num_readings = mSensorReadings.size();
    // CARB_LOG_INFO("normal mSensorReadings.size(): %zu", num_readings);
    return mSensorReadings.data();
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

        uint64_t actor = rawContact[0].body0;
        if (rawContact[0].body0 != asInt(mParentPrim.GetPath())) // If Parent is on index 1
            actor = rawContact[0].body1;
        pxr::SdfPath actorPath(reinterpret_cast<const pxr::SdfPath&>(actor));
        // CARB_LOG_INFO("getting PxActor");
        pxr::GfTransform parentPose;
        pxr::GfVec3d pose(static_cast<double>(mProp.position.x), static_cast<double>(mProp.position.y),
                          static_cast<double>(mProp.position.z));
        ::physx::PxActor* pxActor =
            (::physx::PxActor*)mPhysXInterfacePtr->getPhysXPtr(actorPath, omni::physx::PhysXType::ePTActor);
        // CARB_LOG_INFO("used Physx interface");
        pxr::GfVec3d dp;
        if (pxActor)
        {
            // CARB_LOG_INFO("Found PxActor");
            ::physx::PxRigidDynamic* rd = (::physx::PxRigidDynamic*)pxActor;
            ::physx::PxTransform _pose = rd->getGlobalPose();
            auto gv = (rd->getLinearVelocity());
            dp = pxr::GfVec3d(static_cast<double>(gv.x), static_cast<double>(gv.y), static_cast<double>(gv.z));
            parentPose.SetTranslation(pxr::GfVec3d(
                static_cast<double>(_pose.p.x), static_cast<double>(_pose.p.y), static_cast<double>(_pose.p.z)));
            parentPose.SetRotation(
                pxr::GfRotation(pxr::GfQuatd(static_cast<double>(_pose.q.w),
                                             pxr::GfVec3d(static_cast<double>(_pose.q.x), static_cast<double>(_pose.q.y),
                                                          static_cast<double>(_pose.q.z)))));
        }
        else
        {
            // CARB_LOG_WARN("PxLink");
            ::physx::PxArticulationLink* link = (::physx::PxArticulationLink*)mPhysXInterfacePtr->getPhysXPtr(
                actorPath, omni::physx::PhysXType::ePTLink);
            ::physx::PxTransform _pose = link->getGlobalPose();
            auto gv = link->getLinearVelocity();
            dp = pxr::GfVec3d(static_cast<double>(gv.x), static_cast<double>(gv.y), static_cast<double>(gv.z));


            parentPose.SetTranslation(pxr::GfVec3d(
                static_cast<double>(_pose.p.x), static_cast<double>(_pose.p.y), static_cast<double>(_pose.p.z)));
            parentPose.SetRotation(
                pxr::GfRotation(pxr::GfQuatd(static_cast<double>(_pose.q.w),
                                             pxr::GfVec3d(static_cast<double>(_pose.q.x), static_cast<double>(_pose.q.y),
                                                          static_cast<double>(_pose.q.z)))));
        }

        pose = parentPose.GetMatrix().Transform(pose);
        pxr::GfVec3d totalImpulse(0.0, 0.0, 0.0);
        for (size_t i = 0; i < size; ++i)
        {
            pxr::GfVec3d contactPoint(rawContact[i].position.x, rawContact[i].position.y, rawContact[i].position.z);
            // CARB_LOG_WARN("contact Pose: %f %f %f", contactPoint[0], contactPoint[1], contactPoint[2]);
            // CARB_LOG_WARN("sensor Pose: %f %f %f", pose[0],pose[1], pose[2]);
            auto d = pxr::GfVec3d(0.0f); // dp*rawContact->dt; Pending update on physics contact position being delayed
                                         // a few frames
            auto distance = pose - contactPoint - d;
            // pose.GetLength(), mProp.radius);

            // Check if the distance from sensor to contact position is within sensor radius
            if (mProp.radius < 0.0f || distance.GetLength() < static_cast<double>(mProp.radius))
            {
                mReadingPair[index].inContact = mReadingPair[index].inContact || true;
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
            std::min(static_cast<float>((totalImpulse.GetLength()) / rawContact[0].dt), mProp.maxThreshold);
    }
}

void ContactSensor::onPhysicsStep()
{
    CARB_PROFILE_ZONE(0, "ContactSensor::physics step");
    mPointDrawing->clear();
    mLineDrawing->clear();
    if (mContactManagerPtr == nullptr)
    {
        CARB_LOG_ERROR("ContactManager not found");
        return;
    }
    if (mContacts != nullptr)
    {
        mContactsOld = CsRawData(*mContacts); // update mContactsOld with the mContacts from the previous step if
                                              // mContacts is not null
    }
    mSizeOld = mSize;

    mContacts = mContactManagerPtr->getCsRawData(asInt(mParentPrim.GetPath()), mSize);
    return;
}

void ContactSensor::setContactReportApi()
{
    if (!mParentPrim.GetPrim().IsValid())
    {
        CARB_LOG_ERROR("failed to set Contact Report API, parent prim is invalid or not found");
        return;
    }

    pxr::PhysxSchemaPhysxContactReportAPI contactReportAPI =
        pxr::PhysxSchemaPhysxContactReportAPI::Get(mStage, mParentPrim.GetPath());

    if (!contactReportAPI)
    {
        contactReportAPI = pxr::PhysxSchemaPhysxContactReportAPI::Apply(mParentPrim.GetPrim());
    }
    if (!contactReportAPI.GetThresholdAttr())
    {
        contactReportAPI.CreateThresholdAttr();
    }
    if (!contactReportAPI.GetReportPairsRel())
    {
        contactReportAPI.CreateReportPairsRel();
    }

    const pxr::IsaacSensorSchemaIsaacContactSensor& typedPrim = (pxr::IsaacSensorSchemaIsaacContactSensor)mPrim;

    pxr::GfVec2f thresholdAttr = pxr::GfVec2f(0.01f, 100000.0f);
    isaac::utils::safeGetAttribute(typedPrim.GetThresholdAttr(), thresholdAttr);
    const float* thresholds = thresholdAttr.GetArray();
    contactReportAPI.GetThresholdAttr().Set(thresholds[0]);
}

pxr::GfVec3d ContactSensor::findParentScale()
{
    if (!mParentPrim.IsValid())
    {
        CARB_LOG_ERROR("Failed to find parent scale, Parent Prim is invalid or not found");
    }
    pxr::UsdPrim tempPrim = mPrim.GetPrim();
    pxr::GfVec3d tempScale(1);
    pxr::GfVec3d zeroScale(0);
    std::vector<pxr::GfVec3d> parentScales;

    while (tempPrim.IsValid() && tempPrim.GetName().GetString() != "/")
    {
        tempPrim.GetAttribute(pxr::TfToken("xformOp:scale")).Get(&tempScale);
        tempPrim = tempPrim.GetParent();
        parentScales.push_back(tempScale);
    }

    double x_scale = 1;
    double y_scale = 1;
    double z_scale = 1;

    for (unsigned int i = 0; i < parentScales.size(); i++)
    {
        const double* scale = parentScales[i].GetArray();
        if (scale[0] > 0 && scale[1] > 0 && scale[2] > 0)
        {
            x_scale *= scale[0];
            y_scale *= scale[1];
            z_scale *= scale[2];
        }
    }
    tempScale.Set(x_scale, y_scale, z_scale);
    return tempScale;
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
            findParentScale();
            setContactReportApi();
            return true;
        }
        // go to parent
        tempPrim = tempPrim.GetParent();
    }
    CARB_LOG_ERROR("Error, Parent prim is not found or is invalid");
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
    const pxr::IsaacSensorSchemaIsaacContactSensor& typedPrim = (pxr::IsaacSensorSchemaIsaacContactSensor)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetThresholdAttr(), thresholdAttr);
    isaac::utils::safeGetAttribute(typedPrim.GetRadiusAttr(), radius);
    isaac::utils::safeGetAttribute(typedPrim.GetColorAttr(), mColor);
    isaac::utils::safeGetAttribute(typedPrim.GetSensorPeriodAttr(), sensorPeriod);

    pxr::GfVec3d position(0.0);
    mPrim.GetPrim().GetAttribute(pxr::TfToken("xformOp:translate")).Get(&position);

    pxr::GfVec3d parentScale = findParentScale();
    setContactReportApi();
    const double* pos = position.GetArray();
    const double* scale = parentScale.GetArray();
    const float* thresholds = thresholdAttr.GetArray();

    // contact sensor props
    mProp.maxThreshold = thresholds[1];
    mProp.minThreshold = thresholds[0];
    mProp.radius = radius;
    mProp.sensorPeriod = sensorPeriod;

    carb::Float3 mPropPos = { static_cast<float>(pos[0] * scale[0]), static_cast<float>(pos[1] * scale[1]),
                              static_cast<float>(pos[2] * scale[2]) };
    mProp.position = mPropPos;

    // CARB_LOG_WARN("relative position (stage unit): %f %f %f", mProp.position.x, mProp.position.y,
    // mProp.position.z);
    if (mVisualize)
    {
        draw();
    }
}

void ContactSensor::onStop()
{
    mLineDrawing->clear();
    mPointDrawing->clear();
    mCurrentTime = 0.0f;
    mReadingPair[0] = mReadingPair[1] = CsReading();
    mSensorReadings.clear();
    mContacts = nullptr;
    if (mVisualize)
    {
        draw();
    }
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
    CARB_LOG_INFO("Body 0: %s Body 1: %s \n", reinterpret_cast<const pxr::SdfPath&>(body0).GetString().c_str(),
                  reinterpret_cast<const pxr::SdfPath&>(body1).GetString().c_str());
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
