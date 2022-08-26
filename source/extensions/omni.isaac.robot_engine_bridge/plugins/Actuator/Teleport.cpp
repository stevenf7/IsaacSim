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

#include "Teleport.h"

#include <carb/InterfaceUtils.h>
#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/robot_engine_bridge/IsaacConversions.h>
#include <omni/isaac/utils/Transforms.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


Teleport::Teleport(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void Teleport::tick()
{
    CARB_PROFILE_ZONE(0, "REB Teleport Tick");

    MessageHeader header;
    IsaacMessage<isaac_message::RigidBody3Group> commandsRigidBody3Group;
    if (mObjects.size() <= 0)
    {
        return;
    }
    if (checkErrorCode(receive(mInputComponent, mTeleportChannelName, header, commandsRigidBody3Group)))
    {
        auto commands = commandsRigidBody3Group.getProto();

        auto bodies = commands.getBodies();
        auto names = commands.getNames();
        if (bodies.size() != names.size())
        {
            CARB_LOG_ERROR("Length of rigidBodies and names do not match.");
            return;
        }
        for (size_t i = 0; i < bodies.size(); i++)
        {
            auto isaacBodyPose = bodies[i].getRefTBody();
            auto isaacBodyTranslation = isaacBodyPose.getTranslation();
            auto isaacBodyRotation = isaacBodyPose.getRotation().getQ();
            auto isaacBodyScale = bodies[i].getScales();
            pxr::GfVec3f pxBodyTranslation(
                isaacBodyTranslation.getX(), isaacBodyTranslation.getY(), isaacBodyTranslation.getZ());
            pxr::GfQuatf pxBodyRotation = toGfQuatf(isaacBodyRotation);
            pxr::GfVec3f pxBodyScale(isaacBodyScale.getX(), isaacBodyScale.getY(), isaacBodyScale.getZ());

            std::string inputName = names[i].cStr();
            // make usd paths absolute
            if (inputName[0] != '/')
            {
                inputName = "/" + inputName;
            }
            for (auto& object : mObjects)
            {
                pxr::UsdPrim prim = object.second;
                std::string actorName = object.first;
                if (strcmp(actorName.c_str(), inputName.c_str()) == 0)
                {
                    isaac::utils::transforms::setTransform(
                        mDynamicControlPtr, prim, pxBodyTranslation * mInvUnitScale, pxBodyRotation);
                    isaac::utils::transforms::setScale(mDynamicControlPtr, prim, pxBodyScale);
                }
            }
        }
    }
}

void Teleport::onStart()
{
    onComponentChange();
}

void Teleport::onComponentChange()
{
    IsaacComponent::onComponentChange();

    const pxr::RobotEngineBridgeSchemaRobotEngineTeleport& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineTeleport)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mTeleportChannelName);

    pxr::SdfPathVector targets;
    typedPrim.GetTeleportPrimsRel().GetTargets(&targets);
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

    mInvUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}

void Teleport::addObject(const std::string& actorName, pxr::UsdPrim& prim)
{
    mObjects[actorName] = prim;
}

void Teleport::eraseObject(const std::string& actorName)
{
    mObjects.erase(actorName);
}

void Teleport::updateComponent(const std::string& inputComponent, const std::string& inputChannel)
{
    mInputComponent = inputComponent;
    mTeleportChannelName = inputChannel;
    mInvUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}
}
}
}
