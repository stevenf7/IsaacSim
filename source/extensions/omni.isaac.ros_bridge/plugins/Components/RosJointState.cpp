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
                if (props.type == DcDofType::eTranslation)
                {
                    mDynamicControlPtr->setDofPositionTarget(dof, msg->position[actuator_idx] * mUnitScale);
                }
                else
                {
                    mDynamicControlPtr->setDofPositionTarget(dof, msg->position[actuator_idx]);
                }
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
                if (props.hasLimits)
                {
                    velocityValue = std::min(velocityValue, props.maxVelocity);
                }
                mDynamicControlPtr->getDofProperties(dof, &props);
                if (props.type == DcDofType::eTranslation)
                {
                    velocityValue *= mUnitScale;
                }
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
        CARB_LOG_ERROR("Only Position and Velocity Controls are supported");
        return;
    }
}

}
}
}
