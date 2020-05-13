// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include "Math.h"

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/dynamic_control/DynamicControlTypes.h>

namespace omni
{
namespace isaac
{
namespace utils
{


using namespace omni::isaac::dynamic_control;
using namespace omni::isaac::utils::math;


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
    SurfaceGripper(DynamicControl* dc)
    {
        mDc = dc;

        mJointProperties.body0 = 0;
        mJointProperties.axes = kDcAxisNone;
        mJointProperties.jointType = DcJointType::eSpherical;
        mJointProperties.stiffness = 0;
        mJointProperties.damping = 1.0e5f;
        mJointProperties.forceLimit = 0;
        mJointProperties.torqueLimit = 0;

        mIsClosed = false;
        mIsInitialized = false;
    }

    /**
     * @brief Destroy the Surface Gripper object
     *
     */
    ~SurfaceGripper()
    {
        if (mJointHandle)
        {
            mDc->destroyD6Joint(mJointHandle);
        }
    }

    /**
     * @brief Initialize joint and register with DC extension
     *
     * @param props
     * @return true
     * @return false
     */
    bool initialize(const SurfaceGripperProperties& props)
    {
        mProps = props;

        if (mJointHandle)
        {
            mDc->destroyD6Joint(mJointHandle);
            mJointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
        }
        mJointHandle = mDc->getD6Joint(mProps.d6JointPath.c_str());
        if (!mJointHandle)
        {
            mIsInitialized = false;
            return false;
        }
        mIsInitialized = true;
        return true;
    }

    /**
     * @brief returns whether the joint is closed
     * @return bool.
     */
    inline bool isClosed()
    {
        return mIsClosed;
    }

    void update()
    {
        if (isClosed())
        {
            if (mDc->getD6JointConstraintIsBroken(mJointHandle))
            {
                CARB_LOG_WARN("Gripper Constraint is Broken");
                open();
            }
        }
    }

    /**
     * @brief closes the Surface Gripper, if any object is closer than the lock threshold
     *
     * @return true when an object is close and joint is effectively closed
     * @return false when no object is near the gripper. joint is not closed.
     */
    bool close()
    {
        if (!mIsInitialized)
        {
            CARB_LOG_ERROR("Please call initialize before closing");
            return false;
        }
        if (mJointHandle)
        {
            DcHandle rb_0 = mDc->getRigidBody(mProps.parentPath.c_str());
            if (!rb_0)
            {
                CARB_LOG_ERROR("Rarent rigid Body handle not valid");
                return false;
            }
            DcTransform t_0 = mDc->getRigidBodyPose(rb_0);
            DcTransform threshOffset;
            threshOffset.p.x = mProps.gripThreshold;
            DcTransform _t_0 = (t_0 * mProps.offset);
            carb::Float3 p = _t_0.p;
            // _t_0 = _t_0 * threshOffset;//Disabling until we get soft meshes for grippers
            carb::Float3 dir = getBasisVectorX(t_0.r);
            DcRayCastResult hit = mDc->rayCast(p, dir, mProps.gripThreshold);

            if (hit.hit)
            {
                DcTransform t_1 = inverse(mDc->getRigidBodyPose(hit.rigidBody)) * _t_0;

                mJointProperties.body0 = rb_0;
                mJointProperties.body1 = hit.rigidBody;
                mDc->setRigidBodyDisableGravity(mJointProperties.body1, true);
                mJointProperties.pose0 = mProps.offset;
                mJointProperties.pose1 = t_1;
                mJointProperties.axes = kDcAxisAll;
                memset(mJointProperties.hasLimits, 0, sizeof(bool) * 6);
                mJointProperties.hasLimits[4] = true;
                mJointProperties.hasLimits[5] = true;
                mJointProperties.stiffness = mProps.stiffness;
                mJointProperties.damping = mProps.damping;
                mJointProperties.limitStiffness = mProps.stiffness;
                mJointProperties.limitDamping = mProps.damping;
                mJointProperties.softLimit = true;
                mJointProperties.lowerLimit = mProps.bendAngle;
                mJointProperties.upperLimit = mProps.bendAngle;
                mJointProperties.forceLimit = mProps.forceLimit;
                mJointProperties.torqueLimit = mProps.torqueLimit;
                mDc->setD6JointProperties(mJointHandle, &mJointProperties);
                mIsClosed = true;
            }
            return hit.hit;
        }
        return false;
    }


    /**
     * @brief opens the Surface Gripper, releasing the object
     *
     * @return true
     */
    bool open()
    {
        if (!mIsInitialized)
        {
            CARB_LOG_ERROR("Please call initialize before opening");
            return false;
        }
        if (mIsClosed && mJointHandle)
        {
            mJointProperties.axes = kDcAxisNone;
            mJointProperties.body0 = 0;
            mDc->setRigidBodyDisableGravity(mJointProperties.body1, false);
            mJointProperties.body1 = 0;
            mJointProperties.forceLimit = 0;
            mJointProperties.torqueLimit = 0;
            mDc->setD6JointProperties(mJointHandle, &mJointProperties);
            mIsClosed = false;
            return true;
        }
        return false;
    }

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
