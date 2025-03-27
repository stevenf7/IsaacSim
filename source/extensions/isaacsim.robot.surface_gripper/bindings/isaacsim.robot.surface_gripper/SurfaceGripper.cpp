// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.


// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "isaacsim/robot/surface_gripper/SurfaceGripper.h"

#include <carb/Interface.h>
#include <carb/logging/Log.h>

#include <omni/physx/IPhysx.h>

#include <DynamicControl.h>

namespace isaacsim::robot::surface_gripper
{

SurfaceGripper::SurfaceGripper()
{
    m_dc = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
    m_physxQuery = carb::getCachedInterface<omni::physx::IPhysxSceneQuery>();
    m_jointProperties.body0 = 0;
    m_jointProperties.axes = kDcAxisNone;
    m_jointProperties.jointType = DcJointType::eSpherical;
    m_jointProperties.stiffness = 0;
    m_jointProperties.damping = 1.0e5f;
    m_jointProperties.forceLimit = 0;
    m_jointProperties.torqueLimit = 0;

    for (int i = 0; i < 6; ++i)
    {
        m_jointProperties.hasLimits[i] = false;
    }

    m_closed = false;
    m_initialized = false;
    m_jointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
}

SurfaceGripper::~SurfaceGripper()
{
    if (m_jointHandle && m_dc)
    {
        m_dc->destroyD6Joint(m_jointHandle);
    }
}

bool SurfaceGripper::initialize(const SurfaceGripperProperties& props)
{
    m_props = props;
    if (m_jointHandle)
    {
        m_dc->destroyD6Joint(m_jointHandle);
        m_jointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    }
    m_initialized = true;
    return true;
}

bool SurfaceGripper::isClosed() const
{
    return m_closed;
}

bool SurfaceGripper::isAttemptingClose() const
{
    return m_attemptingClose;
}

void SurfaceGripper::update()
{
    if (isClosed())
    {
        if (m_dc->getD6JointConstraintIsBroken(m_jointHandle))
        {
            CARB_LOG_WARN("Gripper Constraint is Broken");
            open();
        }
    }
    else if (m_attemptingClose)
    {
        attemptClose();
    }
}

bool SurfaceGripper::close()
{
    if (!m_initialized)
    {
        CARB_LOG_ERROR("Please call initialize before closing");
        return false;
    }
    m_attemptingClose = true;
    return attemptClose();
}

bool SurfaceGripper::open()
{
    if (!m_initialized)
    {
        CARB_LOG_ERROR("Please call initialize before opening");
        return false;
    }

    m_attemptingClose = false;
    if (m_closed)
    {
        if (m_dc->isSimulating())
        {
            m_dc->wakeUpRigidBody(m_jointProperties.body1);
            m_dc->setRigidBodyDisableGravity(m_jointProperties.body1, false);
        }
        m_dc->destroyD6Joint(m_jointHandle);
        m_jointHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
        m_closed = false;
        return true;
    }
    return false;
}


/**
 * @brief Attempts closing the Surface Gripper, if any object is closer than the lock threshold
 *
 * @param additional_offset Offset adjustment for collision avoidance
 * @return true Found valid object to attach
 * @return false No valid object in range
 */
bool SurfaceGripper::attemptClose(float additionalOffset)
{
    DcHandle parentBody = m_dc->getRigidBody(m_props.parentPath.c_str());
    if (!parentBody)
    {
        CARB_LOG_ERROR("Parent rigid Body handle not valid for prim %s", m_props.parentPath.c_str());
        return false;
    }
    DcTransform parentTransform = m_dc->getRigidBodyPose(parentBody);
    DcTransform* offsetPtr = reinterpret_cast<DcTransform*>(&m_props.offset);
    DcTransform adjustedTransform = (parentTransform * (*offsetPtr));
    const carb::Float3 dir = getBasisVectorX(adjustedTransform.r);
    // CARB_LOG_INFO("gripper offset: (%f, %f, %f)", m_props.offset.p.x, m_props.offset.p.y, m_props.offset.p.z);
    // CARB_LOG_INFO(
    //     "gripper position: (%f, %f, %f)", adjustedTransform.p.x, adjustedTransform.p.y,
    //     adjustedTransform.p.z);
    // CARB_LOG_INFO("gripper direction: (%f, %f, %f)", dir.x, dir.y, dir.z);
    // DcTransform threshOffset;
    // threshOffset.p.x = m_props.gripThreshold;
    // _t_0 = _t_0 * threshOffset; //Disabling until we get soft meshes for grippers
    size_t remainingAttempts = 1000000;
    additionalOffset = 0.0f;
    omni::physx::RaycastHit result;
    bool hit = false;
    while (remainingAttempts)
    {
        remainingAttempts--;
        carb::Float3 rayStart = isaacsim::core::includes::math::operator+(adjustedTransform.p, dir* additionalOffset);
        hit = m_physxQuery->raycastClosest(rayStart, dir, m_props.gripThreshold, result, false);

        if (hit)
        {

            DcHandle targetBody = m_dc->getRigidBody(intToPath(result.rigidBody).GetString().c_str());
            if (targetBody == parentBody)
            {
                additionalOffset += 1.0e-3f;
                continue;
            }
            CARB_LOG_INFO("Gripping prim %s at distance %f with parent %s",
                          intToPath(result.rigidBody).GetString().c_str(), result.distance, m_props.parentPath.c_str());
            DcTransform targetTransform = inverse(m_dc->getRigidBodyPose(targetBody)) * adjustedTransform;

            m_jointProperties.body0 = parentBody;
            m_jointProperties.body1 = targetBody;
            m_dc->setRigidBodyDisableGravity(m_jointProperties.body1, m_props.disableGravity);
            DcTransform* offsetPtr = reinterpret_cast<DcTransform*>(&m_props.offset);
            m_jointProperties.pose0 = *offsetPtr;
            m_jointProperties.pose1 = targetTransform;
            m_jointProperties.axes = kDcAxisAll;


            m_jointProperties.stiffness = m_props.stiffness;
            m_jointProperties.damping = m_props.damping;
            m_jointProperties.limitStiffness = m_props.stiffness;
            m_jointProperties.limitDamping = m_props.damping;
            if (m_props.bendAngle > 0)
            {
                m_jointProperties.softLimit = true;
                m_jointProperties.lowerLimit = m_props.bendAngle;
                m_jointProperties.upperLimit = m_props.bendAngle;
                m_jointProperties.jointType = DcJointType::eSpherical;
                m_jointProperties.hasLimits[4] = true;
                m_jointProperties.hasLimits[5] = true;
            }
            else
            {
                m_jointProperties.hasLimits[4] = false;
                m_jointProperties.hasLimits[5] = false;
                m_jointProperties.softLimit = false;
                m_jointProperties.lowerLimit = 0;
                m_jointProperties.upperLimit = 0;
                m_jointProperties.jointType = DcJointType::eFixed;
            }


            m_jointProperties.forceLimit = m_props.forceLimit;
            m_jointProperties.torqueLimit = m_props.torqueLimit;
            if (!m_jointHandle)
            {
                std::string s(m_props.d6JointPath);
                m_jointProperties.name = const_cast<char*>(s.c_str());
                m_jointHandle = m_dc->createD6Joint(&m_jointProperties);
            }
            m_dc->setD6JointProperties(m_jointHandle, &m_jointProperties);

            m_closed = true;
        }
        break;
    }
    if (remainingAttempts == 0)
    {
        CARB_LOG_INFO("Raycast Failed");
    }
    if (additionalOffset)
    {
        CARB_LOG_WARN(
            "Surface Gripper is inside the parent Rigid body collider. please move it forward in the X offset direction by %f to avoid wasted computation",
            additionalOffset);
    }
    return hit;
}
} // namespace isaacsim::robot::surface_gripper
