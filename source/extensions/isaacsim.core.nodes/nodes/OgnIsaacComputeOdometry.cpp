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

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <isaacsim/core/includes/BaseResetNode.h>
#include <isaacsim/core/includes/Conversions.h>
#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

#include <DynamicControl.h>
#include <OgnIsaacComputeOdometryDatabase.h>

namespace isaacsim
{
namespace core
{
namespace nodes
{

using isaacsim::core::includes::conversions::asGfRotation;
using isaacsim::core::includes::conversions::asGfVec3d;

class OgnIsaacComputeOdometry : public isaacsim::core::includes::BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacComputeOdometryDatabase::sPerInstanceState<OgnIsaacComputeOdometry>(nodeObj, instanceId);

        state.m_dynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();

        if (!state.m_dynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnIsaacComputeOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnIsaacComputeOdometry>();
        if (state.m_firstFrame)
        {

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            const auto& prim = db.inputs.chassisPrim();
            const char* primPath;
            if (!prim.empty())
            {
                if (!stage->GetPrimAtPath(omni::fabric::toSdfPath(prim[0])))
                {
                    db.logError("The prim %s is not valid. Please specify at least one valid chassis prim", prim[0]);
                    return false;
                }
                primPath = omni::fabric::toSdfPath(prim[0]).GetText();
            }
            else
            {
                db.logError("OmniGraph Error: no chassis prim found");
                return false;
            }


            auto type = state.m_dynamicControlPtr->peekObjectType(primPath);

            // Checking we have a valid articulation
            if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.m_articulationHandle = state.m_dynamicControlPtr->getArticulation(primPath);
                if (!state.m_articulationHandle)
                {
                    db.logError("Articulation not found for prim");
                    return false;
                }

                state.m_rigidBodyHandle = state.m_dynamicControlPtr->getArticulationRootBody(state.m_articulationHandle);
            }
            else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
            {
                state.m_rigidBodyHandle = state.m_dynamicControlPtr->getRigidBody(primPath);
            }
            else
            {
                db.logError("prim is not a valid rigid body or articulation root");
                return false;
            }
            if (!state.m_rigidBodyHandle)
            {
                db.logError("prim is not a valid rigid body");
                return false;
            }


            state.m_unitScale = UsdGeomGetStageMetersPerUnit(stage);

            // get starting pose in the world frame
            state.m_startingPose = state.m_dynamicControlPtr->getRigidBodyPose(state.m_rigidBodyHandle);
            state.m_lastTime = state.m_coreNodeFramework->getSimTime();
            state.m_firstFrame = false;
        }

        state.computeOdometry(db);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    void computeOdometry(OgnIsaacComputeOdometryDatabase& db)
    {
        auto bodyPose = m_dynamicControlPtr->getRigidBodyPose(m_rigidBodyHandle);

        auto bodyLocalLinVel = m_dynamicControlPtr->getRigidBodyLocalLinearVelocity(m_rigidBodyHandle);
        auto bodyGlobalLinVel = m_dynamicControlPtr->getRigidBodyLinearVelocity(m_rigidBodyHandle);
        auto bodyAngVel = m_dynamicControlPtr->getRigidBodyAngularVelocity(m_rigidBodyHandle);

        if (m_coreNodeFramework->getSimTime() != m_lastTime)
        {
            double dt = m_coreNodeFramework->getSimTime() - m_lastTime;
            // Local accelerations
            m_linearAcceleration.x = static_cast<float>((bodyLocalLinVel.x - m_prevLinearVelocity.x) / dt);
            m_linearAcceleration.y = static_cast<float>((bodyLocalLinVel.y - m_prevLinearVelocity.y) / dt);
            m_linearAcceleration.z = static_cast<float>((bodyLocalLinVel.z - m_prevLinearVelocity.z) / dt);

            // Global accelerations
            m_globalLinearAcceleration.x = static_cast<float>((bodyGlobalLinVel.x - m_prevGlobalLinearVelocity.x) / dt);
            m_globalLinearAcceleration.y = static_cast<float>((bodyGlobalLinVel.y - m_prevGlobalLinearVelocity.y) / dt);
            m_globalLinearAcceleration.z = static_cast<float>((bodyGlobalLinVel.z - m_prevGlobalLinearVelocity.z) / dt);

            m_angularAcceleration.x = static_cast<float>((bodyAngVel.x - m_prevAngularVelocity.x) / dt);
            m_angularAcceleration.y = static_cast<float>((bodyAngVel.y - m_prevAngularVelocity.y) / dt);
            m_angularAcceleration.z = static_cast<float>((bodyAngVel.z - m_prevAngularVelocity.z) / dt);

            db.outputs.linearAcceleration().Set(m_linearAcceleration.x, m_linearAcceleration.y, m_linearAcceleration.z);
            db.outputs.globalLinearAcceleration().Set(
                m_globalLinearAcceleration.x, m_globalLinearAcceleration.y, m_globalLinearAcceleration.z);
            db.outputs.angularAcceleration().Set(
                m_angularAcceleration.x, m_angularAcceleration.y, m_angularAcceleration.z);
        }

        // calculate odom reading from starting position
        pxr::GfVec3d globalTranslation = pxr::GfVec3d(
            bodyPose.p.x - m_startingPose.p.x, bodyPose.p.y - m_startingPose.p.y, bodyPose.p.z - m_startingPose.p.z);

        db.outputs.position() =
            (asGfRotation(m_startingPose.r).GetInverse()).TransformDir(globalTranslation) * m_unitScale;

        db.outputs.orientation() = (asGfRotation(bodyPose.r) * asGfRotation(m_startingPose.r).GetInverse()).GetQuat();

        db.outputs.linearVelocity().Set(bodyLocalLinVel.x, bodyLocalLinVel.y, bodyLocalLinVel.z);
        db.outputs.globalLinearVelocity().Set(bodyGlobalLinVel.x, bodyGlobalLinVel.y, bodyGlobalLinVel.z);
        db.outputs.angularVelocity().Set(bodyAngVel.x, bodyAngVel.y, bodyAngVel.z);

        m_prevLinearVelocity = bodyLocalLinVel;
        m_prevGlobalLinearVelocity = bodyGlobalLinVel;
        m_prevAngularVelocity = bodyAngVel;
        m_lastTime = m_coreNodeFramework->getSimTime();
    }

    virtual void reset()
    {
        m_firstFrame = true;
    }

private:
    omni::isaac::dynamic_control::DcHandle m_articulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    // Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle m_rigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* m_dynamicControlPtr = nullptr;

    // pose of the robot at start
    omni::isaac::dynamic_control::DcTransform m_startingPose;

    double m_unitScale;

    bool m_firstFrame = true;

    double m_lastTime = 0.0;
    carb::Float3 m_linearAcceleration = { 0, 0, 0 };
    carb::Float3 m_angularAcceleration = { 0, 0, 0 };

    carb::Float3 m_prevLinearVelocity = { 0, 0, 0 };
    carb::Float3 m_prevAngularVelocity = { 0, 0, 0 };

    carb::Float3 m_globalLinearAcceleration = { 0, 0, 0 };
    carb::Float3 m_prevGlobalLinearVelocity = { 0, 0, 0 };

    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework;
};

REGISTER_OGN_NODE()
}
}
}
