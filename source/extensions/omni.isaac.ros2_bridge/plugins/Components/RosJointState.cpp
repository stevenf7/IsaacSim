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

#include "rosgraph_msgs/msg/clock.hpp"
#include "std_msgs/msg/int64.hpp"
#include "std_msgs/msg/u_int8.hpp"
#include "std_srvs/srv/empty.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <omni/isaac/utils/Math.h>

#include <time.h>

namespace omni
{
namespace isaac
{
namespace ros2_bridge
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
void RosJointState::onStart()
{
    onComponentChange();
}
void RosJointState::onStop()
{
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

    mRosNode->createPublisher<sensor_msgs::msg::JointState>(
        mPrim.GetPath().GetString(), mJointStatePubTopic, mQueueSize, &RosJointState::pubCallback, this);
    mRosNode->createSubscriber<sensor_msgs::msg::JointState>(
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

void RosJointState::pubCallback(rclcpp::PublisherBase* pub)
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
    sensor_msgs::msg::JointState msg;
    setRosTimeStamp(msg.header.stamp);


    mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);

    int num_dofs = mDynamicControlPtr->getArticulationDofCount(mArticulationHandle);

    DcDofState* states =
        mDynamicControlPtr->getArticulationDofStates(mArticulationHandle, omni::isaac::dynamic_control::kDcStateAll);
    std::vector<dynamic_control::DcDofProperties> dofProps(num_dofs);
    mDynamicControlPtr->getArticulationDofProperties(mArticulationHandle, dofProps.data());

    if (states != nullptr)
    {

        for (int j = 0; j < num_dofs; j++)
        {
            DcHandle dof = mDynamicControlPtr->getArticulationDof(mArticulationHandle, j);
            if (dof)
            {
                msg.name.push_back(mDynamicControlPtr->getDofName(dof));
            }
            if (dofProps[j].type == DcDofType::eTranslation)
            {
                msg.position.push_back(isaac::utils::math::roundNearest(states[j].pos * stageUnits, 10000.0)); // m
                msg.velocity.push_back(isaac::utils::math::roundNearest(states[j].vel * stageUnits, 1000.0)); // m/s
                msg.effort.push_back(isaac::utils::math::roundNearest(states[j].effort * stageUnits, 10000.0)); // N
            }
            else
            {
                msg.position.push_back(isaac::utils::math::roundNearest(states[j].pos, 10000.0)); // rad
                msg.velocity.push_back(isaac::utils::math::roundNearest(states[j].vel, 1000.0)); // rad/s
                msg.effort.push_back(
                    isaac::utils::math::roundNearest(states[j].effort * stageUnits * stageUnits, 10000.0)); // N*m
            }
        }
    }


    static_cast<rclcpp::Publisher<sensor_msgs::msg::JointState, std::allocator<void>>*>(pub)->publish(msg);
}
void RosJointState::subCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
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
