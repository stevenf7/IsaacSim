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

#include "nav_msgs/Odometry.h"
#include "tf2_msgs/TFMessage.h"

#include <carb/flatcache/FlatCache.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/ros/RosNode.h>
#include <omni/isaac/utils/Conversions.h>

#include <OgnROS1PublishOdometryDatabase.h>


using omni::isaac::utils::conversions::asGfRotation;
using omni::isaac::utils::conversions::asGfVec3d;

class OgnROS1PublishOdometry : public RosNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishOdometryDatabase::sInternalState<OgnROS1PublishOdometry>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnROS1PublishOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnROS1PublishOdometry>();

        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(db.inputs.nodeNamespace()))
        {

            return false;
        }

        // Either publisher was not valid, create a new one
        if (!state.mOdomPublisher || !state.mTfPublisher)
        {
            state.resetPublishers();

            const char* chassisPrimPath = db.inputs.chassisPrim.path();

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            // Checking we have a valid articulation
            if (state.mDynamicControlPtr->peekObjectType(chassisPrimPath) ==
                omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.mArticulationHandle = state.mDynamicControlPtr->getArticulation(chassisPrimPath);
            }
            else
            {
                db.logError("chassisPrim is not a valid articulation");
                return false;
            }

            if (!state.mArticulationHandle)
            {
                db.logError("Articulation not found for chassisPrim");
                return false;
            }

            state.mChassisHandle = state.mDynamicControlPtr->getArticulationRootBody(state.mArticulationHandle);


            state.mZUp = UsdGeomGetStageUpAxis(stage) == "Z" ? true : false;
            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            auto& robotFrontVec = db.inputs.robotFront();

            state.mRobotFront = pxr::GfVec3f(robotFrontVec[0], robotFrontVec[1], robotFrontVec[2]);


            // get starting pose in the world frame
            state.mStartingPose = state.mDynamicControlPtr->getRigidBodyPose(state.mChassisHandle);


            // Setup ROS odom publisher
            const std::string& odomTopicName = db.inputs.odomTopicName();

            if (!validateTopic(odomTopicName))
            {
                return false;
            }

            state.mOdomPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<nav_msgs::Odometry>(odomTopicName, db.inputs.queueSize()));


            // Setup ROS TF publisher
            const std::string& tfTopicName = db.inputs.tfTopicName();

            if (!validateTopic(tfTopicName))
            {
                return false;
            }

            state.mTfPublisher = std::make_unique<ros::Publisher>(
                state.mNodeHandle->advertise<tf2_msgs::TFMessage>(tfTopicName, db.inputs.queueSize()));


            state.mOdomFrameId = db.inputs.odomFrameId();
            state.mChassisFrameId = db.inputs.chassisFrameId();

            addFramePrefix(db.inputs.nodeNamespace(), state.mOdomFrameId);
            addFramePrefix(db.inputs.nodeNamespace(), state.mChassisFrameId);

            return true;
        }

        state.publishOdom(db);
        state.publishTF(db);

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

        auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);

        auto chassisLocalLinVel = mDynamicControlPtr->getRigidBodyLocalLinearVelocity(mChassisHandle);
        auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mChassisHandle);


        // calculate odom reading from starting position
        pxr::GfVec3d globalTranslation =
            pxr::GfVec3d(chassisPose.p.x - mStartingPose.p.x, chassisPose.p.y - mStartingPose.p.y,
                         chassisPose.p.z - mStartingPose.p.z);
        pxr::GfVec3d odomTranslation =
            (asGfRotation(mStartingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;
        pxr::GfQuatd odomRotation = (asGfRotation(chassisPose.r) * asGfRotation(mStartingPose.r).GetInverse()).GetQuat();

        // velocity in chassis frame
        float measuredSpeedFront = pxr::GfDot(asGfVec3d(chassisLocalLinVel), mRobotFront) * mUnitScale;

        // odometry messages
        odomMsg.twist.twist.linear.x = measuredSpeedFront;
        if (mZUp)
        {
            odomMsg.twist.twist.angular.z = chassisAngVel.z;
        }
        else
        {
            odomMsg.twist.twist.angular.y = chassisAngVel.y;
        }

        odomMsg.pose.pose.position.x = odomTranslation[0];
        odomMsg.pose.pose.position.y = odomTranslation[1];
        odomMsg.pose.pose.position.z = odomTranslation[2];
        odomMsg.pose.pose.orientation.w = odomRotation.GetReal();
        odomMsg.pose.pose.orientation.x = odomRotation.GetImaginary()[0];
        odomMsg.pose.pose.orientation.y = odomRotation.GetImaginary()[1];
        odomMsg.pose.pose.orientation.z = odomRotation.GetImaginary()[2];

        mOdomPublisher->publish(odomMsg);
    }

    void publishTF(OgnROS1PublishOdometryDatabase& db)
    {
        tf2_msgs::TFMessage tfMsg;
        geometry_msgs::TransformStamped msg;
        msg.header.seq = 0;

        if (db.inputs.timeStamp() >= 0.0)
        {
            msg.header.stamp.fromSec(db.inputs.timeStamp());
        }
        else
        {
            db.logWarning("Timestamp is invalid. Timestamp will be neglected for all published ROS Odom TF messages");
        }

        msg.header.frame_id = mOdomFrameId;
        msg.child_frame_id = mChassisFrameId;

        auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);
        // calculate relative pose from starting pose
        pxr::GfVec3d globalTranslation =
            pxr::GfVec3d(chassisPose.p.x - mStartingPose.p.x, chassisPose.p.y - mStartingPose.p.y,
                         chassisPose.p.z - mStartingPose.p.z);
        pxr::GfVec3d odomTranslation =
            (asGfRotation(mStartingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;
        pxr::GfQuatd odomRotation = (asGfRotation(chassisPose.r) * asGfRotation(mStartingPose.r).GetInverse()).GetQuat();

        msg.transform.translation.x = odomTranslation[0];
        msg.transform.translation.y = odomTranslation[1];
        msg.transform.translation.z = odomTranslation[2];
        msg.transform.rotation.w = odomRotation.GetReal();
        msg.transform.rotation.x = odomRotation.GetImaginary()[0];
        msg.transform.rotation.y = odomRotation.GetImaginary()[1];
        msg.transform.rotation.z = odomRotation.GetImaginary()[2];

        tfMsg.transforms.push_back(msg);
        mTfPublisher->publish(tfMsg);
    }

    void resetPublishers()
    {
        mOdomPublisher.reset();
        mTfPublisher.reset();
    }

    virtual void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS1PublishOdometryDatabase::sInternalState<OgnROS1PublishOdometry>(nodeObj);
        state.reset();
    }

    virtual void reset()
    {
        resetPublishers(); // Publishers should be reset before we reset the handle.
        RosNode::reset();
    }


private:
    std::unique_ptr<ros::Publisher> mOdomPublisher;
    std::unique_ptr<ros::Publisher> mTfPublisher;

    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    // Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mChassisHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    // pose of the robot at start
    omni::isaac::dynamic_control::DcTransform mStartingPose;

    bool mZUp = true;

    // The front of the robot
    pxr::GfVec3f mRobotFront = pxr::GfVec3f(1.0, 0.0, 0.0);
    double mUnitScale;

    std::string mOdomFrameId = "odom";
    std::string mChassisFrameId = "base_link";
};

REGISTER_OGN_NODE()
