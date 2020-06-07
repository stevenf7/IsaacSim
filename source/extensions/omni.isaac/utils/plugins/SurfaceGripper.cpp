// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <omni/isaac/utils/Math.h>
#include <omni/isaac/utils/SurfaceGripper.h>
#include <carb/logging/Log.h>

namespace omni
{
namespace isaac
{
namespace utils
{

using namespace omni::isaac::dynamic_control;
using namespace omni::isaac::utils::math;

SurfaceGripper::SurfaceGripper(DynamicControl* dc)
{
    mDc = dc;

    mJointProperties.body0 = 0;
    mJointProperties.axes = kDcAxisNone;
    mJointProperties.jointType = DcJointType::eSpherical;
    mJointProperties.stiffness = 0;
    mJointProperties.damping = 1.0e5f;
    mJointProperties.forceLimit = 0;
    mJointProperties.torqueLimit = 0;
    for (int i = 0; i < 6; ++i)
    {
        mJointProperties.hasLimits[i] = false;
    }

    mIsClosed = false;
    mIsInitialized = false;

    mJointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
}

SurfaceGripper::~SurfaceGripper()
{
    // Make sure that DC is valid before we destroy in case Dc was released already.
    if (mJointHandle && mDc)
    {
        mDc->destroyD6Joint(mJointHandle);
    }
}

bool SurfaceGripper::initialize(const SurfaceGripperProperties& props)
{
    mProps = props;

    if (mJointHandle)
    {
        mDc->destroyD6Joint(mJointHandle);
        mJointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    }
    mIsInitialized = true;
    return true;
}

bool SurfaceGripper::isClosed()
{
    return mIsClosed;
}

void SurfaceGripper::update()
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

bool SurfaceGripper::close()
{
    if (!mIsInitialized)
    {
        CARB_LOG_ERROR("Please call initialize before closing");
        return false;
    }
    else
    {
        DcHandle rb_0 = mDc->getRigidBody(mProps.parentPath.c_str());
        if (!rb_0)
        {
            CARB_LOG_ERROR("Parent rigid Body handle not valid");
            return false;
        }
        DcTransform t_0 = mDc->getRigidBodyPose(rb_0);
        DcTransform _t_0 = (t_0 * mProps.offset);
        carb::Float3 p = _t_0.p;
        carb::Float3 dir = getBasisVectorX(_t_0.r);
        // CARB_LOG_WARN("gripper position: (%f, %f, %f)", p.x, p.y, p.z);
        // CARB_LOG_WARN("gripper direction: (%f, %f, %f)", dir.x, dir.y, dir.z);
        // DcTransform threshOffset;
        // threshOffset.p.x = mProps.gripThreshold;
        // _t_0 = _t_0 * threshOffset; //Disabling until we get soft meshes for grippers
        DcRayCastResult hit = mDc->rayCast(p, dir, mProps.gripThreshold);

        if (hit.hit)
        {
            DcTransform t_1 = inverse(mDc->getRigidBodyPose(hit.rigidBody)) * _t_0;

            mJointProperties.body0 = rb_0;
            mJointProperties.body1 = hit.rigidBody;
            mDc->setRigidBodyDisableGravity(mJointProperties.body1, mProps.disableGravity);
            mJointProperties.pose0 = mProps.offset;
            mJointProperties.pose1 = t_1;
            mJointProperties.axes = kDcAxisAll;


            mJointProperties.stiffness = mProps.stiffness;
            mJointProperties.damping = mProps.damping;
            mJointProperties.limitStiffness = mProps.stiffness;
            mJointProperties.limitDamping = mProps.damping;
            if (mProps.bendAngle > 0)
            {
                mJointProperties.softLimit = true;
                mJointProperties.lowerLimit = mProps.bendAngle;
                mJointProperties.upperLimit = mProps.bendAngle;
                mJointProperties.jointType = DcJointType::eSpherical;
                mJointProperties.hasLimits[4] = true;
                mJointProperties.hasLimits[5] = true;
            }
            else
            {
                mJointProperties.hasLimits[4] = false;
                mJointProperties.hasLimits[5] = false;
                mJointProperties.softLimit = false;
                mJointProperties.lowerLimit = 0;
                mJointProperties.upperLimit = 0;
                mJointProperties.jointType = DcJointType::eFixed;
            }


            mJointProperties.forceLimit = mProps.forceLimit;
            mJointProperties.torqueLimit = mProps.torqueLimit;
            if (!mJointHandle)
            {
                std::string s(mProps.d6JointPath);
                mJointProperties.name = (char*)(s).c_str();
                mJointHandle = mDc->createD6Joint(&mJointProperties);
            }
            mDc->setD6JointProperties(mJointHandle, &mJointProperties);

            mIsClosed = true;
        }
        return hit.hit;
    }
    return false;
}

bool SurfaceGripper::open()
{
    if (!mIsInitialized)
    {
        CARB_LOG_ERROR("Please call initialize before opening");
        return false;
    }
    if (mIsClosed)
    {
        mDc->wakeUpRigidBody(mJointProperties.body1);
        mDc->setRigidBodyDisableGravity(mJointProperties.body1, false);

        mDc->destroyD6Joint(mJointHandle);
        mJointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

        mIsClosed = false;
        return true;
    }
    return false;
}

} // omni
} // isaac
} // utils
