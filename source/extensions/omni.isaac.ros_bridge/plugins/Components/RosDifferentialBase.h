// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

// #include "RosCallback.h"
#include "../Core/IsaacComponent.h"
#include "../Core/RosNode.h"
#include "geometry_msgs/Twist.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <rosBridgeSchema/rosDifferentialBase.h>

namespace omni
{
namespace isaac
{
namespace ros_bridge
{


class RosDifferentialBase : public IsaacComponent
{

public:
    RosDifferentialBase(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    // Virtual so that it can be called when object is destroyed
    virtual ~RosDifferentialBase();
    virtual void initialize(RosNode* rosNode,
                            const pxr::RosBridgeSchemaRosBridgeComponent& prim,
                            pxr::UsdStageWeakPtr stage);

    virtual void onComponentChange();
    void pubCallback(ros::Publisher* pub);
    void tfPubCallback(ros::Publisher* pub);
    void subCallback(const geometry_msgs::Twist::ConstPtr& msg);

private:
    /**
     * @brief Compute the desired wheel velocities from the command speed
     *
     * @param mCommandedSpeed
     */
    void getWheelDesireSpeed(const pxr::GfVec2d& mCommandedSpeed);

    /**
     * @brief
     *
     * @param dt
     * @param lambda
     * @return float
     */
    float timedSmoothingFactor(float dt, float lambda);

    std::string mStatePubTopic = "/odom";
    std::string mTfPubTopic = "/tf";
    std::string mCommandSubTopic = "/cmd_vel";
    int mQueueSize = 0;
    std::string mOdomFrameId = "odom";
    std::string mBaseFrameId = "base_link";

    // The last acceleration used for acceleration smoothing.
    pxr::GfVec2d mLastAcceleration = pxr::GfVec2d(0);
    // stored latest measured speed for calculating acceleration
    pxr::GfVec2d mLastSpeed = pxr::GfVec2d(0);
    pxr::GfVec2d mCommandedSpeed = pxr::GfVec2d(0);
    pxr::GfVec2d mWheelCurrentSpeed = pxr::GfVec2d(0, 0);
    pxr::GfVec2d mWheelDesiredSpeed = pxr::GfVec2d(0, 0);

    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Handles to the left and right wheels
    omni::isaac::dynamic_control::DcHandle mWheelFLHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mWheelFRHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mChassisHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;


    bool mZUp = true;
    float mLastCommandTime;
    bool mBrakeRequested = false;
    double mUnitScale;

    /// The two driving wheels of carter.
    pxr::UsdPrim mWheelFL;
    pxr::UsdPrim mWheelFR;

    // The two joints driving the wheels
    pxr::UsdPrim mWheelFLJoint;
    pxr::UsdPrim mWheelFRJoint;

    /// The front of the robot
    pxr::GfVec3f mRobotFront = pxr::GfVec3f(1.0, 0.0, 0.0);

    /// The maximal allowed linear and angular speed
    pxr::GfVec2f mMaximumSpeed = pxr::GfVec2f(3.0f, 1.5f);

    /// The maximum allowed time duration which the robot will continue with the last sent speed
    /// command in the absence of speed commands.
    float mMaximumTimeWithoutCommand = 0.2f;

    /// A smoothing factor for the estimated acceleration. Smoothing the acceleration is important
    /// as acceleration is estimated via finite differences and can be very noisy. The higher the
    /// value the more smoothing will be applied. If set to 0 smoothing will not be used.
    float mAccelerationSmoothing = 1.0f;

    /// Wheel radius to scale linear velocity by
    float mWheelRadius = 1.0f;

    /// half length between FL and FR wheel
    float mWheelBase;
};
}
}
}
