#pragma once
#include "../Core/IsaacComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <robotEngineBridgeSchema/robotEngineHolonomicBase.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{

/**
 * @brief A simulated differential-base driver based on speed commands.
 *
 */
class HolonomicBaseSimulator : public IsaacComponent
{
public:
    HolonomicBaseSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
    /**
     * @brief The articulation for the robot might not be valid, so force update on start
     *
     */
    virtual void onStart();

    /**
     * @brief Get latest command message and publish ground truth data
     *
     */
    virtual void tick();
    /**
     * @brief Update the properties of this component based on any USD changes
     *
     */
    virtual void onComponentChange();


private:
    /**
     * @brief Compute the desired wheel velocities from the command speed
     *
     * @param mCommandedSpeed
     */
    pxr::GfVec3d getWheelDesireSpeed(const pxr::GfVec3d& mCommandedSpeed);

    /**
     * @brief Scales target wheel velocity
     *
     * @param target
     * @return float
     */
    float getVelocity(float target);

    /**
     * @brief
     *
     * @param dt
     * @param lambda
     * @return float
     */
    float timedSmoothingFactor(float dt, float lambda);

    // The last acceleration used for acceleration smoothing.
    pxr::GfVec3d mLastAcceleration = pxr::GfVec3d(0);
    // stored latest measured speed for calculating acceleration
    pxr::GfVec3d mLastSpeed = pxr::GfVec3d(0);
    pxr::GfVec3d mCommandedSpeed = pxr::GfVec3d(0);
    pxr::GfVec3d mWheelDesiredSpeed = pxr::GfVec3d(0);

    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Handles to the left and right wheels
    omni::isaac::dynamic_control::DcHandle mWheel1Handle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mWheel2Handle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mWheel3Handle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mChassisHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    // half length between FL and FR wheel
    float mWheelBase = 0.04;
    float mWheelRadius = 0.125;
    bool mZUp = true;
    float mLastCommandTime;
    bool mBrakeRequested = false;
    double mUnitScale;

    /// The three driving wheels of base.
    pxr::UsdPrim mWheel1;
    pxr::UsdPrim mWheel2;
    pxr::UsdPrim mWheel3;

    // The two joints driving the wheels
    pxr::UsdPrim mWheel1Joint;
    pxr::UsdPrim mWheel2Joint;
    pxr::UsdPrim mWheel3Joint;


    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mCommandChannelName = "base_command";

    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mStateChannelName = "base_state";

    // The front of the robot
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
};
}
}
}
