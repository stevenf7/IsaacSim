// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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
#include "sensor_msgs/JointState.h"

#include <carb/Framework.h>
#include <carb/Types.h>
#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1SubscribeJointStateDatabase.h>


class OgnROS1SubscribeJointState : public RosNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1SubscribeJointStateDatabase::sInternalState<OgnROS1SubscribeJointState>(nodeObj);
        state.mContextObj = contextObj;
        state.mNodeObj = nodeObj;
    }

    static bool compute(OgnROS1SubscribeJointStateDatabase& db)
    {
        auto& state = db.internalState<OgnROS1SubscribeJointState>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            // Setup ROS publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mCallback = [&state, &db](const sensor_msgs::JointState::ConstPtr& msg) { state.subCallback(msg, db); };

            state.mSubscriber = std::make_unique<ros::Subscriber>(state.mNodeHandle->subscribe<sensor_msgs::JointState>(
                topicName, db.inputs.queueSize(), state.mCallback));
            return true;
        }

        return true;
    }


    void subCallback(const sensor_msgs::JointState::ConstPtr& msg, OgnROS1SubscribeJointStateDatabase& db)
    {
        const unsigned int num_actuators = msg->name.size();

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
            if (msg->effort.size() != num_actuators)
            {
                db.logError("size of effort array does not match number of joints");
                return;
            }

            db.outputs.effortCommand().resize(num_actuators);
            std::memcpy(db.outputs.effortCommand().data(), msg->effort.data(), num_actuators * sizeof(double));
        }
        else
        {
            db.outputs.effortCommand().resize(0);
        }

        db.outputs.timeStamp() = msg->header.stamp.toSec();

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
        auto& state = OgnROS1SubscribeJointStateDatabase::sInternalState<OgnROS1SubscribeJointState>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        auto db = OgnROS1SubscribeJointStateDatabase(mContextObj, mNodeObj);

        db.outputs.jointNames.resize(0);
        db.outputs.positionCommand.resize(0);
        db.outputs.velocityCommand.resize(0);
        db.outputs.effortCommand.resize(0);

        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        RosNode::reset();
    }

private:
    std::unique_ptr<ros::Subscriber> mSubscriber;
    std::function<void(const sensor_msgs::JointState::ConstPtr&)> mCallback;
    GraphContextObj mContextObj;
    NodeObj mNodeObj;
};

REGISTER_OGN_NODE()
