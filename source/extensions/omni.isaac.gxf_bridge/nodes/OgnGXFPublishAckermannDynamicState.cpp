// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "gxf/std/tensor.hpp"

#include <gems/control_types/ackermann_drive.hpp>
#include <plugins/Core/GxfNode.h>

#include <OgnGXFPublishAckermannDynamicStateDatabase.h>
using namespace omni::isaac::gxf_bridge;

class OgnGXFPublishAckermannDynamicState : public GxfNode
{
public:
    static bool compute(OgnGXFPublishAckermannDynamicStateDatabase& db)
    {
        auto& state = db.internalState<OgnGXFPublishAckermannDynamicState>();
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
            schema_server->add(nvidia::isaac::AckermannDynamicStateCompositeSchema()).assign_to(state.schema_uid_);

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

        nvidia::gxf::Expected<nvidia::isaac::CompositeMessageParts> maybe_message = nvidia::isaac::CreateCompositeMessage(
            state.getGxfContext(), state.mAllocator, 1, nvidia::isaac::AckermannDynamicStateIndices::kSize);
        if (!maybe_message)
        {
            db.logError("Cannot create AckermannDynamicState composite message");
            return false;
        }
        nvidia::isaac::CompositeMessageParts message = maybe_message.value();
        message.timestamp->pubtime = state.mClock->timestamp();
        message.timestamp->acqtime = message.timestamp->pubtime;
        const std::string frame_name = db.inputs.poseFrame();
        const auto maybe_frame = state.mAtlas->pose_tree().findFrame(frame_name.c_str());
        if (!maybe_frame)
        {
            db.logError("Cannot find frame %s", frame_name.c_str());
            return false;
        }
        message.pose_frame_uid->uid = maybe_frame.value();
        message.composite_schema_uid->uid = state.schema_uid_;
        nvidia::gxf::Expected<nvidia::isaac::AckermannDynamicStateView<double>> maybe_dynamics_state_view =
            nvidia::isaac::CompositeFromTensor<nvidia::isaac::AckermannDynamicStateView<double>>(message.view.slice(0));
        if (!maybe_dynamics_state_view)
        {
            db.logError("Cannot create base state view");
            return false;
        }
        nvidia::isaac::AckermannDynamicStateView<double> dynamicsState = maybe_dynamics_state_view.value();

        auto& linVel = db.inputs.linearVelocity();
        float measuredSpeedFront =
            pxr::GfDot(pxr::GfVec3d(linVel[0], linVel[1], linVel[2]), state.mRobotFront) * state.mUnitScale;
        dynamicsState.speed() = measuredSpeedFront;

        auto& linAcc = db.inputs.linearAcceleration();
        float measuredAccelerationFront =
            pxr::GfDot(pxr::GfVec3d(linAcc[0], linAcc[1], linAcc[2]), state.mRobotFront) * state.mUnitScale;
        dynamicsState.acceleration() = measuredAccelerationFront;

        if (std::abs(measuredSpeedFront) < db.inputs.linearSpeedThreshold())
        {
            dynamicsState.curvature() = 0.0;
            dynamicsState.curvature_derivative() = 0.0;
        }
        else
        {
            auto& angVel = db.inputs.angularVelocity();
            auto& angAcc = db.inputs.angularAcceleration();
            auto angSpeed = state.mZUp ? angVel[2] : angVel[1];
            auto angAccel = state.mZUp ? angAcc[2] : angAcc[1];
            dynamicsState.curvature() = angSpeed / measuredSpeedFront;
            dynamicsState.curvature_derivative() =
                (angAccel - measuredAccelerationFront * dynamicsState.curvature()) / measuredSpeedFront;
        }
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return state.publish(db.inputs.outputEntity(), db.inputs.outputComponent(), message.message);
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
