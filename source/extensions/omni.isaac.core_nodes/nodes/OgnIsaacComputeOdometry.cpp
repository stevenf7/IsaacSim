// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
#include <DynamicControl.h>
#include <OgnIsaacComputeOdometryDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

using omni::isaac::utils::conversions::asGfRotation;
using omni::isaac::utils::conversions::asGfVec3d;

class OgnIsaacComputeOdometry : public BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnIsaacComputeOdometryDatabase::sPerInstanceState<OgnIsaacComputeOdometry>(nodeObj, instanceId);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnIsaacComputeOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnIsaacComputeOdometry>();
        if (state.mFirstFrame)
        {
            const auto& prim = db.inputs.chassisPrim();
            const char* primPath;
            if (prim.size() > 0)
            {
                primPath = omni::fabric::toSdfPath(prim[0]).GetText();
            }
            else
            {
                db.logError("Omnigraph Error: no chasis prim found");
                return false;
            }

            state.mFirstFrame = false;
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }
            auto type = state.mDynamicControlPtr->peekObjectType(primPath);

            // Checking we have a valid articulation
            if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.mArticulationHandle = state.mDynamicControlPtr->getArticulation(primPath);
                if (!state.mArticulationHandle)
                {
                    db.logError("Articulation not found for prim");
                    return false;
                }

                state.mRigidBodyHandle = state.mDynamicControlPtr->getArticulationRootBody(state.mArticulationHandle);
            }
            else if (type == omni::isaac::dynamic_control::eDcObjectRigidBody)
            {
                state.mRigidBodyHandle = state.mDynamicControlPtr->getRigidBody(primPath);
            }
            else
            {
                db.logError("prim is not a valid rigid body or articulation root");
                return false;
            }
            if (!state.mRigidBodyHandle)
            {
                db.logError("prim is not a valid rigid body");
                return false;
            }


            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            // get starting pose in the world frame
            state.mStartingPose = state.mDynamicControlPtr->getRigidBodyPose(state.mRigidBodyHandle);
            state.mLastTime = state.mCoreNodeFramework->getSimTime();
        }

        state.computeOdometry(db);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    void computeOdometry(OgnIsaacComputeOdometryDatabase& db)
    {
        auto bodyPose = mDynamicControlPtr->getRigidBodyPose(mRigidBodyHandle);

        auto bodyLocalLinVel = mDynamicControlPtr->getRigidBodyLocalLinearVelocity(mRigidBodyHandle);
        auto bodyAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mRigidBodyHandle);


        if (mCoreNodeFramework->getSimTime() != mLastTime)
        {
            double dt = mCoreNodeFramework->getSimTime() - mLastTime;
            mLinearAcceleration.x = static_cast<float>((bodyLocalLinVel.x - mPrevLinearVelocity.x) / dt);
            mLinearAcceleration.y = static_cast<float>((bodyLocalLinVel.y - mPrevLinearVelocity.y) / dt);
            mLinearAcceleration.z = static_cast<float>((bodyLocalLinVel.z - mPrevLinearVelocity.z) / dt);

            mAngularAcceleration.x = static_cast<float>((bodyAngVel.x - mPrevAngularVelocity.x) / dt);
            mAngularAcceleration.y = static_cast<float>((bodyAngVel.y - mPrevAngularVelocity.y) / dt);
            mAngularAcceleration.z = static_cast<float>((bodyAngVel.z - mPrevAngularVelocity.z) / dt);

            db.outputs.linearAcceleration().Set(mLinearAcceleration.x, mLinearAcceleration.y, mLinearAcceleration.z);
            db.outputs.angularAcceleration().Set(mAngularAcceleration.x, mAngularAcceleration.y, mAngularAcceleration.z);
        }


        // calculate odom reading from starting position
        pxr::GfVec3d globalTranslation = pxr::GfVec3d(
            bodyPose.p.x - mStartingPose.p.x, bodyPose.p.y - mStartingPose.p.y, bodyPose.p.z - mStartingPose.p.z);

        db.outputs.position() = (asGfRotation(mStartingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;

        db.outputs.orientation() = (asGfRotation(bodyPose.r) * asGfRotation(mStartingPose.r).GetInverse()).GetQuat();

        db.outputs.linearVelocity().Set(bodyLocalLinVel.x, bodyLocalLinVel.y, bodyLocalLinVel.z);

        db.outputs.angularVelocity().Set(bodyAngVel.x, bodyAngVel.y, bodyAngVel.z);


        mPrevLinearVelocity = bodyLocalLinVel;
        mPrevAngularVelocity = bodyAngVel;
        mLastTime = mCoreNodeFramework->getSimTime();
    }

    virtual void reset()
    {
        mFirstFrame = true;
    }

private:
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    // Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mRigidBodyHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr = nullptr;

    // pose of the robot at start
    omni::isaac::dynamic_control::DcTransform mStartingPose;

    double mUnitScale;

    bool mFirstFrame = true;

    double mLastTime = 0.0;
    carb::Float3 mLinearAcceleration = { 0, 0, 0 };
    carb::Float3 mAngularAcceleration = { 0, 0, 0 };

    carb::Float3 mPrevLinearVelocity = { 0, 0, 0 };
    carb::Float3 mPrevAngularVelocity = { 0, 0, 0 };

    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
}
}
}
