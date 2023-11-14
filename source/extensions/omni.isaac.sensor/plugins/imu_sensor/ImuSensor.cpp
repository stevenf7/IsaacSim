// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
#include <omni/usd/UtilsIncludes.h>
// clang-format on

#include "ImuSensor.h"

#include "omni/isaac/sensor/IsaacSensor.h"
#include "omni/isaac/utils/Pose.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Log.h>

#include <omni/isaac/math/core/quat.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxSceneQuery.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>
#include <physicsSchemaTools/UsdTools.h>
#include <pxr/usd/usdPhysics/scene.h>

#include <PxActor.h>


#if defined(_WIN32)
#    include <PxArticulationLink.h>
#else
#    pragma GCC diagnostic push
#    pragma GCC diagnostic ignored "-Wpragmas"
#    include <PxArticulationLink.h>
#    pragma GCC diagnostic pop
#endif

#include <PxRigidDynamic.h>
#include <PxScene.h>
#include <map>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace sensor
{
ImuSensor::~ImuSensor()
{
    reset();
    mRawBuffer.clear();
    mSensorReadings.clear();
    mSensorReadingsSensorFrame.clear();
}

void ImuSensor::drawAxis(const usdrt::GfMatrix4d& usdTransform, const float& length)
{
    omni::math::linalg::vec3d position = usdTransform.ExtractTranslation();

    // TransformDir for a 4x4 matrix multiplies the rotation matrix part by a vector
    omni::math::linalg::vec3d xtransform =
        usdTransform.TransformDir(omni::math::linalg::vec3d(static_cast<double>(length), 0.0, 0.0));
    omni::math::linalg::vec3d ytransform =
        usdTransform.TransformDir(omni::math::linalg::vec3d(0.0, static_cast<double>(length), 0.0));
    omni::math::linalg::vec3d ztransform =
        usdTransform.TransformDir(omni::math::linalg::vec3d(0.0, 0.0, static_cast<double>(length)));

    xtransform += position;
    ytransform += position;
    ztransform += position;

    // draw the axis in global frame
    carb::scenerenderer::PrimitiveVertex center;
    center.position.x = static_cast<float>(position.GetArray()[0]);
    center.position.y = static_cast<float>(position.GetArray()[1]);
    center.position.z = static_cast<float>(position.GetArray()[2]);
    center.width = length * 0.5f;

    // x axis - red
    center.color = carb::ColorRgba{ 1.0f, 0.0f, 0.0f, 1.0f };
    carb::scenerenderer::PrimitiveVertex x_axis;
    x_axis.position =
        carb::Float3{ static_cast<float>(xtransform.GetArray()[0]), static_cast<float>(xtransform.GetArray()[1]),
                      static_cast<float>(xtransform.GetArray()[2]) };
    x_axis.width = center.width;
    x_axis.color = center.color;
    mLineDrawing->addVertex(center);
    mLineDrawing->addVertex(x_axis);

    // y axis - green
    center.color = carb::ColorRgba{ 0.0f, 1.0f, 0.0f, 1.0f };
    carb::scenerenderer::PrimitiveVertex y_axis;
    y_axis.position =
        carb::Float3{ static_cast<float>(ytransform.GetArray()[0]), static_cast<float>(ytransform.GetArray()[1]),
                      static_cast<float>(ytransform.GetArray()[2]) };
    y_axis.width = center.width;
    y_axis.color = center.color;
    mLineDrawing->addVertex(center);
    mLineDrawing->addVertex(y_axis);

    // z axis - blue
    center.color = carb::ColorRgba{ 0.0f, 0.0f, 1.0f, 1.0f };
    carb::scenerenderer::PrimitiveVertex z_axis;
    z_axis.position =
        carb::Float3{ static_cast<float>(ztransform.GetArray()[0]), static_cast<float>(ztransform.GetArray()[1]),
                      static_cast<float>(ztransform.GetArray()[2]) };
    z_axis.width = center.width;
    z_axis.color = center.color;
    mLineDrawing->addVertex(center);
    mLineDrawing->addVertex(z_axis);

    mLineDrawing->draw();
    return;
}

void ImuSensor::draw()
{
    usdrt::GfMatrix4d usdTransform =
        omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath());
    usdTransform.Orthonormalize();

    // 0.5/unit scale means 0.5 meter or 50cm
    drawAxis(usdTransform, static_cast<float>(0.5f / mUnitScale));

    return;
}

size_t ImuSensor::getNumReadings()
{
    CARB_LOG_WARN_ONCE(
        "*** Deprecation alert: IMU getNumReadings function is deprecated and will be removed in the next update");
    CARB_LOG_WARN_ONCE("*** the return value will always be 0 or 1");

    size_t size = 0;
    if (getSensorReading().is_valid)
    {
        size = 1;
    }
    return size;
}

IsReading ImuSensor::getSensorReadings(size_t& numReadings, const bool& readGravity)
{
    CARB_LOG_WARN_ONCE(
        "*** Deprecation alert: IMU getSensorReadings function is deprecated and will be removed in the next update");
    CARB_LOG_WARN_ONCE("*** please use getSensorReading for sensor readings");

    if (mProps.sensorPeriod < mTimeDelta && mProps.sensorPeriod > 0 && mTimeDelta - mProps.sensorPeriod > 0.001)
    {
        CARB_LOG_WARN_ONCE(
            "*** warning: IMU sensor frequency is higher than physics frequency, returning the latest physics value");
    }

    IsReading reading = getSensorReading(nullptr, false, readGravity);

    if (reading.is_valid)
    {
        numReadings = 1;
    }
    else
    {
        numReadings = 0;
    }

    return reading;
}

IsReading ImuSensor::getSensorReading(const std::function<IsReading(std::vector<IsReading>, float)>& interpolateFunction,
                                      const bool& getLatestValue,
                                      const bool& readGravity)
{
    if (mProps.sensorPeriod > 0 && mProps.sensorPeriod < mTimeDelta && mTimeDelta - mProps.sensorPeriod > 0.001)
    {
        CARB_LOG_WARN_ONCE(
            "*** warning: IMU sensor frequency is higher than physics frequency, returning the latest physics value");
    }

    IsReading sensorReading = IsReading();

    if (mEnabled)
    {
        // if sensor period is shorter than physics downtime, or user choose latest value return current value
        // or internal time + sensor period time is behind the last step time, then something went wrong
        // i.e. sensor was disabled for a long time and then re-enabled
        // get the latest time and measurement
        if (mProps.sensorPeriod <= mTimeDelta || mSensorTime + mProps.sensorPeriod < mSensorReadings[1].time ||
            getLatestValue)
        {
            sensorReading = mSensorReadings[0];
            sensorReading.is_valid = true;
            if (mProps.sensorPeriod > 0 && mSensorTime + mProps.sensorPeriod < mSensorReadings[1].time)
            {
                CARB_LOG_WARN("*** warning IMU sensor time out of sync, using latest measurements");
            }
        }
        else
        {
            sensorReading.time = mSensorTime;
            sensorReading.is_valid = true;
            float time_ratio = 1;

            if (mSensorReadingsSensorFrame[1].time != mSensorReadingsSensorFrame[0].time)
            {
                time_ratio = (mSensorTime - mSensorReadingsSensorFrame[1].time) /
                             (mSensorReadingsSensorFrame[0].time - mSensorReadingsSensorFrame[1].time);
            }
            else
            {
                time_ratio = (mSensorTime - mSensorReadingsSensorFrame[1].time) / static_cast<float>(mTimeDelta);
            }
            // user didn't pass in a interpolation function
            if (!interpolateFunction)
            {
                sensorReading.lin_acc_x =
                    lerp(mSensorReadingsSensorFrame[1].lin_acc_x, mSensorReadingsSensorFrame[0].lin_acc_x, time_ratio);
                sensorReading.lin_acc_y =
                    lerp(mSensorReadingsSensorFrame[1].lin_acc_y, mSensorReadingsSensorFrame[0].lin_acc_y, time_ratio);
                sensorReading.lin_acc_z =
                    lerp(mSensorReadingsSensorFrame[1].lin_acc_z, mSensorReadingsSensorFrame[0].lin_acc_z, time_ratio);

                sensorReading.ang_vel_x =
                    lerp(mSensorReadingsSensorFrame[1].ang_vel_x, mSensorReadingsSensorFrame[0].ang_vel_x, time_ratio);
                sensorReading.ang_vel_y =
                    lerp(mSensorReadingsSensorFrame[1].ang_vel_y, mSensorReadingsSensorFrame[0].ang_vel_y, time_ratio);
                sensorReading.ang_vel_z =
                    lerp(mSensorReadingsSensorFrame[1].ang_vel_z, mSensorReadingsSensorFrame[0].ang_vel_z, time_ratio);

                sensorReading.orientation.w = lerp(mSensorReadingsSensorFrame[1].orientation.w,
                                                   mSensorReadingsSensorFrame[0].orientation.w, time_ratio);
                sensorReading.orientation.x = lerp(mSensorReadingsSensorFrame[1].orientation.x,
                                                   mSensorReadingsSensorFrame[0].orientation.x, time_ratio);
                sensorReading.orientation.y = lerp(mSensorReadingsSensorFrame[1].orientation.y,
                                                   mSensorReadingsSensorFrame[0].orientation.y, time_ratio);
                sensorReading.orientation.z = lerp(mSensorReadingsSensorFrame[1].orientation.z,
                                                   mSensorReadingsSensorFrame[0].orientation.z, time_ratio);
            }
            // use user's interpolation function
            else
            {
                sensorReading = interpolateFunction(mSensorReadingsSensorFrame, mSensorTime);
            }
        }

        if (readGravity)
        {
            sensorReading.lin_acc_x += static_cast<float>(mGravitySensorFrame[0]);
            sensorReading.lin_acc_y += static_cast<float>(mGravitySensorFrame[1]);
            sensorReading.lin_acc_z += static_cast<float>(mGravitySensorFrame[2]);
        }
    }
    return sensorReading;
}

IsReading ImuSensor::getSimSensorReading(const bool& readGravity)
{
    CARB_LOG_WARN_ONCE(
        "*** Deprecation alert: IMU getSensorSimReading function is deprecated and will be removed in the next update");
    CARB_LOG_WARN_ONCE("*** please use getSensorReading for sensor reading");
    if (mProps.sensorPeriod > 0 && mProps.sensorPeriod < mTimeDelta && mTimeDelta - mProps.sensorPeriod > 0.001)
    {
        CARB_LOG_WARN_ONCE(
            "*** warning: IMU sensor frequency is higher than physics frequency, returning the latest physics value");
    }
    return getSensorReading(nullptr, true, readGravity);
}

void ImuSensor::reset()
{
    mRawBuffer.resize(mRawBufferSize, IsRawData());

    mSensorReadings.resize(mRawBufferSize, IsReading());
    mSensorReadingsSensorFrame.resize(mRawBufferSize, IsReading());
    mSensorTime = 0;
}

void ImuSensor::onPhysicsStep()
{
    mLineDrawing->clear();
    // CARB_LOG_INFO("Sensor Update %f", mTimeSeconds);

    pxr::SdfPath actor(mParentPrim.GetPath());

    ::physx::PxRigidBody* rigid = nullptr;
    // follow logics are from source/extensions/omni.isaac.dynamic_control/plugins/DcPhysx.cpp
    ::physx::PxActor* pxActor = (::physx::PxActor*)mPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTActor);
    if (pxActor)
    {
        ::physx::PxActorType::Enum type = pxActor->getType();
        if (type == ::physx::PxActorType::eRIGID_DYNAMIC /*|| type == PxActorType::eARTICULATION_LINK*/)
        {
            rigid = static_cast<::physx::PxRigidBody*>(pxActor);
        }
    }
    else
    {
        ::physx::PxArticulationLink* link =
            (::physx::PxArticulationLink*)mPhysXInterface->getPhysXPtr(actor, omni::physx::PhysXType::ePTLink);
        if (link)
        {
            rigid = static_cast<::physx::PxRigidBody*>(link);
        }
    }

    // only when rigid is valid can we start to generate sensor data
    if (rigid)
    {
        // both velocities are in world frame, need to convert them to sensor frame
        ::physx::PxVec3 ang_vel = rigid->getAngularVelocity();
        ::physx::PxVec3 lin_vel = rigid->getLinearVelocity();

        // v_w linear velocity in world frame
        // w_w angular velocity in world frame
        omni::math::linalg::vec3d w_w = omni::math::linalg::vec3d(ang_vel.x, ang_vel.y, ang_vel.z);
        omni::math::linalg::vec3d v_w = omni::math::linalg::vec3d(lin_vel.x, lin_vel.y, lin_vel.z);

        // Get transformation matrix from body to world
        usdrt::GfMatrix4d R_bw =
            omni::isaac::utils::pose::computeWorldXformNoCache(mStage, mUsdrtStage, mPrim.GetPath()).GetOrthonormalized();

        // Inverse to get transformation matrix from world to body
        usdrt::GfMatrix4d R_wb = R_bw.GetInverse();

        // sensor orientation in world frame
        usdrt::GfMatrix3d R_w = mProps.orientation * R_bw.ExtractRotationMatrix();
        omni::math::linalg::quatd q_wb = R_w.ExtractRotation();

        // velocity of sensor frame in sensor frame
        omni::math::linalg::vec3d v_b = R_wb.TransformDir(v_w);

        // angular velocity of sensor frame in sensor frame
        omni::math::linalg::vec3d w_b = R_wb.TransformDir(w_w);

        // gravity that the IMU experience in sensor frame
        mGravitySensorFrame = R_wb.TransformDir(mGravity);

        // we then finite diff v_b to get a_b, to reduce noise, average multiple finite diffs
        // save raw data into a buffer list , buffer 0 always saves the latest velocities
        if (!mRawBuffer.empty())
        {
            mRawBuffer.pop_back();
        }

        const double* imaginary = q_wb.GetImaginary().GetArray();

        // read in new data
        mRawBuffer.insert(mRawBuffer.begin(), IsRawData());
        mRawBuffer[0].time = static_cast<float>(mTimeSeconds);
        mRawBuffer[0].dt = static_cast<float>(mTimeDelta);
        mRawBuffer[0].lin_vel_x = static_cast<float>(v_b[0]);
        mRawBuffer[0].lin_vel_y = static_cast<float>(v_b[1]);
        mRawBuffer[0].lin_vel_z = static_cast<float>(v_b[2]);
        mRawBuffer[0].ang_vel_x = static_cast<float>(w_b[0]);
        mRawBuffer[0].ang_vel_y = static_cast<float>(w_b[1]);
        mRawBuffer[0].ang_vel_z = static_cast<float>(w_b[2]);
        mRawBuffer[0].orientation.w = static_cast<float>(q_wb.GetReal());
        mRawBuffer[0].orientation.x = static_cast<float>(imaginary[0]);
        mRawBuffer[0].orientation.y = static_cast<float>(imaginary[1]);
        mRawBuffer[0].orientation.z = static_cast<float>(imaginary[2]);

        if (!mSensorReadings.empty())
        {
            mSensorReadings.pop_back();
        }
        mSensorReadings.insert(mSensorReadings.begin(), IsReading());

        // signal processing
        mSensorReadings[0].time = static_cast<float>(mTimeSeconds);
        // ang_vel output strategy: average past mAngularVelocityFilterSize timesteps
        float tmp_sum_x = 0, tmp_sum_y = 0, tmp_sum_z = 0;
        for (int i = 0; i < mAngularVelocityFilterSize; i++)
        {
            tmp_sum_x += mRawBuffer[i].ang_vel_x;
            tmp_sum_y += mRawBuffer[i].ang_vel_y;
            tmp_sum_z += mRawBuffer[i].ang_vel_z;
        }
        mSensorReadings[0].ang_vel_x = static_cast<float>(tmp_sum_x / mAngularVelocityFilterSize);
        mSensorReadings[0].ang_vel_y = static_cast<float>(tmp_sum_y / mAngularVelocityFilterSize);
        mSensorReadings[0].ang_vel_z = static_cast<float>(tmp_sum_z / mAngularVelocityFilterSize);

        // lin acc output strategy: average mLinearAccelerationFilterSize finite diffs
        // say if mLinearAccelerationFilterSize = 2, we do (([0] - [2]) / (2dt) + ([1] - [3]) / (2dt))/2
        tmp_sum_x = 0.0f;
        tmp_sum_y = 0.0f;
        tmp_sum_z = 0.0f;
        for (int i = 0; i < mLinearAccelerationFilterSize; i++)
        {
            float dt = mRawBuffer[i].time - mRawBuffer[i + mLinearAccelerationFilterSize].time;

            if (dt > 1e-10)
            {
                tmp_sum_x += (mRawBuffer[i].lin_vel_x - mRawBuffer[i + mLinearAccelerationFilterSize].lin_vel_x) / dt;
                tmp_sum_y += (mRawBuffer[i].lin_vel_y - mRawBuffer[i + mLinearAccelerationFilterSize].lin_vel_y) / dt;
                tmp_sum_z += (mRawBuffer[i].lin_vel_z - mRawBuffer[i + mLinearAccelerationFilterSize].lin_vel_z) / dt;
            }
        }


        // average acc
        mSensorReadings[0].lin_acc_x = static_cast<float>(tmp_sum_x / mLinearAccelerationFilterSize);
        mSensorReadings[0].lin_acc_y = static_cast<float>(tmp_sum_y / mLinearAccelerationFilterSize);
        mSensorReadings[0].lin_acc_z = static_cast<float>(tmp_sum_z / mLinearAccelerationFilterSize);

        // // add gravity
        // mSensorReadings[0].lin_acc_x += static_cast<float>(g_b[0]);
        // mSensorReadings[0].lin_acc_y += static_cast<float>(g_b[1]);
        // mSensorReadings[0].lin_acc_z += static_cast<float>(g_b[2]);

        // Log raw buffer:
        // CARB_LOG_INFO("mRawBuffer [%f, %f, %f, %f, %f, %f, %f, %f, %f, %f]", mRawBuffer[0].lin_vel_x,
        //               mRawBuffer[1].lin_vel_x, mRawBuffer[2].lin_vel_x, mRawBuffer[3].lin_vel_x,
        //               mRawBuffer[4].lin_vel_x, mRawBuffer[5].lin_vel_x, mRawBuffer[6].lin_vel_x,
        //               mRawBuffer[7].lin_vel_x, mRawBuffer[8].lin_vel_x, mRawBuffer[9].lin_vel_x);

        float tmp_sum_w = 0.0;
        tmp_sum_x = 0.0f;
        tmp_sum_y = 0.0f;
        tmp_sum_z = 0.0f;

        for (int i = 0; i < mOrientationFilterSize; i++)
        {
            tmp_sum_w += mRawBuffer[i].orientation.w;
            tmp_sum_x += mRawBuffer[i].orientation.x;
            tmp_sum_y += mRawBuffer[i].orientation.y;
            tmp_sum_z += mRawBuffer[i].orientation.z;
        }

        mSensorReadings[0].orientation.w = static_cast<float>(tmp_sum_w / mOrientationFilterSize);
        mSensorReadings[0].orientation.x = static_cast<float>(tmp_sum_x / mOrientationFilterSize);
        mSensorReadings[0].orientation.y = static_cast<float>(tmp_sum_y / mOrientationFilterSize);
        mSensorReadings[0].orientation.z = static_cast<float>(tmp_sum_z / mOrientationFilterSize);

        // Print out reading pair:
        // CARB_LOG_INFO("mReadingPair[0]: [(%f, %f, %f), (%f, %f, %f), (%f, %f, %f, %f)]", mReadingPair[0].lin_acc_x,
        //               mReadingPair[0].lin_acc_y, mReadingPair[0].lin_acc_z, mReadingPair[0].ang_vel_x,
        //               mReadingPair[0].ang_vel_y, mReadingPair[0].ang_vel_z, mReadingPair[0].orientation.w,
        //               mReadingPair[0].orientation.x, mReadingPair[0].orientation.y, mReadingPair[0].orientation.z);
        // CARB_LOG_INFO("mReadingPair[1]: [(%f, %f, %f), (%f, %f, %f), (%f, %f, %f, %f)]", mReadingPair[1].lin_acc_x,
        //               mReadingPair[1].lin_acc_y, mReadingPair[1].lin_acc_z, mReadingPair[1].ang_vel_x,
        //               mReadingPair[1].ang_vel_y, mReadingPair[1].ang_vel_z, mReadingPair[1].orientation.w,
        //               mReadingPair[1].orientation.x, mReadingPair[1].orientation.y, mReadingPair[1].orientation.z);
        if (mProps.sensorPeriod <= mTimeDelta)
        {
            mSensorTime = mSensorReadings[0].time;
        }
        else if (mSensorTime + mProps.sensorPeriod <= mSensorReadings[0].time)
        {
            mSensorTime += mProps.sensorPeriod;
            mSensorReadingsSensorFrame = mSensorReadings;
        }
    }
}

bool ImuSensor::findValidParent()
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
            return true;
        }
        // go to parent
        tempPrim = tempPrim.GetParent();
    }
    CARB_LOG_ERROR("*** error: Parent prim is not found or is invalid");
    return false;
}

void ImuSensor::onComponentChange()
{
    IsaacSensorComponentBase::onComponentChange();


    // get orientation quad sensor period, and translate

    const pxr::IsaacSensorIsaacImuSensor& typedPrim = (pxr::IsaacSensorIsaacImuSensor)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetSensorPeriodAttr(), this->mProps.sensorPeriod);
    isaac::utils::safeGetAttribute(typedPrim.GetLinearAccelerationFilterWidthAttr(), this->mLinearAccelerationFilterSize);
    isaac::utils::safeGetAttribute(typedPrim.GetAngularVelocityFilterWidthAttr(), this->mAngularVelocityFilterSize);
    isaac::utils::safeGetAttribute(typedPrim.GetOrientationFilterWidthAttr(), this->mOrientationFilterSize);

    // reject 0 or negative rolling avg size
    mLinearAccelerationFilterSize = std::max(mLinearAccelerationFilterSize, 1);
    mAngularVelocityFilterSize = std::max(mAngularVelocityFilterSize, 1);
    mOrientationFilterSize = std::max(mOrientationFilterSize, 1);

    int max_rolling_size =
        std::max(std::max(mLinearAccelerationFilterSize, mAngularVelocityFilterSize), mOrientationFilterSize);

    // size of the raw data must be 2 times larger than the max rolling avg size
    // also the buffer should be sufficiently large (20)
    if (this->mRawBufferSize != 2 * max_rolling_size)
    {
        this->mRawBufferSize = std::max(2 * max_rolling_size, 20);
        mRawBuffer.resize(mRawBufferSize, IsRawData());
        mSensorReadings.resize(mRawBufferSize, IsReading());
    }
    pxr::GfQuatd sensor_quat(0.0);
    mPrim.GetPrim().GetAttribute(pxr::TfToken("xformOp:orient")).Get(&sensor_quat);
    sensor_quat.Normalize();

    pxr::GfVec3d position(0.0);
    mPrim.GetPrim().GetAttribute(pxr::TfToken("xformOp:translate")).Get(&position);


    omni::math::linalg::quatd rotate(
        sensor_quat.GetReal(),
        omni::math::linalg::vec3d(sensor_quat.GetImaginary().GetArray()[0], sensor_quat.GetImaginary().GetArray()[1],
                                  sensor_quat.GetImaginary().GetArray()[2]));

    mProps.orientation.SetRotate(rotate);

    findValidParent();

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    // gravity that the IMU experiences in world frame
    omni::math::linalg::vec3d dir = omni::math::linalg::vec3d(0, 0, -1.0f);
    float mag = 9.80665f;
    mGravity = mag / mUnitScale * -dir;
    // If a scene exists we try reading gravity from it
    pxr::UsdPrimRange range = mStage->Traverse();
    omni::physx::IPhysx* physxPtr = carb::getCachedInterface<omni::physx::IPhysx>();

    for (pxr::UsdPrimRange::iterator iter = range.begin(); iter != range.end(); ++iter)
    {
        pxr::UsdPrim prim = *iter;

        if (prim.IsA<pxr::UsdPhysicsScene>())
        {
            pxr::UsdPhysicsScene scene(prim);
            // Try to get the actual physics scene's gravity vector
            ::physx::PxScene* physxScenePtr = static_cast<::physx::PxScene*>(
                physxPtr->getPhysXPtr(prim.GetPrimPath(), omni::physx::PhysXType::ePTScene));

            if (physxScenePtr)
            {
                ::physx::PxVec3 gravity = physxScenePtr->getGravity();
                mGravity = -omni::math::linalg::vec3d(gravity.x, gravity.y, gravity.z) / mUnitScale;
            }
            else
            {
                // Fallback onto USD values
                isaac::utils::safeGetAttribute(scene.GetGravityMagnitudeAttr(), mag);
                pxr::GfVec3f dir_attr;
                isaac::utils::safeGetAttribute(scene.GetGravityDirectionAttr(), dir_attr); // (0, 0, -1.0f)

                dir.Set(static_cast<double>(dir_attr.GetArray()[0]), static_cast<double>(dir_attr.GetArray()[1]),
                        static_cast<double>(dir_attr.GetArray()[2]));
                mGravity = static_cast<double>(mag) / mUnitScale * -dir;
            }
        }
    }

    if (mPreviousEnabled != this->mEnabled)
    {
        if (mEnabled)
        {
            this->onPhysicsStep(); // force on physics step to run to get up to date value
            mSensorTime = static_cast<float>(mTimeSeconds);
            mRawBuffer.resize(mRawBufferSize, IsRawData());
            mSensorReadings.resize(mRawBufferSize, IsReading());
            mSensorReadingsSensorFrame = mSensorReadings;
        }
        else
        {
            this->onStop();
        }
        mPreviousEnabled = this->mEnabled;
    }

    if (mVisualize && mEnabled)
    {
        CARB_LOG_WARN_ONCE("*** Deprecation Alert: visualization through prim will be removed in the next release!");
        CARB_LOG_WARN_ONCE(" please use axis visualization node in Omnigraph to visualize this");
        draw();
    }
}

void ImuSensor::onStop()
{
    reset();

    mLineDrawing->clear();
    if (mVisualize)
    {
        draw();
    }
}

void ImuSensor::printIsReading(const IsReading& reading)
{
    CARB_LOG_INFO("Is Reading");
    CARB_LOG_INFO("time: %f", reading.time);
    CARB_LOG_INFO("ang vel x: %f", reading.ang_vel_x);
    CARB_LOG_INFO("ang vel y: %f", reading.ang_vel_y);
    CARB_LOG_INFO("ang vel z: %f", reading.ang_vel_z);

    CARB_LOG_INFO("lin accel x: %f", reading.lin_acc_x);
    CARB_LOG_INFO("lin accel y: %f", reading.lin_acc_y);
    CARB_LOG_INFO("lin accel z: %f", reading.lin_acc_z);
    CARB_LOG_INFO("orientation xyzw: (%f, %f, %f, %f)", reading.orientation.x, reading.orientation.y,
                  reading.orientation.z, reading.orientation.w);
}

}
}
}
#ifdef _WIN32
#    pragma warning(pop)
#endif
