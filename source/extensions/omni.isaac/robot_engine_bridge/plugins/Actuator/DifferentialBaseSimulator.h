#pragma once
#include "../Core/IsaacComponent.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>

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
class DifferentialBaseSimulator : public IsaacComponent
{
public:
    DifferentialBaseSimulator(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr);
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
    void getWheelDesireSpeed(const pxr::GfVec2d& mCommandedSpeed);

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
    pxr::GfVec2d mLastAcceleration;
    // stored latest measured speed for calculating acceleration
    pxr::GfVec2d mLastSpeed;
    pxr::GfVec2d mCommandedSpeed;
    pxr::GfVec2d mWheelCurrentSpeed = pxr::GfVec2d(0, 0);
    pxr::GfVec2d mWheelDesiredSpeed = pxr::GfVec2d(0, 0);

    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Handles to the left and right wheels
    omni::isaac::dynamic_control::DcHandle mWheelFLHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    omni::isaac::dynamic_control::DcHandle mWheelFRHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    /// Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mChassisHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    // half length between FL and FR wheel
    float mWheelBase;
    bool mZUp = true;
    float mLastCommandTime;
    bool mBrakeRequested;
    double mUnitScale;

    /// The two driving wheels of carter.
    pxr::UsdPrim mWheelFL;
    pxr::UsdPrim mWheelFR;

    // The two joints driving the wheels
    pxr::UsdPrim mWheelFLJoint;
    pxr::UsdPrim mWheelFRJoint;


    /// The name of the channel on which commands are received
    std::string mInputComponent = "input";
    std::string mCommandChannelName = "base_command";

    /// The name of the channel on which state informations is published
    std::string mOutputComponent = "output";
    std::string mStateChannelName = "base_state";

    /// The front of the robot
    pxr::GfVec3d mRobotFront = pxr::GfVec3d(1.0, 0.0, 0.0);

    /// The maximal allowed linear and angular speed
    pxr::GfVec2d mMaximumSpeed = pxr::GfVec2d(3.0f, 1.5f);

    /// The maximum allowed time duration which the robot will continue with the last sent speed
    /// command in the absence of speed commands.
    float mMaximumTimeWithoutCommand = 0.2f;

    /// The maximal motorTorque apply to the driving wheels.
    /// This determines the maximum acceleration.
    float mMaxMotorTorque = 10.0f;

    /// Whether to use a proportional driver (true) or always apply mMaxMotorTorque (false)
    bool mUseProprotionalDriver = true;

    /// Proportional controller gain
    float mProportionalGain = 100.0f;

    /// brakeTorque applied when braking is requested
    float mBrakeTorque = 100.0f;

    /// A smoothing factor for the estimated acceleration. Smoothing the acceleration is important
    /// as acceleration is estimated via finite differences and can be very noisy. The higher the
    /// value the more smoothing will be applied. If set to 0 smoothing will not be used.
    float mAccelerationSmoothing = 1.0f;
};
}
}
}
