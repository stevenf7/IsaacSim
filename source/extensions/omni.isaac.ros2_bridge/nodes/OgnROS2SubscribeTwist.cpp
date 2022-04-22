// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "geometry_msgs/msg/twist.hpp"

#include <omni/isaac/ros/Ros2Node.h>

#include <OgnROS2SubscribeTwistDatabase.h>

class OgnROS2SubscribeTwist : public Ros2Node
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS2SubscribeTwistDatabase::sInternalState<OgnROS2SubscribeTwist>(nodeObj);
    // }

    static bool compute(OgnROS2SubscribeTwistDatabase& db)
    {
        auto& state = db.internalState<OgnROS2SubscribeTwist>();
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
            const std::string& topicName = db.inputs.topicName();
            std::string fullTopicName = addTopicPrefix(db.inputs.nodeNamespace(), topicName);
            if (!validateTopic(fullTopicName))
            {
                return false;
            }
            state.mCallback = [&state, &db](const geometry_msgs::msg::Twist::SharedPtr msg)
            { state.subCallback(msg, db); };

            state.mSubscriber = state.mNodeHandle->create_subscription<geometry_msgs::msg::Twist>(
                fullTopicName, db.inputs.queueSize(), state.mCallback);
            return true;
        }

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2SubscribeTwistDatabase::sInternalState<OgnROS2SubscribeTwist>(nodeObj);
        state.reset();
    }

    /**
     * @brief Reset the node
     * Note that we need to reset the subscriber first so it doesn't get called again, then the callback, and then call
     * the base class reset
     *
     */
    virtual void reset()
    {
        mSubscriber.reset(); // This should be reset before we reset the handle.
        mCallback = nullptr;
        Ros2Node::reset();
    }

    void subCallback(const geometry_msgs::msg::Twist::SharedPtr& msg, OgnROS2SubscribeTwistDatabase& db)
    {
        auto& linVel = db.outputs.linearVelocity();

        linVel[0] = msg->linear.x;
        linVel[1] = msg->linear.y;
        linVel[2] = msg->linear.z;

        auto& angVel = db.outputs.angularVelocity();

        angVel[0] = msg->angular.x;
        angVel[1] = msg->angular.y;
        angVel[2] = msg->angular.z;

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
    }


private:
    std::shared_ptr<rclcpp::Subscription<geometry_msgs::msg::Twist>> mSubscriber = nullptr;
    std::function<void(const geometry_msgs::msg::Twist::SharedPtr)> mCallback;
};

REGISTER_OGN_NODE()
