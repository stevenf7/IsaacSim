// clang-format off
#include <UsdPCH.h>
// clang-format on
#include <string>

#include "RigidBodiesSink.h"
#include "../Utils/IsaacConversions.h"
#include <omni/isaac/utils/Conversions.h>
#include <boost/algorithm/string.hpp>
#include <carb/logging/Log.h>
#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>

#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{

using utils::conversions::asGfQuatd;
using utils::conversions::asGfVec3d;

namespace robot_engine_bridge
{


RigidBodiesSink::RigidBodiesSink(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void RigidBodiesSink::tick()
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
            omni::isaac::dynamic_control::DcHandle artculationHandle =
                mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            omni::isaac::dynamic_control::DcHandle artculationRootBody =
                mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            // Calculate pose
            omni::isaac::dynamic_control::DcTransform articulationPose =
                mDynamicControlPtr->getRigidBodyPose(artculationRootBody);
            pxr::GfVec3d articulationTranslation = asGfVec3d(articulationPose.p);
            pxr::GfQuatd articulationRotation = asGfQuatd(articulationPose.r);
            // Calculate linear velocity
            pxr::GfVec3d articulationLinearVelocity =
                asGfVec3d(mDynamicControlPtr->getRigidBodyLinearVelocity(artculationRootBody));
            // Calculate angular velocity
            pxr::GfVec3d articulationAngularVelocity =
                asGfVec3d(mDynamicControlPtr->getRigidBodyAngularVelocity(artculationRootBody));
            // Calculate linear acceleration
            pxr::GfVec3d articulationLinearAcceleration =
                (articulationLinearVelocity - mLastLinearVelocity[bodyIndex]) / mTimeDelta;
            // Calculate angular acceleration
            pxr::GfVec3d articulationAngularAcceleration =
                (articulationAngularVelocity - mLastAngularVelocity[bodyIndex]) / mTimeDelta;
            mLastLinearVelocity[bodyIndex] = articulationLinearVelocity;
            mLastAngularVelocity[bodyIndex] = articulationAngularVelocity;
            // Converts to robot engine proto message
            toVector3dProto(articulationTranslation * mUnitScale, isaacTranslationProto);
            toSO3dProto(articulationRotation, isaacRotationProto);
            toVector3dProto(articulationLinearVelocity * mUnitScale, isaacLinearVelocityProto);
            toVector3dProto(articulationAngularVelocity, isaacAngularVelocityProto);
            toVector3dProto(articulationLinearAcceleration * mUnitScale, isaacLinearAccelerationProto);
            toVector3dProto(articulationAngularAcceleration, isaacAngularAccelerationProto);
        }
        else if (prim_type == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
                mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            // Calculate pose
            omni::isaac::dynamic_control::DcTransform rigidBodyPose =
                mDynamicControlPtr->getRigidBodyPose(rigidBodyHandle);
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
    std::vector<std::vector<uint8_t>> buffers;
    publish(mOutputComponent, mRigidBodyChannelName, rigidBodiesProto, isaac_message::RigidBody3GroupProtoId, buffers);
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
}
}
}
