// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on
#include "RigidBodiesSink.h"

#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/logging/Log.h>

#include <boost/algorithm/string.hpp>
#include <omni/isaac/robot_engine_bridge/IsaacConversions.h>
#include <omni/isaac/utils/Conversions.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>

#include <string>

namespace omni
{
namespace isaac
{

using utils::conversions::asGfQuatd;
using utils::conversions::asGfVec3d;

namespace robot_engine_bridge
{

using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;

RigidBodiesSink::RigidBodiesSink(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void RigidBodiesSink::tick()
{
}

void RigidBodiesSink::publishAllMessages()
{

    if (mObjects.size() <= 0)
        return;

    if (mLastLinearVelocity.size() == 0)
        mLastLinearVelocity.resize(mObjects.size(), pxr::GfVec3d(0, 0, 0));
    if (mLastAngularVelocity.size() == 0)
        mLastAngularVelocity.resize(mObjects.size(), pxr::GfVec3d(0, 0, 0));

    // Create the message
    IsaacMessage<isaac_message::RigidBody3Group> rigidBodiesMessage;
    auto rigidBodiesProto = rigidBodiesMessage.initProto();
    auto rigidBodies = rigidBodiesProto.initBodies(mObjects.size());
    auto rigidBodyNames = rigidBodiesProto.initNames(mObjects.size());

    int bodyIndex = 0;
    for (auto& object : mObjects)
    {
        // For each rigid body
        bodyIndex = object.second.first;
        pxr::UsdPrim prim = object.second.second;
        // Set actor name
        std::string actorName = object.first;
        rigidBodyNames.set(bodyIndex, actorName);

        auto isaacPoseProto = rigidBodies[bodyIndex].initRefTBody();
        auto isaacTranslationProto = isaacPoseProto.initTranslation();
        auto isaacRotationProto = isaacPoseProto.initRotation();
        auto isaacLinearVelocityProto = rigidBodies[bodyIndex].initLinearVelocity();
        auto isaacAngularVelocityProto = rigidBodies[bodyIndex].initAngularVelocity();
        auto isaacLinearAccelerationProto = rigidBodies[bodyIndex].initLinearAcceleration();
        auto isaacAngularAccelerationProto = rigidBodies[bodyIndex].initAngularAcceleration();

        omni::isaac::dynamic_control::DcObjectType prim_type =
            mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
        if (prim_type == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            DcHandle artRootBody = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            // Calculate pose
            DcTransform articulationPose = mDynamicControlPtr->getRigidBodyPose(artRootBody);
            pxr::GfVec3d artTranslation = asGfVec3d(articulationPose.p);
            pxr::GfQuatd artRotation = asGfQuatd(articulationPose.r);
            // Calculate linear velocity
            pxr::GfVec3d artLinVel = asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artRootBody));
            // Calculate angular velocity
            pxr::GfVec3d artAngVel = asGfVec3d(mDynamicControlPtr->getRigidBodyAngularVelocity(artRootBody));
            // Calculate linear acceleration
            pxr::GfVec3d artLinAcc = (artLinVel - mLastLinearVelocity[bodyIndex]) / mTimeDelta;
            // Calculate angular acceleration
            pxr::GfVec3d artAngAcc = (artAngVel - mLastAngularVelocity[bodyIndex]) / mTimeDelta;
            mLastLinearVelocity[bodyIndex] = artLinVel;
            mLastAngularVelocity[bodyIndex] = artAngVel;
            // Converts to robot engine proto message
            toVector3dProto(artTranslation * mUnitScale, isaacTranslationProto);
            toSO3dProto(artRotation, isaacRotationProto);
            toVector3dProto(artLinVel * mUnitScale, isaacLinearVelocityProto);
            toVector3dProto(artAngVel, isaacAngularVelocityProto);
            toVector3dProto(artLinAcc * mUnitScale, isaacLinearAccelerationProto);
            toVector3dProto(artAngAcc, isaacAngularAccelerationProto);
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {

            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            // Calculate pose
            DcTransform rigidBodyPose = mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
            pxr::GfVec3d rigidBodyTranslation = asGfVec3d(rigidBodyPose.p);
            pxr::GfQuatd rigidBodyRotation = asGfQuatd(rigidBodyPose.r);
            // Calculate linear velocity
            pxr::GfVec3d rigidBodyLinearVelocity =
                asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(rigidBodyHandle));
            // Calculate angular velocity
            pxr::GfVec3d rigidBodyAngularVelocity =
                asGfVec3d(mDynamicControlPtr->getRigidBodyAngularVelocity(rigidBodyHandle));
            // Calculate linear acceleration
            pxr::GfVec3d rigidBodyLinearAcceleration =
                (rigidBodyLinearVelocity - mLastLinearVelocity[bodyIndex]) / mTimeDelta;
            // Calculate angular acceleration
            pxr::GfVec3d rigidBodyAngularAcceleration =
                (rigidBodyAngularVelocity - mLastAngularVelocity[bodyIndex]) / mTimeDelta;
            mLastLinearVelocity[bodyIndex] = rigidBodyLinearVelocity;
            mLastAngularVelocity[bodyIndex] = rigidBodyAngularVelocity;
            // Converts to robot engine proto message
            toVector3dProto(rigidBodyTranslation * mUnitScale, isaacTranslationProto);
            toSO3dProto(rigidBodyRotation, isaacRotationProto);
            toVector3dProto(rigidBodyLinearVelocity * mUnitScale, isaacLinearVelocityProto);
            toVector3dProto(rigidBodyAngularVelocity, isaacAngularVelocityProto);
            toVector3dProto(rigidBodyLinearAcceleration * mUnitScale, isaacLinearAccelerationProto);
            toVector3dProto(rigidBodyAngularAcceleration, isaacAngularAccelerationProto);
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectNone)
        {
            // Calculate pose
            const pxr::GfTransform usdBodyPose(omni::usd::UsdUtils::getWorldTransformMatrix(prim));
            pxr::GfVec3d usdBodyTranslation = usdBodyPose.GetTranslation();
            pxr::GfQuatd usdBodyRotation = usdBodyPose.GetRotation().GetQuat();
            // Set linear, angular velocity and acceleration to 0
            pxr::GfVec3d usdBodyLinearVelocity(0, 0, 0);
            pxr::GfVec3d usdBodyAngularVelocity(0, 0, 0);
            pxr::GfVec3d usdBodyLinearAcceleration(0, 0, 0);
            pxr::GfVec3d usdBodyAngularAcceleration(0, 0, 0);
            mLastLinearVelocity[bodyIndex] = usdBodyLinearVelocity;
            mLastAngularVelocity[bodyIndex] = usdBodyAngularVelocity;
            // Converts to robot engine proto message
            toVector3dProto(usdBodyTranslation * mUnitScale, isaacTranslationProto);
            toSO3dProto(usdBodyRotation, isaacRotationProto);
            toVector3dProto(usdBodyLinearVelocity, isaacLinearVelocityProto);
            toVector3dProto(usdBodyAngularVelocity, isaacAngularVelocityProto);
            toVector3dProto(usdBodyLinearAcceleration, isaacLinearAccelerationProto);
            toVector3dProto(usdBodyAngularAcceleration, isaacAngularAccelerationProto);
        }
        bodyIndex++;
    }
    std::vector<std::unique_ptr<IsaacBuffer>> buffers;
    // We publish in json mode to handle cases with many prims
    bool publishBinary = mObjects.size() <= 10;
    publish(mOutputComponent, mRigidBodyChannelName, rigidBodiesMessage, buffers, publishBinary);
}

void RigidBodiesSink::onStart()
{
    onComponentChange();
}

void RigidBodiesSink::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineRigidBodySink)mPrim;


    isaac::utils::safeGetAttribute(typedPrim.GetOutputComponentAttr(), mOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetOutputChannelAttr(), mRigidBodyChannelName);

    pxr::SdfPathVector targets;
    typedPrim.GetRigidBodyPrimsRel().GetTargets(&targets);
    if (targets.size() == 0)
    {
        return;
    }
    for (pxr::SdfPath eachRigidBodyPath : targets)
    {
        pxr::UsdPrim rigidBodyPrim = mStage->GetPrimAtPath(eachRigidBodyPath);
        const std::string actorName = eachRigidBodyPath.GetString();
        if (rigidBodyPrim)
        {
            if (mObjects.find(actorName) != mObjects.end())
                eraseObject(actorName);
            addObject(actorName, rigidBodyPrim);
        }
    }


    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}

void RigidBodiesSink::addObject(const std::string& actorName, pxr::UsdPrim& prim)
{
    mObjects[actorName] = std::pair<size_t, pxr::UsdPrim>(mObjects.size(), prim);
}

void RigidBodiesSink::eraseObject(const std::string& actorName)
{
    const size_t removed_index = mObjects[actorName].first;
    mObjects.erase(actorName);

    for (auto& object : mObjects)
    {
        // Once the index is removed, all items "higher" should be decremented by one
        if (object.second.first > removed_index)
        {
            object.second.first -= 1;
        }
    }
}

void RigidBodiesSink::updateComponent(const std::string& outputComponent, const std::string& outputChannel)
{
    mOutputComponent = outputComponent;
    mRigidBodyChannelName = outputChannel;
    mUnitScale = UsdGeomGetStageMetersPerUnit(mStage);
}

}
}
}
