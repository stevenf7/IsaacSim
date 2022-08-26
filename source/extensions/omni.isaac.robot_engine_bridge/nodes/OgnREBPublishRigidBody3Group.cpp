// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// #include "ros/ros.h"

#include <omni/isaac/robot_engine_bridge/IsaacConversions.h>
#include <omni/isaac/robot_engine_bridge/RebNode.h>

#include <OgnREBPublishRigidBody3GroupDatabase.h>

using namespace omni::isaac::robot_engine_bridge;

class OgnREBPublishRigidBody3Group : public RebNode
{
public:
    static bool compute(OgnREBPublishRigidBody3GroupDatabase& db)
    {
        auto& state = db.internalState<OgnREBPublishRigidBody3Group>();
        if (!state.initializeHandles())
        {
            return false;
        }
        state.updateTimestamp(db.inputs.timeStamp(), db.inputs.timeOffset());

        const GraphContextObj& context = db.abi_context();
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

        auto mUnitScale = UsdGeomGetStageMetersPerUnit(stage);

        IsaacMessage<isaac_message::RigidBody3Group> rigidBodiesMessage;
        auto rigidBodiesProto = rigidBodiesMessage.initProto();
        auto rigidBodies = rigidBodiesProto.initBodies(1);
        auto rigidBodyNames = rigidBodiesProto.initNames(1);


        auto isaacPoseProto = rigidBodies[1].initRefTBody();
        auto isaacTranslationProto = isaacPoseProto.initTranslation();
        auto isaacRotationProto = isaacPoseProto.initRotation();
        auto isaacLinearVelocityProto = rigidBodies[1].initLinearVelocity();
        auto isaacAngularVelocityProto = rigidBodies[1].initAngularVelocity();
        auto isaacLinearAccelerationProto = rigidBodies[1].initLinearAcceleration();
        auto isaacAngularAccelerationProto = rigidBodies[1].initAngularAcceleration();
        auto measuredLinearAcceleration = (db.inputs.linearVelocity() - state.mLastLinearVelocity) / state.mTimeDelta;
        state.mLastLinearAcceleration += state.timedSmoothingFactor(state.mTimeDelta, 1.0) *
                                         (measuredLinearAcceleration - state.mLastLinearAcceleration);

        auto measuredAngularAcceleration = (db.inputs.angularVelocity() - state.mLastAngularVelocity) / state.mTimeDelta;
        state.mLastAngularAcceleration += state.timedSmoothingFactor(state.mTimeDelta, 1.0) *
                                          (measuredAngularAcceleration - state.mLastAngularAcceleration);

        toVector3dProto(db.inputs.translation(), isaacTranslationProto);
        toSO3dProto(db.inputs.orientation(), isaacRotationProto);
        toVector3dProto(db.inputs.linearVelocity(), isaacLinearVelocityProto);
        toVector3dProto(db.inputs.angularVelocity(), isaacAngularVelocityProto);
        toVector3dProto(state.mLastLinearAcceleration, isaacLinearAccelerationProto);
        toVector3dProto(state.mLastAngularAcceleration, isaacAngularAccelerationProto);
        std::vector<std::unique_ptr<IsaacBuffer>> buffers;
        state.publish(db.inputs.outputComponent(), db.inputs.outputChannel(), rigidBodiesMessage, buffers);

        state.mLastLinearVelocity = db.inputs.linearVelocity();
        state.mLastAngularVelocity = db.inputs.angularVelocity();

        return true;
    }

private:
    pxr::GfVec3d mLastLinearVelocity;
    pxr::GfVec3d mLastLinearAcceleration;
    pxr::GfVec3d mLastAngularVelocity;
    pxr::GfVec3d mLastAngularAcceleration;


    float timedSmoothingFactor(float dt, float lambda)
    {
        if (lambda <= dt * 0.01f)
        {
            return 0.0;
        }
        else
        {
            return 1.0f - std::exp(-dt / lambda);
        }
    }
};

REGISTER_OGN_NODE()
