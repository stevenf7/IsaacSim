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

#include <OgnIsaacReadOdometryDatabase.h>

namespace omni
{
namespace isaac
{
namespace core_nodes
{

using omni::isaac::utils::conversions::asGfRotation;
using omni::isaac::utils::conversions::asGfVec3d;

class OgnIsaacReadOdometry : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnIsaacReadOdometryDatabase::sInternalState<OgnIsaacReadOdometry>(nodeObj);

        state.mDynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.mDynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadOdometryDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.internalState<OgnIsaacReadOdometry>();

        if (state.mFirstFrame)
        {

            state.mFirstFrame = false;

            const char* chassisPrimPath = db.inputs.chassisPrim.path();

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            // Checking we have a valid articulation
            if (state.mDynamicControlPtr->peekObjectType(chassisPrimPath) ==
                omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.mArticulationHandle = state.mDynamicControlPtr->getArticulation(chassisPrimPath);
            }
            else
            {
                db.logError("chassisPrim is not a valid articulation");
                return false;
            }

            if (!state.mArticulationHandle)
            {
                db.logError("Articulation not found for chassisPrim");
                return false;
            }

            state.mChassisHandle = state.mDynamicControlPtr->getArticulationRootBody(state.mArticulationHandle);

            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            // get starting pose in the world frame
            state.mStartingPose = state.mDynamicControlPtr->getRigidBodyPose(state.mChassisHandle);

            return true;
        }

        state.computeOdometry(db);
        return true;
    }

    void computeOdometry(OgnIsaacReadOdometryDatabase& db)
    {
        auto chassisPose = mDynamicControlPtr->getRigidBodyPose(mChassisHandle);

        auto chassisLocalLinVel = mDynamicControlPtr->getRigidBodyLocalLinearVelocity(mChassisHandle);
        auto chassisAngVel = mDynamicControlPtr->getRigidBodyAngularVelocity(mChassisHandle);

        // calculate odom reading from starting position
        pxr::GfVec3d globalTranslation =
            pxr::GfVec3d(chassisPose.p.x - mStartingPose.p.x, chassisPose.p.y - mStartingPose.p.y,
                         chassisPose.p.z - mStartingPose.p.z);
        pxr::GfVec3d odomTranslation =
            (asGfRotation(mStartingPose.r).GetInverse()).TransformDir(globalTranslation) * mUnitScale;
        pxr::GfQuatd odomRotation = (asGfRotation(chassisPose.r) * asGfRotation(mStartingPose.r).GetInverse()).GetQuat();

        auto& position = db.outputs.position();
        position[0] = odomTranslation[0];
        position[1] = odomTranslation[1];
        position[2] = odomTranslation[2];

        auto& orientation = db.outputs.orientation();
        orientation[0] = odomRotation.GetImaginary()[0];
        orientation[1] = odomRotation.GetImaginary()[1];
        orientation[2] = odomRotation.GetImaginary()[2];
        orientation[3] = odomRotation.GetReal();

        auto& linVel = db.outputs.linearVelocity();
        linVel[0] = chassisLocalLinVel.x;
        linVel[1] = chassisLocalLinVel.y;
        linVel[2] = chassisLocalLinVel.z;

        auto& angVel = db.outputs.angularVelocity();
        angVel[0] = chassisAngVel.x;
        angVel[1] = chassisAngVel.y;
        angVel[2] = chassisAngVel.z;
    }

    virtual void reset()
    {
        mFirstFrame = true;
    }

private:
    omni::isaac::dynamic_control::DcHandle mArticulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

    // Rigidbody whose state (velocity, acceleration) is being published.
    omni::isaac::dynamic_control::DcHandle mChassisHandle = omni::isaac::dynamic_control::kDcInvalidHandle;

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
