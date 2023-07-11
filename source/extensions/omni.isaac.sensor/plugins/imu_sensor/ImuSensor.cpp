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
}

void ImuSensor::drawAxis(const pxr::GfVec3d& _position, const pxr::GfRotation& _orientation, const float& length)
{
    pxr::GfVec3d xtransform = _orientation.TransformDir(pxr::GfVec3d(static_cast<double>(length), 0.0, 0.0));
    pxr::GfVec3d ytransform = _orientation.TransformDir(pxr::GfVec3d(0.0, static_cast<double>(length), 0.0));
    pxr::GfVec3d ztransform = _orientation.TransformDir(pxr::GfVec3d(0.0, 0.0, static_cast<double>(length)));

    xtransform += _position;
    ytransform += _position;
    ztransform += _position;

    // draw the axis in global frame
    carb::scenerenderer::PrimitiveVertex center;
    center.position.x = static_cast<float>(_position.GetArray()[0]);
    center.position.y = static_cast<float>(_position.GetArray()[1]);
    center.position.z = static_cast<float>(_position.GetArray()[2]);
    center.width = length * 0.1f;

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
    pxr::GfMatrix4d usdTransform = omni::usd::UsdUtils::getWorldTransformMatrix(mPrim.GetPrim());
    pxr::GfVec3d translation = usdTransform.ExtractTranslation();
    usdTransform.Orthonormalize();
    pxr::GfRotation rotation = usdTransform.ExtractRotation();

    // 0.5/unit scale means 0.5 meter or 50cm
    drawAxis(pxr::GfVec3f(translation), rotation, static_cast<float>(0.5f / mUnitScale));

    return;
}

size_t ImuSensor::getNumReadings()
{
    if (!mProcessedReadings)
    {
        size_t size;
        getSensorReadings(size);
    }
    return mSensorReadings.size();
}

IsReading* ImuSensor::getSensorReadings(size_t& num_readings)
{
    if (mProps.sensorPeriod > 0)
    {
        if (!mProcessedReadings)
        {
            float start = mReadingPair[!mCurrent].time;

            // Add a tolerance to the end time to be 1/10th of sensorperiod, to avoid duplicate data near the end
            float end = mReadingPair[mCurrent].time - mProps.sensorPeriod / 10;

            // will return the data from the last physics dt update. This is to keep the getSensorReadings function
            // consistent with the contact sensor
            mCurrentTime = start;
            mSensorReadings.clear();

            // when sensorPeriod is much shorter than simulation dt, more than 1 readings are returned
            while (mCurrentTime < end)
            {
                float time_pos = (mCurrentTime - start) / (end - start);
                IsReading reading;
                reading.time = mCurrentTime;
                reading.lin_acc_x = lerp(mReadingPair[!mCurrent].lin_acc_x, mReadingPair[mCurrent].lin_acc_x, time_pos);
                reading.lin_acc_y = lerp(mReadingPair[!mCurrent].lin_acc_y, mReadingPair[mCurrent].lin_acc_y, time_pos);
                reading.lin_acc_z = lerp(mReadingPair[!mCurrent].lin_acc_z, mReadingPair[mCurrent].lin_acc_z, time_pos);

                reading.ang_vel_x = lerp(mReadingPair[!mCurrent].ang_vel_x, mReadingPair[mCurrent].ang_vel_x, time_pos);
                reading.ang_vel_y = lerp(mReadingPair[!mCurrent].ang_vel_y, mReadingPair[mCurrent].ang_vel_y, time_pos);
                reading.ang_vel_z = lerp(mReadingPair[!mCurrent].ang_vel_z, mReadingPair[mCurrent].ang_vel_z, time_pos);

                reading.orientation.w =
                    lerp(mReadingPair[!mCurrent].orientation.w, mReadingPair[mCurrent].orientation.w, time_pos);
                reading.orientation.x =
                    lerp(mReadingPair[!mCurrent].orientation.x, mReadingPair[mCurrent].orientation.x, time_pos);
                reading.orientation.y =
                    lerp(mReadingPair[!mCurrent].orientation.y, mReadingPair[mCurrent].orientation.y, time_pos);
                reading.orientation.z =
                    lerp(mReadingPair[!mCurrent].orientation.z, mReadingPair[mCurrent].orientation.z, time_pos);

                mSensorReadings.push_back(reading);
                mCurrentTime += mProps.sensorPeriod;
            }
            mProcessedReadings = true;
        }
    }
    else
    {
        mSensorReadings.clear();
        mSensorReadings.push_back(mReadingPair[mCurrent]);
    }
    num_readings = mSensorReadings.size();
    // INFO_LOG_INFO("Num Readings :%ld", num_readings);
    return mSensorReadings.data();
}

IsReading ImuSensor::getSimSensorReading()
{
    return mReadingPair[mCurrent];
}

void ImuSensor::reset()
{
    mCurrentTime = 0.0f;
    mCurrent = 0;

    mRawBuffer.resize(mRawBufferSize, IsRawData());

    mReadingPair[0] = mReadingPair[1] = IsReading();
    mProcessedReadings = false;
    mSensorReadings.clear();
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


        /*  *transform velocities in the rigid body frame to that in the sensor frame according to mProps*
         *  notation used here follows book "Modern Robotics" (Kevin Lynch)
         *  we denote world frame as w, body frame as a, sensor frame as b
         *  R_ab rotates a vector in frame b into frame a
         *  R_ab and q_ab are the same rotation, R is the rotation matrix while q is the quaternion
         *  we use T_wa to represent R_wa, p_wa together in a 4x4 homogeneous matrix
         *
         *  p_wb represents the position of b in frame w
         *  for example, p_wa is the global position of frame a,
         *  and p_ab is the transformation from body frame to sensor frame
         *
         *  so the global position of sensor frame is p_wb = p_wa + Rwa*p_ab
         *  global rotation of sensor frame is R_wb = R_wa*R_ab
         *  velocities of body frame in world frame are w_wa(w) and v_wa(v)
         *  velocity of sensor frame in world frame: v_wb = v_wa + R_wa*skew(w_a)*p_ab = v + skew(w)*R_wa*p_ab
         *
         *  finally, velocity of sensor frame in sensor frame  v_b = R_wb^T*v_wb
         *  w_b is the body angular velocity of frame b in frame b, w_b = R_wb^T*w_wa
         */
        pxr::GfVec3d w(
            static_cast<double>(ang_vel.x), static_cast<double>(ang_vel.y), static_cast<double>(ang_vel.z)); // w_wa
        pxr::GfVec3d v(
            static_cast<double>(lin_vel.x), static_cast<double>(lin_vel.y), static_cast<double>(lin_vel.z)); // v_wa

        ::physx::PxTransform T_wa = rigid->getGlobalPose();

        pxr::GfVec3d p_wa(static_cast<double>(T_wa.p.x), static_cast<double>(T_wa.p.y), static_cast<double>(T_wa.p.z));

        pxr::GfRotation R_wa(pxr::GfQuatd(
            static_cast<double>(T_wa.q.w),
            pxr::GfVec3d(static_cast<double>(T_wa.q.x), static_cast<double>(T_wa.q.y), static_cast<double>(T_wa.q.z))));

        pxr::GfVec3d p_ab(static_cast<double>(mProps.position.x), static_cast<double>(mProps.position.y),
                          static_cast<double>(mProps.position.z));
        pxr::GfQuatd q_ab(
            static_cast<double>(mProps.orientation.w),
            pxr::GfVec3d(static_cast<double>(mProps.orientation.x), static_cast<double>(mProps.orientation.y),
                         static_cast<double>(mProps.orientation.z)));


        pxr::GfRotation R_ab(q_ab);
        pxr::GfRotation R_wb = R_wa * R_ab;
        pxr::GfVec3d p_wab = R_wa.TransformDir(p_ab);
        // velocity of sensor frame in world frame
        pxr::GfVec3d v_wb =
            v + pxr::GfMatrix3d(0.0, -w[2], w[1], w[2], 0.0, -w[0], -w[1], w[0], 0.0) * p_wab; // convert w to
                                                                                               // a
                                                                                               // skew-symmetric
                                                                                               // form
        // velocity of sensor frame in sensor frame
        pxr::GfVec3d v_b = R_wb.GetInverse().TransformDir(v_wb);
        // angular velocity of sensor frame in sensor frame
        pxr::GfVec3d w_b = R_wb.GetInverse().TransformDir(w);


        // gravity that the IMU experience in sensor frame
        pxr::GfVec3d g_b = R_wb.GetInverse().TransformDir(mGravity);

        // we then finite diff v_b to get a_b, to reduce noise, average multiple finite diffs
        // save raw data into a buffer list , buffer 0 always saves the latest velocities

        for (int i = mRawBufferSize - 1; i > 0; i--)
        {
            mRawBuffer[i].time = mRawBuffer[i - 1].time;
            mRawBuffer[i].dt = mRawBuffer[i - 1].dt;
            mRawBuffer[i].lin_vel_x = mRawBuffer[i - 1].lin_vel_x;
            mRawBuffer[i].lin_vel_y = mRawBuffer[i - 1].lin_vel_y;
            mRawBuffer[i].lin_vel_z = mRawBuffer[i - 1].lin_vel_z;
            mRawBuffer[i].ang_vel_x = mRawBuffer[i - 1].ang_vel_x;
            mRawBuffer[i].ang_vel_y = mRawBuffer[i - 1].ang_vel_y;
            mRawBuffer[i].ang_vel_z = mRawBuffer[i - 1].ang_vel_z;

            mRawBuffer[i].orientation.w = mRawBuffer[i - 1].orientation.w;
            mRawBuffer[i].orientation.x = mRawBuffer[i - 1].orientation.x;
            mRawBuffer[i].orientation.y = mRawBuffer[i - 1].orientation.y;
            mRawBuffer[i].orientation.z = mRawBuffer[i - 1].orientation.z;
        }

        // read in new data
        mRawBuffer[0] = IsRawData();
        mRawBuffer[0].time = static_cast<float>(mTimeSeconds);
        mRawBuffer[0].dt = static_cast<float>(mTimeDelta);
        mRawBuffer[0].lin_vel_x = static_cast<float>(v_b[0]);
        mRawBuffer[0].lin_vel_y = static_cast<float>(v_b[1]);
        mRawBuffer[0].lin_vel_z = static_cast<float>(v_b[2]);
        mRawBuffer[0].ang_vel_x = static_cast<float>(w_b[0]);
        mRawBuffer[0].ang_vel_y = static_cast<float>(w_b[1]);
        mRawBuffer[0].ang_vel_z = static_cast<float>(w_b[2]);
        mRawBuffer[0].orientation.w = static_cast<float>(T_wa.q.w);
        mRawBuffer[0].orientation.x = static_cast<float>(T_wa.q.x);
        mRawBuffer[0].orientation.y = static_cast<float>(T_wa.q.y);
        mRawBuffer[0].orientation.z = static_cast<float>(T_wa.q.z);

        // signal processing
        mCurrent ^= 1;
        mReadingPair[mCurrent].time = static_cast<float>(mTimeSeconds);
        // ang_vel output strategy: average past mAngularVelocityFilterSize timesteps
        float tmp_sum_x = 0, tmp_sum_y = 0, tmp_sum_z = 0;
        for (int i = 0; i < mAngularVelocityFilterSize; i++)
        {
            tmp_sum_x += mRawBuffer[i].ang_vel_x;
            tmp_sum_y += mRawBuffer[i].ang_vel_y;
            tmp_sum_z += mRawBuffer[i].ang_vel_z;
        }
        mReadingPair[mCurrent].ang_vel_x = static_cast<float>(tmp_sum_x / mAngularVelocityFilterSize);
        mReadingPair[mCurrent].ang_vel_y = static_cast<float>(tmp_sum_y / mAngularVelocityFilterSize);
        mReadingPair[mCurrent].ang_vel_z = static_cast<float>(tmp_sum_z / mAngularVelocityFilterSize);

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
        mReadingPair[mCurrent].lin_acc_x = static_cast<float>(tmp_sum_x / mLinearAccelerationFilterSize);
        mReadingPair[mCurrent].lin_acc_y = static_cast<float>(tmp_sum_y / mLinearAccelerationFilterSize);
        mReadingPair[mCurrent].lin_acc_z = static_cast<float>(tmp_sum_z / mLinearAccelerationFilterSize);
        // add gravity
        mReadingPair[mCurrent].lin_acc_x += static_cast<float>(g_b[0]);
        mReadingPair[mCurrent].lin_acc_y += static_cast<float>(g_b[1]);
        mReadingPair[mCurrent].lin_acc_z += static_cast<float>(g_b[2]);

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

        mReadingPair[mCurrent].orientation.w = static_cast<float>(tmp_sum_w / mOrientationFilterSize);
        mReadingPair[mCurrent].orientation.x = static_cast<float>(tmp_sum_x / mOrientationFilterSize);
        mReadingPair[mCurrent].orientation.y = static_cast<float>(tmp_sum_y / mOrientationFilterSize);
        mReadingPair[mCurrent].orientation.z = static_cast<float>(tmp_sum_z / mOrientationFilterSize);

        // Print out reading pair:
        // CARB_LOG_INFO("mReadingPair[0]: [(%f, %f, %f), (%f, %f, %f), (%f, %f, %f, %f)]", mReadingPair[0].lin_acc_x,
        //               mReadingPair[0].lin_acc_y, mReadingPair[0].lin_acc_z, mReadingPair[0].ang_vel_x,
        //               mReadingPair[0].ang_vel_y, mReadingPair[0].ang_vel_z, mReadingPair[0].orientation.w,
        //               mReadingPair[0].orientation.x, mReadingPair[0].orientation.y, mReadingPair[0].orientation.z);
        // CARB_LOG_INFO("mReadingPair[1]: [(%f, %f, %f), (%f, %f, %f), (%f, %f, %f, %f)]", mReadingPair[1].lin_acc_x,
        //               mReadingPair[1].lin_acc_y, mReadingPair[1].lin_acc_z, mReadingPair[1].ang_vel_x,
        //               mReadingPair[1].ang_vel_y, mReadingPair[1].ang_vel_z, mReadingPair[1].orientation.w,
        //               mReadingPair[1].orientation.x, mReadingPair[1].orientation.y, mReadingPair[1].orientation.z);

        if (mFirst)
        {
            mInitPair.lin_acc_x = mReadingPair[mCurrent].lin_acc_x;
            mInitPair.lin_acc_y = mReadingPair[mCurrent].lin_acc_y;
            mInitPair.lin_acc_z = mReadingPair[mCurrent].lin_acc_z;

            mInitPair.ang_vel_x = mReadingPair[mCurrent].ang_vel_x;
            mInitPair.ang_vel_y = mReadingPair[mCurrent].ang_vel_y;
            mInitPair.ang_vel_z = mReadingPair[mCurrent].ang_vel_z;

            mInitPair.orientation.w = mReadingPair[mCurrent].orientation.w;
            mInitPair.orientation.x = mReadingPair[mCurrent].orientation.x;
            mInitPair.orientation.y = mReadingPair[mCurrent].orientation.y;
            mInitPair.orientation.z = mReadingPair[mCurrent].orientation.z;

            mFirst = false;
        }

        mProcessedReadings = false;
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
    CARB_LOG_ERROR("Error, Parent prim is not found or is invalid");
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
    if (this->mRawBufferSize < 2 * max_rolling_size && max_rolling_size > 10)
    {
        this->mRawBufferSize = 2 * max_rolling_size;
    }

    mRawBuffer.resize(mRawBufferSize, IsRawData());

    pxr::GfVec3d position(0.0);
    mPrim.GetPrim().GetAttribute(pxr::TfToken("xformOp:translate")).Get(&position);
    mProps.position = omni::isaac::utils::conversions::asCarbFloat3(position);

    pxr::GfQuatd orientation(0.0);
    mPrim.GetPrim().GetAttribute(pxr::TfToken("xformOp:orient")).Get(&orientation);
    double real = orientation.GetReal();
    const double* imaginary = orientation.GetImaginary().GetArray();

    mProps.orientation.w = static_cast<float>(real);
    mProps.orientation.x = static_cast<float>(imaginary[0]);
    mProps.orientation.y = static_cast<float>(imaginary[1]);
    mProps.orientation.z = static_cast<float>(imaginary[2]);

    findValidParent();

    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    // gravity that the IMU experiences in world frame
    pxr::GfVec3f dir = pxr::GfVec3f(0, 0, -1.0f);
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
                mGravity = -pxr::GfVec3f(gravity.x, gravity.y, gravity.z) / mUnitScale;
            }
            else
            {
                // Fallback onto USD values
                isaac::utils::safeGetAttribute(scene.GetGravityMagnitudeAttr(), mag);
                isaac::utils::safeGetAttribute(scene.GetGravityDirectionAttr(), dir);
                mGravity = mag / mUnitScale * -dir;
            }
        }
    }

    if (mVisualize)
    {
        draw();
    }
}

void ImuSensor::onStop()
{

    // reset output reading buffer to match initial value
    mReadingPair[mCurrent].lin_acc_x = mInitPair.lin_acc_x;
    mReadingPair[mCurrent].lin_acc_y = mInitPair.lin_acc_y;
    mReadingPair[mCurrent].lin_acc_z = mInitPair.lin_acc_z;

    mReadingPair[mCurrent].ang_vel_x = mInitPair.ang_vel_x;
    mReadingPair[mCurrent].ang_vel_y = mInitPair.ang_vel_y;
    mReadingPair[mCurrent].ang_vel_z = mInitPair.ang_vel_z;

    mReadingPair[mCurrent].orientation.w = mInitPair.orientation.w;
    mReadingPair[mCurrent].orientation.x = mInitPair.orientation.x;
    mReadingPair[mCurrent].orientation.y = mInitPair.orientation.y;
    mReadingPair[mCurrent].orientation.z = mInitPair.orientation.z;

    mReadingPair[!mCurrent] = IsReading();

    mRawBuffer.resize(mRawBufferSize, IsRawData());

    mFirst = true;

    mLineDrawing->clear();
    mPointDrawing->clear();
    if (mVisualize)
    {
        draw();
    }
}

void ImuSensor::printIsReading(IsReading reading)
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
