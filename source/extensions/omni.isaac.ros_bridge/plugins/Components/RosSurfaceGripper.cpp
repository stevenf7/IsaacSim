// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include "RosSurfaceGripper.h"

#include <carb/Framework.h>

#include <omni/isaac/utils/Conversions.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosSurfaceGripper::RosSurfaceGripper(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
    mGripperJoint = std::make_unique<omni::isaac::surface_gripper::SurfaceGripper>(dynamicControlPtr);
}

RosSurfaceGripper::~RosSurfaceGripper()
{
    CARB_LOG_INFO("RosSurfaceGripper Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSurfaceGripperPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSurfaceGripperSubTopic);
}

void RosSurfaceGripper::initialize(RosNode* rosNode,
                                   const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                                   pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
}
void RosSurfaceGripper::onStart()
{
    onComponentChange();
}
void RosSurfaceGripper::onStop()
{
    mGripperJoint->open();
}
void RosSurfaceGripper::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosSurfaceGripper& typedPrim = (pxr::RosBridgeSchemaRosSurfaceGripper)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSurfaceGripperPubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mSurfaceGripperSubTopic);


    isaac::utils::safeGetAttribute(typedPrim.GetSurfaceGripperPubTopicAttr(), mSurfaceGripperPubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetSurfaceGripperSubTopicAttr(), mSurfaceGripperSubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);

    mRosNode->createPublisher<sensor_msgs::JointState>(
        mPrim.GetPath().GetString(), mSurfaceGripperPubTopic, mQueueSize, &RosSurfaceGripper::pubCallback, this);
    mRosNode->createSubscriber<sensor_msgs::JointState>(
        mPrim.GetPath().GetString(), mSurfaceGripperSubTopic, mQueueSize, &RosSurfaceGripper::subCallback, this);

    isaac::utils::safeGetAttribute(typedPrim.GetGripperEntityAttr(), mGripperEntityName);

    pxr::SdfPathVector targets;
    typedPrim.GetD6JointPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        std::string jointPath = mPrim.GetPath().GetString() + "/d6Joint";

        CARB_LOG_WARN("JointPrim path not specified, using %s", jointPath.c_str());
        mProps.d6JointPath = jointPath;
    }
    else
    {
        mProps.d6JointPath = targets[0].GetString();
    }


    typedPrim.GetParentPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        CARB_LOG_ERROR("Parent prim relationsip for surface gripper not specified");
        return;
    }
    mProps.parentPath = targets[0].GetString();

    pxr::GfVec3f offsetPosition(0, 0, 0);
    pxr::GfQuatf offsetRotation(1, 0, 0, 0);

    mProps.gripThreshold = 1;
    mProps.forceLimit = 1e10;
    mProps.torqueLimit = 1e10;
    mProps.bendAngle = 0;
    mProps.stiffness = 1e10;
    mProps.damping = 1e3;

    isaac::utils::safeGetAttribute(typedPrim.GetOffsetPositionAttr(), offsetPosition);
    isaac::utils::safeGetAttribute(typedPrim.GetOffsetRotationAttr(), offsetRotation);
    isaac::utils::safeGetAttribute(typedPrim.GetGripThresholdAttr(), mProps.gripThreshold);
    isaac::utils::safeGetAttribute(typedPrim.GetForceLimitAttr(), mProps.forceLimit);
    isaac::utils::safeGetAttribute(typedPrim.GetTorqueLimitAttr(), mProps.torqueLimit);
    isaac::utils::safeGetAttribute(typedPrim.GetBendAngleAttr(), mProps.bendAngle);
    isaac::utils::safeGetAttribute(typedPrim.GetStiffnessAttr(), mProps.stiffness);
    isaac::utils::safeGetAttribute(typedPrim.GetDampingAttr(), mProps.damping);
    mProps.offset = omni::isaac::utils::conversions::asDcTransform(offsetPosition, offsetRotation);
    mGripperJoint->initialize(mProps);
}

void RosSurfaceGripper::pubCallback(ros::Publisher* pub)
{
    sensor_msgs::JointState msg;
    msg.header.seq = 0;
    setRosTimeStamp(msg.header.stamp);


    msg.name.push_back(mGripperEntityName);
    bool gripperStatus = mGripperJoint->isClosed();
    if (gripperStatus)
        msg.position.push_back(1.0);
    else
        msg.position.push_back(0.0);

    pub->publish(msg);
}
void RosSurfaceGripper::subCallback(const sensor_msgs::JointState::ConstPtr& msg)
{
    const unsigned int num_actuators = msg->name.size();
    if (num_actuators != 0)
    {
        auto itr = std::find(msg->name.begin(), msg->name.end(), mGripperEntityName);

        if (itr == msg->name.end())
        {
            CARB_LOG_ERROR("Gripper command joint name does not match usd property %s", mGripperEntityName.c_str());
            return;
        }
        int actuatorIndex = std::distance(msg->name.begin(), itr);
        if (actuatorIndex >= 0)
        {
            float actuatorStatus = msg->position[actuatorIndex];
            if (actuatorStatus >= 0.5)
            {
                CARB_LOG_INFO("Closing Gripper");

                if (!mGripperJoint->isClosed())
                {
                    bool status = mGripperJoint->close();
                    if (status)
                    {
                        CARB_LOG_INFO("Gripper Closed");
                    }
                    else
                    {
                        CARB_LOG_WARN("Gripper not closed successfully");
                    }
                }
                else
                {
                    CARB_LOG_INFO("Gripper already closed");
                }
            }
            else
            {
                CARB_LOG_INFO("Opening Gripper");
                if (mGripperJoint->isClosed())
                {
                    bool status = mGripperJoint->open();
                    if (status)
                    {
                        CARB_LOG_INFO("Gripper Opened");
                    }
                    else
                    {
                        CARB_LOG_WARN("Gripper not opened successfully");
                    }
                }
                else
                {
                    CARB_LOG_INFO("Gripper already opened");
                }
            }
        }
    }
}

}
}
}
