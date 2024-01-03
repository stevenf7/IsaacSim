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

#include "sensor_msgs/Imu.h"

#include <OgnROS1PublishImuDatabase.h>
#include <RosNode.h>


class OgnROS1PublishImu : public RosNode
{
public:
    // static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    // {
    //     auto& state = OgnROS1PublishImuDatabase::sInternalState<OgnROS1PublishImu>(nodeObj);
    // }

    static bool compute(OgnROS1PublishImuDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnROS1PublishImu>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {
            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mPublisher)
        {

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            // Setup ROS IMU publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<sensor_msgs::Imu>(topicName, db.inputs.queueSize()));


            state.mFrameId = db.inputs.frameId();

            addFramePrefix(db.inputs.nodeNamespace(), state.mFrameId);

            return true;
        }

        state.publishImu(db);

        return true;
    }


    void publishImu(OgnROS1PublishImuDatabase& db)
    {
        sensor_msgs::Imu msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS IMU messages");
        }

        msg.header.frame_id = mFrameId;

        if (!db.inputs.publishLinearAcceleration())
        {
            msg.linear_acceleration_covariance[0] = -1;
        }
        else
        {
            auto& linAccel = db.inputs.linearAcceleration();
            msg.linear_acceleration.x = linAccel[0];
            msg.linear_acceleration.y = linAccel[1];
            msg.linear_acceleration.z = linAccel[2];
        }

        if (!db.inputs.publishAngularVelocity())
        {
            msg.angular_velocity_covariance[0] = -1;
        }
        else
        {
            auto& angVel = db.inputs.angularVelocity();
            msg.angular_velocity.x = angVel[0];
            msg.angular_velocity.y = angVel[1];
            msg.angular_velocity.z = angVel[2];
        }

        if (!db.inputs.publishOrientation())
        {
            msg.orientation_covariance[0] = -1;
        }
        else
        {
            auto& orientation = db.inputs.orientation();
            msg.orientation.x = orientation.GetImaginary()[0];
            msg.orientation.y = orientation.GetImaginary()[1];
            msg.orientation.z = orientation.GetImaginary()[2];
            msg.orientation.w = orientation.GetReal();
        }

        mPublisher->publish(msg);
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishImuDatabase::sInternalState<OgnROS1PublishImu>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;
    std::string mFrameId = "sim_imu";
};

REGISTER_OGN_NODE()
