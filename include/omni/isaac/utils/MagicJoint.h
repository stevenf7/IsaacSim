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
 * @brief Properties for Magic joint (suction-style gripper)
 *
 */
struct MagicJointProperties
{
    std::string d6JointPath; //! USD path of the joint
    std::string parentPath; //! parent body that  contains the joint
    DcTransform offset; //! offset from parent body to joint point of contact
    float gripThreshold; //!  How far from an object it allows the gripper to lock in
    float forceLimit; //! gripper breaking force
    float torqueLimit; //! torque breaking force
};

/**
 * @brief Magic Joint (suction-cup style gripper)
 *
 */
class MagicJoint
{

public:
    /**
     * @brief Creates a magic joint
     *
     * @param[in] dc.
     * @param[in] props.
     */
    MagicJoint(DynamicControl* dc)
    {
        mDc = dc;

        mJointProperties.body0 = 0;
        mJointProperties.axes = kDcAxisNone;
        mJointProperties.stiffness = 0;
        mJointProperties.damping = 1.0e5f;
        mJointProperties.forceLimit = 0;
        mJointProperties.torqueLimit = 0;

        mIsClosed = false;
        mIsInitialized = false;
    }

    /**
     * @brief Destroy the Magic Joint object
     *
     */
    ~MagicJoint()
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
    bool initialize(const MagicJointProperties& props)
    {
        mProps = props;

        // CARB_LOG_WARN("Break Force/torque: %f %f", mProps.forceLimit, mProps.torqueLimit);
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
     * @brief closes the magic joint, if any object is closer than the lock threshold
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
            carb::Float3 p = (t_0 * mProps.offset).p;
            carb::Float3 dir = getBasisVectorX(t_0.r);
            DcRayCastResult hit = mDc->rayCast(p, dir, mProps.gripThreshold);

            if (hit.hit)
            {
                DcTransform t_1 = inverse(mDc->getRigidBodyPose(hit.rigidBody)) * t_0;

                mJointProperties.body0 = rb_0;
                mJointProperties.body1 = hit.rigidBody;
                mDc->setRigidBodyDisableGravity(mJointProperties.body1, true);
                mJointProperties.pose1 = t_1;
                mJointProperties.axes = kDcAxisAll;
                mJointProperties.stiffness = 1.e8f;
                mJointProperties.damping = 1.e6f;
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
     * @brief opens the magic joint, releasing the object
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
    MagicJointProperties mProps;

    bool mIsClosed;
    bool mIsInitialized;
};

} // omni
} // isaac
} // utils
