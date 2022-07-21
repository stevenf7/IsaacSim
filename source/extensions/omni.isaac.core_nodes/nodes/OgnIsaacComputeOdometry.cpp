// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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
#include <carb/flatcache/FlatCache.h>
#include <carb/logging/Logger.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

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
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacComputeOdometryDatabase::sInternalState<OgnIsaacComputeOdometry>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnIsaacComputeOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacComputeOdometry>();

        if (state.mFirstFrame)
        {

            state.mFirstFrame = false;

            const char* primPath = db.inputs.chassisPrim.path();

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

            return true;
        }

        state.computeOdometry(db);
        return true;
    }

    void computeOdometry(OgnIsaacComputeOdometryDatabase& db)
    {
        auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mRigidBodyHandle);

        auto chassisLocalLinVel = mDynamicControlPtr->getRigidBodyLocalLinearVelocity(mRigidBodyHandle);
        auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mRigidBodyHandle);

        // calculate odom reading from starting position
        pxr::GfVec3d globalTranslation =
            pxr::GfVec3d(chassisPose.p.x - mStartingPose.p.x, chassisPose.p.y - mStartingPose.p.y,
                         chassisPose.p.z - mStartingPose.p.z);

        db.outputs.position() = (asGfRotation(mStartingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;

        db.outputs.orientation() = (asGfRotation(chassisPose.r) * asGfRotation(mStartingPose.r).GetInverse()).GetQuat();

        db.outputs.linearVelocity().Set(chassisLocalLinVel.x, chassisLocalLinVel.y, chassisLocalLinVel.z);

        db.outputs.angularVelocity().Set(chassisAngVel.x, chassisAngVel.y, chassisAngVel.z);
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
};

REGISTER_OGN_NODE()
} // nodes
} // graph
} // omni
