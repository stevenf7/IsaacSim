// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/dynamic_control/DynamicControlTypes.h>

namespace omni
{
namespace isaac
{
namespace utils
{


using namespace omni::isaac::dynamic_control;


/**
 * @brief Properties for Surface Gripper (suction-style gripper)
 *
 */
struct SurfaceGripperProperties
{
    std::string d6JointPath; //! USD path of the joint
    std::string parentPath; //! parent body that  contains the joint
    DcTransform offset; //! offset from parent body to joint point of contact in vacuum pressure
    float gripThreshold; //!  How far from an object it allows the gripper to lock in. Object will be pulled in this
                         //!  distance when gripper is closed
    float forceLimit; //! gripper breaking force
    float torqueLimit; //! torque breaking force
    float bendAngle; //! maximum bend angle for the gripper
    float stiffness; //! Gripper Stiffness
    float damping; //! Gripper damping
    bool disableGravity; //! flag to disable gravity of selected item to compensate for object's mass on robotic
                         //! controllers
};

/**
 * @brief Surface Gripper (suction-cup style gripper)
 *
 */
class SurfaceGripper
{

public:
    /**
     * @brief Creates a Surface Gripper
     *
     * @param[in] dc.
     * @param[in] props.
     */
    SurfaceGripper(DynamicControl* dc);

    /**
     * @brief Destroy the Surface Gripper object
     *
     */
    ~SurfaceGripper();

    /**
     * @brief Initialize joint and register with DC extension
     *
     * @param props
     * @return true
     * @return false
     */
    bool(initialize)(const SurfaceGripperProperties& props);

    /**
     * @brief returns whether the joint is closed
     * @return bool.
     */
    bool isClosed();

    void update();

    /**
     * @brief closes the Surface Gripper, if any object is closer than the lock threshold
     *
     * @return true when an object is close and joint is effectively closed
     * @return false when no object is near the gripper. joint is not closed.
     */
    bool close();


    /**
     * @brief opens the Surface Gripper, releasing the object
     *
     * @return true
     */
    bool open();

private:
    DynamicControl* mDc = nullptr;
    DcHandle mJointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    DcD6JointProperties mJointProperties;
    SurfaceGripperProperties mProps;

    bool mIsClosed;
    bool mIsInitialized;
};

} // omni
} // isaac
} // utils
