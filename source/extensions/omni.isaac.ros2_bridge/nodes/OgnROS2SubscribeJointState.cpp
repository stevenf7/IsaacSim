// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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

#include "omni/isaac/utils/UsdUtilities.h"
#include "sensor_msgs/msg/joint_state.hpp"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/ros/Ros2Node.h>
#include <omni/isaac/utils/Math.h>

#include <OgnROS2SubscribeJointStateDatabase.h>


class OgnROS2SubscribeJointState : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeJointStateDatabase::sInternalState<OgnROS2SubscribeJointState>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.internalState<OgnROS2SubscribeJointState>();

        // if not simulating, skip subscriber
        if (!state.mDynamicControlPtr->isSimulating())
        {
            return false;
        }

        const GraphContextObj& context = db.abi_context();
        const char* primPath = db.inputs.targetPrim.path();

        // spin once calls reset automatically if it was not successful
        const auto& nodeObj = db.abi_node();
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }
            state.mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(stage);

            // Verify we have a valid articulation prim
            if (state.mDynamicControlPtr->peekObjectType(primPath) == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.mArticulationHandle = state.mDynamicControlPtr->getArticulation(primPath);
            }
            else
            {
                db.logError("Prim is not an articulation");
                return false;
            }

            if (!state.mArticulationHandle)
            {

                db.logError("Articulation %s not found", primPath);
                return false;
            }

            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);
            if (!validateTopic(fullTopicName))
            {
                return false;
            }
            state.mCallback = [&state, &db](const sensor_msgs::msg::JointState::SharedPtr& msg)
            { state.subCallback(msg, db); };

            state.mSubscriber = state.mNodeHandle->create_subscription<sensor_msgs::msg::JointState>(
                fullTopicName, db.inputs.queueSize(), state.mCallback);
            return true;
        }

        return true;
    }


    void subCallback(const sensor_msgs::msg::JointState::SharedPtr& msg, OgnROS2SubscribeJointStateDatabase& db)
    {
        const unsigned int num_actuators = msg->name.size();

        if (msg->position.size() != 0)
        {
            if (msg->position.size() != num_actuators)
            {
                db.logError("size of joint position array does not match number of joints");
                return;
            }
            mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
            for (unsigned int actuator_idx = 0; actuator_idx < num_actuators; actuator_idx++)
            {
                omni::isaac::dynamic_control::DcHandle dof =
                    mDynamicControlPtr->findArticulationDof(mArticulationHandle, msg->name[actuator_idx].c_str());
                if (dof)
                {
                    omni::isaac::dynamic_control::DcDofProperties props;
                    mDynamicControlPtr->getDofProperties(dof, &props);
                    float elementValue = static_cast<float>(msg->position[actuator_idx]);
                    if (props.type == omni::isaac::dynamic_control::DcDofType::eTranslation)
                    {
                        elementValue *= mUnitScale;
                    }
                    if (props.hasLimits)
                    {
                        elementValue = CARB_CLAMP(elementValue, props.lower, props.upper);
                    }
                    if (props.type == omni::isaac::dynamic_control::DcDofType::eRotation)
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
                db.logError("size of joint velocity array does not match number of joints");
                return;
            }
            mDynamicControlPtr->wakeUpArticulation(mArticulationHandle);
            for (unsigned int actuator_idx = 0; actuator_idx < num_actuators; actuator_idx++)
            {
                omni::isaac::dynamic_control::DcHandle dof =
                    mDynamicControlPtr->findArticulationDof(mArticulationHandle, msg->name[actuator_idx].c_str());
                if (dof)
                {
                    float velocityValue = static_cast<float>(msg->velocity[actuator_idx]);
                    omni::isaac::dynamic_control::DcDofProperties props;
                    mDynamicControlPtr->getDofProperties(dof, &props);
                    // Clamp after scale to stage units
                    if (props.type == omni::isaac::dynamic_control::DcDofType::eTranslation)
                    {
                        velocityValue *= mUnitScale;
                    }
                    velocityValue = std::min(velocityValue, props.maxVelocity);

                    mDynamicControlPtr->setDofVelocityTarget(dof, velocityValue);
                }
                else
                {
                    db.logError("Entity not found in articulation");
                }
            }
        }
        else
        {
            db.logError("Only Position and Velocity joint commands are supported");
            return;
        }
    }


    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeJointStateDatabase::sInternalState<OgnROS2SubscribeJointState>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Subscription<sensor_msgs::msg::JointState>> mSubscriber = nullptr;
    std::function<void(const sensor_msgs::msg::JointState::SharedPtr)> mCallback;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    double mUnitScale = 1;
};

REGISTER_OGN_NODE()
