// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/logging/Log.h>
#include <carb/profiler/Profile.h>
#include <carb/InterfaceUtils.h>

#include "../Utils/IsaacUtilities.h"

#include "Teleport.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


Teleport::Teleport(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
    onComponentChange();
}

void Teleport::tick()
{
    CARB_PROFILE_ZONE(0, "REB Teleport Tick");

    MessageHeader header;
    IsaacMessage<isaac_message::RigidBody3Group> commandsRigidBody3Group;
    auto commands = commandsRigidBody3Group.initProto();
    if (mObjects.size() <= 0)
    {
        return;
    }
    if (receive(mInputComponent, mTeleportChannelName, header, commands))
    {
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
            pxr::GfVec4f pxBodyRotation(
                isaacBodyRotation.getX(), isaacBodyRotation.getY(), isaacBodyRotation.getZ(), isaacBodyRotation.getW());
            pxr::GfVec3f pxBodyScale(isaacBodyScale.getX(), isaacBodyScale.getY(), isaacBodyScale.getZ());

            for (auto& object : mObjects)
            {
                pxr::UsdPrim prim = object.second;
                std::string actorName = object.first;
                if (strcmp(actorName.c_str(), names[i].asString().cStr()) == 0)
                {
                    setTransform(mDynamicControlPtr, prim, pxBodyTranslation * mUnitScale, pxBodyRotation);
                    setScale(prim, pxBodyScale);
                }
            }
        }
    }
}


void Teleport::onComponentChange()
{
    IsaacComponent::onComponentChange();

    if (auto attr = mPrim.GetAttribute(pxr::TfToken("teleportInputComponent")))
    {
        attr.Get(&mInputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("teleportChannelName")))
    {
        attr.Get(&mTeleportChannelName);
    }
    mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}

void Teleport::addObject(std::string& actorName, pxr::UsdPrim& prim)
{
    mObjects[actorName] = prim;
}

void Teleport::eraseObject(std::string& actorName)
{
    mObjects.erase(actorName);
}
}
}
}
