// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include "RosDifferentialBase.h"

#include "geometry_msgs/Twist.h"
#include "nav_msgs/Odometry.h"

#include <carb/Framework.h>

#include <omni/isaac/ros/Utils.h>
#include <omni/isaac/utils/Conversions.h>

namespace omni
{
namespace isaac
{
using utils::conversions::asGfRotation;
using utils::conversions::asGfVec3d;
namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosDifferentialBase::RosDifferentialBase(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

RosDifferentialBase::~RosDifferentialBase()
{
    CARB_LOG_INFO("RosDifferentialBase Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mStatePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mTfPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCommandSubTopic);
}

void RosDifferentialBase::initialize(RosNode* rosNode,
                                     const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                                     pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosDifferentialBase::onStart()
{
    mZUp = UsdGeomGetStageUpAxis(mStage) == "Z" ? true : false;
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
    onComponentChange();
    // get starting pose in the world frame
    startingPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
}
void RosDifferentialBase::onStop()
{
}
void RosDifferentialBase::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosDifferentialBase& typedPrim = (pxr::RosBridgeSchemaRosDifferentialBase)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mStatePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mTfPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mCommandSubTopic);

    isaac::utils::safeGetAttribute(typedPrim.GetStatePubTopicAttr(), mStatePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetCommandSubTopicAttr(), mCommandSubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);
    isaac::utils::safeGetAttribute(typedPrim.GetOdomFrameIdAttr(), mOdomFrameId);
    isaac::utils::safeGetAttribute(typedPrim.GetBaseFrameIdAttr(), mBaseFrameId);

    ros_utils::addPrefix(mRosNodePrefix, mOdomFrameId, false);
    ros_utils::addPrefix(mRosNodePrefix, mBaseFrameId, false);
    ros_utils::addPrefix(mRosNodePrefix, mStatePubTopic, true);
    ros_utils::addPrefix(mRosNodePrefix, mCommandSubTopic, true);

    mRosNode->createPublisher<nav_msgs::Odometry>(
        mPrim.GetPath().GetString(), mStatePubTopic, mQueueSize, &RosDifferentialBase::pubCallback, this);
    mRosNode->createPublisher<tf2_msgs::TFMessage>(
        mPrim.GetPath().GetString(), mTfPubTopic, mQueueSize, &RosDifferentialBase::tfPubCallback, this);
    mRosNode->createSubscriber<geometry_msgs::Twist>(
        mPrim.GetPath().GetString(), mCommandSubTopic, mQueueSize, &RosDifferentialBase::subCallback, this);

    // Parse parameters

    isaac::utils::safeGetAttribute(typedPrim.GetRobotFrontAttr(), mRobotFront);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxSpeedAttr(), mMaximumSpeed);
    isaac::utils::safeGetAttribute(typedPrim.GetMaxTimeWithoutCommandAttr(), mMaximumTimeWithoutCommand);
    isaac::utils::safeGetAttribute(typedPrim.GetAccelerationSmoothingAttr(), mAccelerationSmoothing);
    isaac::utils::safeGetAttribute(typedPrim.GetWheelRadiusAttr(), mWheelRadius);
    mWheelRadius = mWheelRadius / mUnitScale;

    isaac::utils::safeGetAttribute(typedPrim.GetWheelBaseAttr(), mWheelBase);
    mWheelBase = mWheelBase / mUnitScale;

    pxr::SdfPath chassisPath;
    std::string wheelFLName;
    std::string wheelFRName;

    pxr::SdfPathVector targets;
    typedPrim.GetChassisPrimRel().GetTargets(&targets);
    if (targets.size() == 0)
    {
        return;
    }

    chassisPath = targets[0];

    if (mDynamicControlPtr->peekObjectType(chassisPath.GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(chassisPath.GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("chassisPrim is not a valid articulation");
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation not found for chassisPrim");
        return;
    }
    mChassisHandle = mDynamicControlPtr->getArticulationRootBody(mArticulationHandle);


    isaac::utils::safeGetAttribute(typedPrim.GetLeftWheelJointNameAttr(), wheelFLName);

    mWheelFLHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFLName.c_str());
    // Get the wheel prim from the joint
    if (!mWheelFLHandle)
    {
        if (wheelFLName.empty())
        {
            CARB_LOG_ERROR(
                "leftWheelJointName not found, please enter the name of the left wheel in Property Tab -> Raw USD Properties -> leftWheelJointName");
        }
        else
        {
            CARB_LOG_ERROR("leftWheelJointPrim %s not valid", wheelFLName.c_str());
        }
        return;
    }
    isaac::utils::safeGetAttribute(typedPrim.GetRightWheelJointNameAttr(), wheelFRName);


    mWheelFRHandle = mDynamicControlPtr->findArticulationDof(mArticulationHandle, wheelFRName.c_str());

    if (!mWheelFRHandle)
    {
        if (wheelFRName.empty())
        {
            CARB_LOG_ERROR(
                "rightWheelJointName not found, please enter the name of the right wheel in Property Tab -> Raw USD Properties -> rightWheelJointName");
        }

        else
        {
            CARB_LOG_ERROR("rightWheelJointPrim %s not valid", wheelFRName.c_str());
        }
        return;
    }

    // warn if using default wheel radius and base distance
    if (mWheelRadius == 0.0f)
    {
        CARB_LOG_ERROR(
            "Wheel radius zero. Please enter the wheel radius in Property Tab -> Raw USD Properties -> wheelRadius");
    }
    if (mWheelBase == 0.0f)
    {
        CARB_LOG_ERROR(
            "Wheel base distance used. Please enter the wheel radius in Property Tab -> Raw USD Properties -> wheel base ");
    }
}

void RosDifferentialBase::pubCallback(ros::Publisher* pub)
{
    nav_msgs::Odometry odomMsg;
    odomMsg.header.seq = 0;
    setRosTimeStamp(odomMsg.header.stamp);

    odomMsg.header.frame_id = mOdomFrameId;
    odomMsg.child_frame_id = mBaseFrameId;

    auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
    // auto chassisLinVel = mDynamicControlPtr->getRigidBodyLinearVelocity(mChassisHandle);
    auto chassisLocalLinVel = mDynamicControlPtr->getRigidBodyLocalLinearVelocity(mChassisHandle);
    auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mChassisHandle);

    // CARB_LOG_ERROR("[%f %f %f] [%f %f %f] [%f %f %f]", chassisPose.p.x, chassisPose.p.y, chassisPose.p.z,
    //    chassisLinVel.x, chassisLinVel.y, chassisLinVel.z, chassisAngVel.x, chassisAngVel.y, chassisAngVel.z);

    // calculate odom reading from starting position
    pxr::GfVec3d globalTranslation = pxr::GfVec3d(
        chassisPose.p.x - startingPose.p.x, chassisPose.p.y - startingPose.p.y, chassisPose.p.z - startingPose.p.z);
    pxr::GfVec3d odomTranslation =
        (asGfRotation(startingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;
    pxr::GfQuatd odomRotation = (asGfRotation(chassisPose.r) * asGfRotation(startingPose.r).GetInverse()).GetQuat();
    // velocity in chassis frame
    float measuredSpeedFront = pxr::GfDot(asGfVec3d(chassisLocalLinVel), mRobotFront) * mUnitScale;

    // pxr::GfVec2d measuredSpeed = pxr::GfVec2d(measuredSpeedFront, mZUp ? chassisAngVel.z : chassisAngVel.y);
    // pxr::GfVec2d measuredAcceleration = (measuredSpeed - mLastSpeed) / mTimeDelta;
    // mLastAcceleration +=
    // timedSmoothingFactor(mTimeDelta, mAccelerationSmoothing) * (measuredAcceleration - mLastAcceleration);

    // odometry messages
    odomMsg.twist.twist.linear.x = measuredSpeedFront;
    if (mZUp)
        odomMsg.twist.twist.angular.z = chassisAngVel.z;
    else
        odomMsg.twist.twist.angular.y = chassisAngVel.y;
    odomMsg.pose.pose.position.x = odomTranslation[0];
    odomMsg.pose.pose.position.y = odomTranslation[1];
    odomMsg.pose.pose.position.z = odomTranslation[2];
    odomMsg.pose.pose.orientation.w = odomRotation.GetReal();
    odomMsg.pose.pose.orientation.x = odomRotation.GetImaginary()[0];
    odomMsg.pose.pose.orientation.y = odomRotation.GetImaginary()[1];
    odomMsg.pose.pose.orientation.z = odomRotation.GetImaginary()[2];

    pub->publish(odomMsg);
}
void RosDifferentialBase::tfPubCallback(ros::Publisher* pub)
{
    tf2_msgs::TFMessage tfMsg;
    geometry_msgs::TransformStamped msg;
    msg.header.seq = 0;
    setRosTimeStamp(msg.header.stamp);

    msg.header.frame_id = mOdomFrameId;
    msg.child_frame_id = mBaseFrameId;

    auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
    // calculate relative pose from starting pose
    pxr::GfVec3d globalTranslation = pxr::GfVec3d(
        chassisPose.p.x - startingPose.p.x, chassisPose.p.y - startingPose.p.y, chassisPose.p.z - startingPose.p.z);
    pxr::GfVec3d odomTranslation =
        (asGfRotation(startingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;
    pxr::GfQuatd odomRotation = (asGfRotation(chassisPose.r) * asGfRotation(startingPose.r).GetInverse()).GetQuat();

    msg.transform.translation.x = odomTranslation[0];
    msg.transform.translation.y = odomTranslation[1];
    msg.transform.translation.z = odomTranslation[2];
    msg.transform.rotation.w = odomRotation.GetReal();
    msg.transform.rotation.x = odomRotation.GetImaginary()[0];
    msg.transform.rotation.y = odomRotation.GetImaginary()[1];
    msg.transform.rotation.z = odomRotation.GetImaginary()[2];

    tfMsg.transforms.push_back(msg);
    pub->publish(tfMsg);
}
void RosDifferentialBase::subCallback(const geometry_msgs::Twist::ConstPtr& msg)
{
    mCommandedSpeed[0] = pxr::GfClamp(msg->linear.x, double(-mMaximumSpeed[0]), double(mMaximumSpeed[0])) / mUnitScale;
    mCommandedSpeed[1] =
        pxr::GfClamp(mZUp ? msg->angular.z : msg->angular.y, double(-mMaximumSpeed[1]), double(mMaximumSpeed[1]));

    mLastCommandTime = mTimeSeconds;

    // Compute new velocities
    getWheelDesireSpeed(mCommandedSpeed);
    // CARB_LOG_ERROR("Speeds %f %f", mWheelDesiredSpeed[0], mWheelDesiredSpeed[1]);
    if (mArticulationHandle)
    {
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
    }
    else
    {
        CARB_LOG_ERROR("Differential Base Articulation Handle Is Invalid");
        return;
    }
    // Apply velocities
    if (mWheelFLHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFLHandle, mWheelDesiredSpeed[0]);
    }
    else
    {
        CARB_LOG_ERROR("Differential Base Left Wheel Invalid");
        return;
    }
    if (mWheelFRHandle)
    {
        mDynamicControlPtr->setDofVelocityTarget(mWheelFRHandle, mWheelDesiredSpeed[1]);
    }
    else
    {
        CARB_LOG_ERROR("Differential Base Right Wheel Invalid");
        return;
    }
}

void RosDifferentialBase::getWheelDesireSpeed(const pxr::GfVec2d& mCommandedSpeed)
{
    mBrakeRequested =
        pxr::GfIsClose(mCommandedSpeed[0], 0.0f, FLT_EPSILON) && pxr::GfIsClose(mCommandedSpeed[1], 0.0f, FLT_EPSILON);
    // mCommandedSpeed[0] is in stageunits/s
    // mCommandedSpeed[1] is in rad/s
    // mWheelBase is in stageunits
    // mWheelRadius is in stageunits
    // mWheelDesiredSpeed is in rad/s


    if ((std::abs(mWheelRadius) < 1e-5) || (std::abs(mWheelBase) < 1e-5))
    {
        CARB_LOG_ERROR("Wheel radius is zero, cannot calculate robot speed");
        CARB_LOG_ERROR("Wheel base distance is zero, cannot calculate robot speed");
    }
    else
    {
        mWheelDesiredSpeed[0] = (mCommandedSpeed[0] - mCommandedSpeed[1] * mWheelBase) / mWheelRadius;
        mWheelDesiredSpeed[1] = (mCommandedSpeed[0] + mCommandedSpeed[1] * mWheelBase) / mWheelRadius;
    }
}

float RosDifferentialBase::timedSmoothingFactor(float dt, float lambda)
{
    if (lambda <= dt * 0.01f)
    {
        return 0.0;
    }
    else
    {
        return 1.0f - std::exp(-dt / lambda);
    }
}

}
}
}
