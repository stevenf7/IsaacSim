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

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2SubscribeJointStateDatabase.h>


class OgnROS2SubscribeJointState : public Ros2Node
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeJointStateDatabase::sInternalState<OgnROS2SubscribeJointState>(nodeObj);
        state.mContextObj = contextObj;
        state.mNodeObj = nodeObj;
    }

    static bool compute(OgnROS2SubscribeJointStateDatabase& db)
    {
        auto& state = db.internalState<OgnROS2SubscribeJointState>();

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
        const size_t num_actuators = msg->name.size();

        if (num_actuators == 0)
        {
            db.logWarning("No joints found");
            return;
        }

        db.outputs.jointNames().resize(num_actuators);

        // Copy joint names and convert to token array
        std::transform(msg->name.begin(), msg->name.end(), db.outputs.jointNames().begin(),
                       [db](std::string name) { return db.stringToToken(name.c_str()); });

        if (msg->position.size() > 0)
        {
            if (msg->position.size() != num_actuators)
            {
                db.logError("size of joint position array does not match number of joints");
                return;
            }
            db.outputs.positionCommand().resize(num_actuators);
            std::memcpy(db.outputs.positionCommand().data(), msg->position.data(), num_actuators * sizeof(double));
        }
        else
        {
            db.outputs.positionCommand().resize(0);
        }

        if (msg->velocity.size() != 0)
        {
            if (msg->velocity.size() != num_actuators)
            {
                db.logError("size of joint velocity array does not match number of joints");
                return;
            }
            db.outputs.velocityCommand().resize(num_actuators);
            std::memcpy(db.outputs.velocityCommand().data(), msg->velocity.data(), num_actuators * sizeof(double));
        }
        else
        {
            db.outputs.velocityCommand().resize(0);
        }

        if (msg->effort.size() != 0)
        {
            if (msg->velocity.size() != num_actuators)
            {
                db.logError("size of joint velocity array does not match number of joints");
                return;
            }

            db.outputs.velocityCommand().resize(num_actuators);
            std::memcpy(db.outputs.velocityCommand().data(), msg->velocity.data(), num_actuators * sizeof(double));
        }
        else
        {
            db.outputs.effortCommand().resize(0);
        }

        db.outputs.timeStamp() = rclcpp::Time(msg->header.stamp).seconds();

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
    }

    static bool updateNodeVersion(const GraphContextObj& context, const NodeObj& nodeObj, int oldVersion, int newVersion)
    {
        if (oldVersion < newVersion)
        {
            const INode* const iNode = nodeObj.iNode;
            if (oldVersion < 2)
            {
                iNode->removeAttribute(nodeObj, "inputs:targetPrim");
            }
            return true;
        }
        return false;
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeJointStateDatabase::sInternalState<OgnROS2SubscribeJointState>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        auto db = OgnROS2SubscribeJointStateDatabase(mContextObj, mNodeObj);

        db.outputs.jointNames.resize(0);
        db.outputs.positionCommand.resize(0);
        db.outputs.velocityCommand.resize(0);
        db.outputs.effortCommand.resize(0);

        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        Ros2Node::reset();
    }

private:
    std::shared_ptr<rclcpp::Subscription<sensor_msgs::msg::JointState>> mSubscriber = nullptr;
    std::function<void(const sensor_msgs::msg::JointState::SharedPtr)> mCallback;

    GraphContextObj mContextObj;
    NodeObj mNodeObj;
};

REGISTER_OGN_NODE()
