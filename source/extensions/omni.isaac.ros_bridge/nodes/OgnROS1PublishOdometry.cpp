// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "nav_msgs/Odometry.h"

#include <OgnROS1PublishOdometryDatabase.h>
#include <RosNode.h>


class OgnROS1PublishOdometry : public RosNode
{
public:
    // static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    // {
    //     auto& state = OgnROS1PublishOdometryDatabase::sPerInstanceState<OgnROS1PublishOdometry>(nodeObj, instanceId);
    // }

    static bool compute(OgnROS1PublishOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnROS1PublishOdometry>();

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

            state.mZUp = UsdGeomGetStageUpAxis(stage) == "Z" ? true : false;
            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            auto& robotFrontVec = db.inputs.robotFront();

            state.mRobotFront = pxr::GfVec3f(robotFrontVec[0], robotFrontVec[1], robotFrontVec[2]);

            state.mRobotFront = pxr::GfGetNormalized(state.mRobotFront, 1.0f);

            if (state.mZUp)
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 0.0, 1.0), state.mRobotFront);
            }
            else
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 1.0, 0.0), state.mRobotFront);
            }

            // Setup ROS odom publisher
            const std::string& topicName = db.inputs.topicName();

            if (!validateTopic(topicName))
            {
                return false;
            }

            state.mPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<nav_msgs::Odometry>(topicName, db.inputs.queueSize()));


            state.mOdomFrameId = db.inputs.odomFrameId();
            state.mChassisFrameId = db.inputs.chassisFrameId();

            addFramePrefix(db.inputs.nodeNamespace(), state.mOdomFrameId);
            addFramePrefix(db.inputs.nodeNamespace(), state.mChassisFrameId);

            return true;
        }

        state.publishOdom(db);

        return true;
    }


    void publishOdom(OgnROS1PublishOdometryDatabase& db)
    {
        nav_msgs::Odometry odomMsg;
        odomMsg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            odomMsg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS Odom messages");
        }

        odomMsg.header.frame_id = mOdomFrameId;
        odomMsg.child_frame_id = mChassisFrameId;

        auto& linVel = db.inputs.linearVelocity();
        float measuredSpeedFront = pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), mRobotFront) * mUnitScale;

        float measuredSpeedSide = pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), mRobotSide) * mUnitScale;

        auto& angVel = db.inputs.angularVelocity();

        // odometry messages
        odomMsg.twist.twist.linear.x = measuredSpeedFront;
        odomMsg.twist.twist.linear.y = measuredSpeedSide;

        if (mZUp)
        {
            odomMsg.twist.twist.angular.z = angVel[2]; // Get Z component of angular velocity
        }
        else
        {
            odomMsg.twist.twist.angular.y = angVel[1]; // Get Y component of angular velocity
        }

        auto& position = db.inputs.position();

        odomMsg.pose.pose.position.x = position[0];
        odomMsg.pose.pose.position.y = position[1];
        odomMsg.pose.pose.position.z = position[2];

        auto& orientation = db.inputs.orientation();
        odomMsg.pose.pose.orientation.x = orientation.GetImaginary()[0];
        odomMsg.pose.pose.orientation.y = orientation.GetImaginary()[1];
        odomMsg.pose.pose.orientation.z = orientation.GetImaginary()[2];
        odomMsg.pose.pose.orientation.w = orientation.GetReal();

        mPublisher->publish(odomMsg);
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS1PublishOdometryDatabase::sPerInstanceState<OgnROS1PublishOdometry>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mPublisher.reset(); // Publisher should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mPublisher;

    double mUnitScale;
    bool mZUp = true;

    // The front of the robot
    pxr::GfVec3f mRobotFront = pxr::GfVec3f(1.0, 0.0, 0.0);

    pxr::GfVec3f mRobotSide = pxr::GfVec3f(0.0, 1.0, 0.0);

    pxr::GfVec3f mStageup = pxr::GfVec3f(0.0, 0.0, 1.0);

    std::string mOdomFrameId = "odom";
    std::string mChassisFrameId = "base_link";
};

REGISTER_OGN_NODE()
