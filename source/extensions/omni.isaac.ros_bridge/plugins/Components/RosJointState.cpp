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

#include "RosJointState.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include "rosgraph_msgs/Clock.h"
#include "std_msgs/Int64.h"
#include "std_msgs/UInt8.h"
#include "std_srvs/Empty.h"
#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{

using namespace omni::isaac::dynamic_control;

RosJointState::RosJointState(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

RosJointState::~RosJointState()
{
    CARB_LOG_INFO("RosJointState Destroyed");
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mJointStatePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mJointStateSubTopic);
}

void RosJointState::initialize(RosNode* rosNode,
                               const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                               pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(rosNode, prim, stage);
    onComponentChange();
}

void RosJointState::onComponentChange()
{

    IsaacComponent::onComponentChange();

    const pxr::RosBridgeSchemaRosJointState& typedPrim = (pxr::RosBridgeSchemaRosJointState)mPrim;
    // Destroy the old message, in case the topic changes
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mJointStatePubTopic);
    mRosNode->destroyMessage(mPrim.GetPath().GetString() + mJointStateSubTopic);


    isaac::utils::safeGetAttribute(typedPrim.GetJointStatePubTopicAttr(), mJointStatePubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetJointStateSubTopicAttr(), mJointStateSubTopic);
    isaac::utils::safeGetAttribute(typedPrim.GetQueueSizeAttr(), mQueueSize);

    mRosNode->createPublisher<sensor_msgs::JointState>(
        mPrim.GetPath().GetString(), mJointStatePubTopic, mQueueSize, &RosJointState::pubCallback, this);
    mRosNode->createSubscriber<sensor_msgs::JointState>(
        mPrim.GetPath().GetString(), mJointStateSubTopic, mQueueSize, &RosJointState::subCallback, this);

    pxr::SdfPathVector targets;
    typedPrim.GetArticulationPrimRel().GetTargets(&targets);

    if (targets.size() == 0)
    {
        return;
    }
    mArticulationPath = targets[0];

    if (mDynamicControlPtr->peekObjectType(mArticulationPath.GetString().c_str()) ==
        omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        mArticulationHandle = mDynamicControlPtr->getArticulation(mArticulationPath.GetString().c_str());
    }
    else
    {
        CARB_LOG_ERROR("Articulation %s is not valid art", mArticulationPath.GetString().c_str());
        return;
    }
    if (!mArticulationHandle)
    {
        CARB_LOG_ERROR("Articulation %s not found", mArticulationPath.GetString().c_str());
        return;
    }
    mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}

void RosJointState::pubCallback(ros::Publisher* pub)
{
    if (!mArticulationHandle)
    {
        if (mDynamicControlPtr->peekObjectType(mArticulationPath.GetString().c_str()) ==
            omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            mArticulationHandle = mDynamicControlPtr->getArticulation(mArticulationPath.GetString().c_str());
        }
        else
        {
            CARB_LOG_ERROR("Articulation %s is not valid art", mArticulationPath.GetString().c_str());
            return;
        }
        if (!mArticulationHandle)
        {
            CARB_LOG_ERROR("Articulation %s not found", mArticulationPath.GetString().c_str());
            return;
        }
    }

    double stageUnits = 1.0 / mUnitScale;
    sensor_msgs::JointState msg;
    msg.header.seq = 0;
    msg.header.stamp.fromSec(mTimeSeconds);


    mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);

    int num_dofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);

    for (int j = 0; j < num_dofs; j++)
    {

        DcHandle dof = mDynamicControlPtr->getArticulationDof(mArticulationHandle, j);
        if (dof)
        {
            msg.name.push_back(mDynamicControlPtr->getDofName(dof));
            DcDofProperties props;
            mDynamicControlPtr->getDofProperties(dof, &props);
            if (props.type == DcDofType::eTranslation)
            {
                msg.position.push_back(mDynamicControlPtr->getDofPosition(dof) * stageUnits);
            }
            else
            {
                msg.position.push_back(mDynamicControlPtr->getDofPosition(dof));
            }
            msg.velocity.push_back(mDynamicControlPtr->getDofVelocity(dof));
            msg.effort.push_back(0 /*mDynamicControlPtr->getDofForce(dof)*/); // TODO
        }
    }


    pub->publish(msg);
}
void RosJointState::subCallback(const sensor_msgs::JointState::ConstPtr& msg)
{
    if (!mArticulationHandle)
    {
        if (mDynamicControlPtr->peekObjectType(mArticulationPath.GetString().c_str()) ==
            omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            mArticulationHandle = mDynamicControlPtr->getArticulation(mArticulationPath.GetString().c_str());
        }
        else
        {
            CARB_LOG_ERROR("Articulation %s is not valid art", mArticulationPath.GetString().c_str());
            return;
        }
        if (!mArticulationHandle)
        {
            CARB_LOG_ERROR("Articulation %s not found", mArticulationPath.GetString().c_str());
            return;
        }
    }
    const unsigned int num_actuators = msg->name.size();
    if (msg->position.size() != 0)
    {
        if (msg->position.size() != num_actuators)
        {
            CARB_LOG_ERROR("size of joint position array does not match number of joints");
            return;
        }
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
        for (unsigned int actuator_idx = 0; actuator_idx < num_actuators; actuator_idx++)
        {
            DcHandle dof = mDynamicControlPtr->findArticulationDof(mArticulationHandle, msg->name[actuator_idx].c_str());
            if (dof)
            {
                DcDofProperties props;
                mDynamicControlPtr->getDofProperties(dof, &props);
                float elementValue = static_cast<float>(msg->position[actuator_idx]);
                if (props.type == DcDofType::eTranslation)
                {
                    elementValue *= mUnitScale;
                }
                if (props.hasLimits)
                {
                    elementValue = CARB_CLAMP(elementValue, props.lower, props.upper);
                }
                if (props.type == DcDofType::eRotation)
                {
                    // Joints become unstable if we get close to 2*pi limit. Artificially limit as a workaround
                    elementValue = CARB_CLAMP(elementValue, -6.25, 6.25);
                }
                mDynamicControlPtr->setDofPositionTarget(dof, elementValue);
            }
        }
    }
    else if (msg->velocity.size() != 0)
    {
        if (msg->velocity.size() != num_actuators)
        {
            CARB_LOG_ERROR("size of joint velocity array does not match number of joints");
            return;
        }
        mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
        for (unsigned int actuator_idx = 0; actuator_idx < num_actuators; actuator_idx++)
        {
            DcHandle dof = mDynamicControlPtr->findArticulationDof(mArticulationHandle, msg->name[actuator_idx].c_str());
            if (dof)
            {
                float velocityValue = static_cast<float>(msg->velocity[actuator_idx]);
                DcDofProperties props;
                mDynamicControlPtr->getDofProperties(dof, &props);
                // Clamp after scale to stage units
                if (props.type == DcDofType::eTranslation)
                {
                    velocityValue *= mUnitScale;
                }
                velocityValue = std::min(velocityValue, props.maxVelocity);

                mDynamicControlPtr->setDofVelocityTarget(dof, velocityValue);
            }
            else
            {
                CARB_LOG_ERROR("Entity not found in articulation");
            }
        }
    }
    else
    {
        CARB_LOG_ERROR("Only Position and Velocity joint commands are supported");
        return;
    }
}

}
}
}
