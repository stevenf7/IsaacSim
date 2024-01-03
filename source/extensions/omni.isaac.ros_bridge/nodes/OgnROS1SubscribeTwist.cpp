// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "geometry_msgs/Twist.h"

#include <OgnROS1SubscribeTwistDatabase.h>
#include <RosNode.h>

class OgnROS1SubscribeTwist : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1SubscribeTwistDatabase::sInternalState<OgnROS1SubscribeTwist>(nodeObj);
    // }

    static bool compute(OgnROS1SubscribeTwistDatabase& db)
    {
        auto& state = db.internalState<OgnROS1SubscribeTwist>();
        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }
        // Subscriber was not valid, create a new one
        if (!state.mSubscriber)
        {
            const std::string& topicName = db.inputs.topicName();
            if (!validateTopic(topicName))
            {
                return false;
            }
            state.mCallback = [&state, &db](const geometry_msgs::Twist::ConstPtr& msg) { state.subCallback(msg, db); };

            state.mSubscriber = std::make_unique<ros::Subscriber>(
                state.mNodeHandle->subscribe<geometry_msgs::Twist>(topicName, db.inputs.queueSize(), state.mCallback));
            return true;
        }

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1SubscribeTwistDatabase::sInternalState<OgnROS1SubscribeTwist>(nodeObj);
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
        RosNode::reset();
    }

    void subCallback(const geometry_msgs::Twist::ConstPtr& msg, OgnROS1SubscribeTwistDatabase& db)
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
    std::unique_ptr<ros::Subscriber> mSubscriber;
    std::function<void(const geometry_msgs::Twist::ConstPtr&)> mCallback;
};

REGISTER_OGN_NODE()
