// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "ackermann_msgs/AckermannDriveStamped.h"

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1SubscribeAckermannDatabase.h>

class OgnROS1SubscribeAckermann : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1SubscribeAckermannDatabase::sInternalState<OgnROS1SubscribeAckermann>(nodeObj);
    // }

    static bool compute(OgnROS1SubscribeAckermannDatabase& db)
    {
        auto& state = db.internalState<OgnROS1SubscribeAckermann>();
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
            state.mCallback = [&state, &db](const ackermann_msgs::AckermannDriveStamped::ConstPtr& msg)
            { state.subCallback(msg, db); };

            state.mSubscriber =
                std::make_unique<ros::Subscriber>(state.mNodeHandle->subscribe<ackermann_msgs::AckermannDriveStamped>(
                    topicName, db.inputs.queueSize(), state.mCallback));
            return true;
        }

        return true;
    }

    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1SubscribeAckermannDatabase::sInternalState<OgnROS1SubscribeAckermann>(nodeObj);
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

    void subCallback(const ackermann_msgs::AckermannDriveStamped::ConstPtr& msg, OgnROS1SubscribeAckermannDatabase& db)
    {
        auto& frameId = db.outputs.frameId();
        auto& timeStamp = db.outputs.timeStamp();
        auto& steeringAngle = db.outputs.steeringAngle();
        auto& steeringAngleVelocity = db.outputs.steeringAngleVelocity();
        auto& speed = db.outputs.speed();
        auto& acceleration = db.outputs.acceleration();
        auto& jerk = db.outputs.jerk();

        frameId = msg->header.frame_id;
        timeStamp = msg->header.stamp.toSec();
        steeringAngle = msg->drive.steering_angle;
        steeringAngleVelocity = msg->drive.steering_angle_velocity;
        speed = msg->drive.speed;
        acceleration = msg->drive.acceleration;
        jerk = msg->drive.jerk;


        db.outputs.execOut() = kExecutionAttributeStateEnabled;
    }


private:
    std::unique_ptr<ros::Subscriber> mSubscriber;
    std::function<void(const ackermann_msgs::AckermannDriveStamped::ConstPtr&)> mCallback;
};

REGISTER_OGN_NODE()
