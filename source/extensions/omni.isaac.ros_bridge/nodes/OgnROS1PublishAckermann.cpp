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

#include "ackermann_msgs/AckermannDriveStamped.h"

#include <omni/isaac/ros/RosNode.h>

#include <OgnROS1PublishAckermannDatabase.h>


class OgnROS1PublishAckermann : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1PublishAckermannDatabase::sInternalState<OgnROS1PublishAckermann>(nodeObj);
    // }

    static bool compute(OgnROS1PublishAckermannDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnROS1PublishAckermann>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {

            // Setup ROS AckermannDriveStamped publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<ackermann_msgs::AckermannDriveStamped>(topicName, db.inputs.queueSize()));


            state.mFrameId = db.inputs.frameId();

            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        state.publishAckermannDriveStamped(db);

        return true;
    }


    void publishAckermannDriveStamped(OgnROS1PublishAckermannDatabase& db)
    {
        ackermann_msgs::AckermannDriveStamped msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning(
                "Timestamp is invalid. Timestamp will be neglected for all published ROS AckermannDriveStamped messages");
        }

        msg.header.frame_id = mFrameId;

        msg.drive.steering_angle = db.inputs.steeringAngle();
        msg.drive.steering_angle_velocity = db.inputs.steeringAngleVelocity();
        msg.drive.speed = db.inputs.speed();
        msg.drive.acceleration = db.inputs.acceleration();
        msg.drive.jerk = db.inputs.jerk();

        mPublisher->publish(msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishAckermannDatabase::sInternalState<OgnROS1PublishAckermann>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;
    std::string mFrameId = "";
};

REGISTER_OGN_NODE()
