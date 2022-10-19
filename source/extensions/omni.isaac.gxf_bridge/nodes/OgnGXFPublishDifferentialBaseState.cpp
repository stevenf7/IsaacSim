// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <gems/control_types/differential_drive.hpp>
#include <omni/isaac/gxf_bridge/GxfNode.h>

#include <OgnGXFPublishDifferentialBaseStateDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishDifferentialBaseState : public GxfNode
{
public:
    static bool compute(OgnGXFPublishDifferentialBaseStateDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishDifferentialBaseState>();
        if (!state.getGxfContext())
        {
            if (state.setGxfContext(db.inputs.context()) != GXF_SUCCESS)
            {
                return false;
            }

            nvidia::gxf::Handle<nvidia::isaac::CompositeSchemaServer> schema_server =
                state.mAtlas->composite_schema_server();

            if (!schema_server)
            {
                CARB_LOG_ERROR("Composite schema server not set in ATLAS.");
                return false;
            }
            schema_server->add(nvidia::isaac::DifferentialBaseStateCompositeSchema()).assign_to(state.schema_uid_);

            const GraphContextObj& context = db.abi_context();

            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            state.mZUp = UsdGeomGetStageUpAxis(stage) == "Z" ? true : false;
            state.mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

            auto& robotFrontVec = db.inputs.robotFront();

            state.mRobotFront = pxr::GfVec3f(robotFrontVec[0], robotFrontVec[1], robotFrontVec[2]);

            state.mRobotFront = pxr::GfGetNormalized(state.mRobotFront, 1.0f);

            if (state.mZUp)
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 0.0, 1.0), state.mRobotFront);
            }
            else
            {
                state.mRobotSide = pxr::GfCross(pxr::GfVec3f(0.0, 1.0, 0.0), state.mRobotFront);
            }
            return true;
        }

        nvidia::isaac::CreateCompositeMessage(state.getGxfContext(), state.mAllocator, /*num_rows=*/1, /*num_cols=*/4)
            .map(
                [state, db](nvidia::isaac::CompositeMessageParts message)
                {
                    message.timestamp->pubtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
                    message.timestamp->acqtime = static_cast<int64_t>(db.inputs.timeStamp() * 1e9);
                    message.pose_frame_uid->uid =
                        state.mAtlas->pose_tree().findFrame(db.inputs.poseFrame().data()).value();
                    message.composite_schema_uid->uid = state.schema_uid_;

                    return nvidia::isaac::CompositeFromTensor<nvidia::isaac::DifferentialBaseStateView<double>>(
                               message.view.slice(0))
                        .map(
                            [db, state](nvidia::isaac::DifferentialBaseStateView<double> diffBaseState)
                            {
                                auto& linVel = db.inputs.linearVelocity();
                                float measuredSpeedFront =
                                    pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), state.mRobotFront) *
                                    state.mUnitScale;
                                diffBaseState.linear_speed() = measuredSpeedFront;

                                auto& linAcc = db.inputs.linearAcceleration();
                                float measuredAccelerationFront =
                                    pxr::GfDot(pxr::GfVec3d(linAcc[0], linAcc[1], linAcc[2]), state.mRobotFront) *
                                    state.mUnitScale;
                                diffBaseState.linear_acceleration() = measuredAccelerationFront;

                                auto& angVel = db.inputs.angularVelocity();
                                auto& angAcc = db.inputs.angularAcceleration();

                                if (state.mZUp)
                                { // Get Z component
                                    diffBaseState.angular_speed() = angVel[2];
                                    diffBaseState.angular_acceleration() = angAcc[2];
                                }
                                else
                                {
                                    // Get Y component
                                    diffBaseState.angular_speed() = angVel[1];
                                    diffBaseState.angular_acceleration() = angAcc[1];
                                }
                            })
                        .substitute(message);
                })
            .map([&state, db](nvidia::isaac::CompositeMessageParts message)
                 { return state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.message); });

        return true;
    }

private:
    uint64_t schema_uid_;

    double mUnitScale = 1.0;
    bool mZUp = true;

    // The front of the robot
    pxr::GfVec3f mRobotFront = pxr::GfVec3f(1.0, 0.0, 0.0);
    pxr::GfVec3f mRobotSide = pxr::GfVec3f(0.0, 1.0, 0.0);
    pxr::GfVec3f mStageup = pxr::GfVec3f(0.0, 0.0, 1.0);
};

REGISTER_OGN_NODE()
