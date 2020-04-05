// clang-format off
#include <UsdPCH.h>
// clang-format on
#include <vector>
#include <memory>
#include <string>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <carb/profiler/Profile.h>
#include <carb/InterfaceUtils.h>

#include <omni/usd/UsdUtils.h>

#include "../Core/IsaacComponent.h"
#include "../Monitor/RigidBodiesSink.h"
#include "../Actuator/Teleport.h"
#include "../Utils/IsaacUtilities.h"

#include "ScenarioFromMessage.h"

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{


ScenarioFromMessage::ScenarioFromMessage(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
    : IsaacComponent(), mDynamicControlPtr(dynamicControlPtr)
{
}

void ScenarioFromMessage::initialize(IsaacCApi* isaacCApiPtr,
                                     const isaac_handle_t& appHandle,
                                     const pxr::UsdPrim& prim,
                                     pxr::UsdStageRefPtr stage)
{
    IsaacComponent::initialize(isaacCApiPtr, appHandle, prim, stage);
    initSubComponents();
    onComponentChange();
}

void ScenarioFromMessage::tick()
{
    CARB_PROFILE_ZONE(0, "REB ScenarioFromMessage Tick");

    IsaacMessage<isaac_message::ActorGroup> actorGroup;
    auto actorGroupProto = actorGroup.initProto();
    {
        // Receive current command
        std::vector<std::vector<uint8_t>> buffers;
        MessageHeader header;
        if (receive(mInputComponent, mRequestChannelName, header, actorGroupProto, buffers))
        {
            LoadScenarioFromMessage(actorGroupProto);
        }
    }
    mTeleport->updateTimestamp(mTimeSeconds, mTimeDelta, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
    mTeleport->tick();

    mRigidBodiesSink->updateTimestamp(mTimeSeconds, mTimeDelta, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
    mRigidBodiesSink->tick();
}

void ScenarioFromMessage::onComponentChange()
{

    IsaacComponent::onComponentChange();
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("inputComponent")))
    {
        attr.Get(&mInputComponent);
    }
    if (auto attr = mPrim.GetAttribute(pxr::TfToken("requestChannelName")))
    {
        attr.Get(&mRequestChannelName);
    }

    mTeleport->onComponentChange();
    mRigidBodiesSink->onComponentChange();
    mUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}
void ScenarioFromMessage::initSubComponents()
{

    mTeleport = std::make_unique<Teleport>(mDynamicControlPtr);
    mTeleport->initialize(mIsaacCApiPtr, mAppHandle, mPrim, mStage);

    mRigidBodiesSink = std::make_unique<RigidBodiesSink>(mDynamicControlPtr);
    mRigidBodiesSink->initialize(mIsaacCApiPtr, mAppHandle, mPrim, mStage);
}

void ScenarioFromMessage::LoadScenarioFromMessage(isaac_message::ActorGroup::Builder& request)
{
    // handle spawn request
    auto actorCreateRequests = request.getSpawnRequests();
    if (actorCreateRequests.size() > 0)
    {
        for (size_t i = 0; i < actorCreateRequests.size(); i++)
        {
            std::string actorName = actorCreateRequests[i].getName().asString();
            std::string mUsdAsset = actorCreateRequests[i].getPrefab().asString();
            carb::extras::Path mUsdAssetPath(mUsdAsset);
            std::string warningMsg;

            auto prim = omni::usd::UsdUtils::createExternalRefNodeAtPath(
                mStage, mUsdAsset.c_str(), ("/" + actorName).c_str(), warningMsg);

            // Set Pose
            if (prim)
            {
                if (actorCreateRequests[i].hasPose())
                {
                    auto isaacBodypose = actorCreateRequests[i].getPose();
                    auto isaacBodyTranslation = isaacBodypose.getTranslation();
                    auto isaacBodyRotation = isaacBodypose.getRotation().getQ();
                    pxr::GfVec3f pxBodyTranslation(
                        isaacBodyTranslation.getX(), isaacBodyTranslation.getY(), isaacBodyTranslation.getZ());
                    pxr::GfVec4f pxBodyRotation(isaacBodyRotation.getX(), isaacBodyRotation.getY(),
                                                isaacBodyRotation.getZ(), isaacBodyRotation.getW());

                    setTransform(mDynamicControlPtr, prim, pxBodyTranslation * mUnitScale, pxBodyRotation);
                }
                AddObject(actorName, prim);
            }
        }
    }
    // handle destroy request
    auto actorDestroyRequests = request.getDestroyRequests();
    if (actorDestroyRequests.size() > 0)
    {
        for (size_t i = 0; i < actorDestroyRequests.size(); i++)
        {
            // destroy all child gameobject by name
            std::string actorName = actorDestroyRequests[i].asString();
            auto defaultPrim = mStage->GetDefaultPrim();
            auto targetPath = defaultPrim.GetPath().GetString() + "/" + actorName;
            auto prim = mStage->GetPrimAtPath(pxr::SdfPath(targetPath));
            if (prim)
            {
                omni::usd::UsdUtils::removePrim(prim);
                RemoveObject(actorName);
            }
        }
    }
}
void ScenarioFromMessage::AddObject(std::string& actorName, pxr::UsdPrim& prim)
{
    if (mRigidBodiesSink && prim)
    {
        mRigidBodiesSink->addObject(actorName, prim);
    }
    if (mTeleport && prim)
    {
        mTeleport->addObject(actorName, prim);
    }
}
void ScenarioFromMessage::RemoveObject(std::string& actorName)
{
    if (mRigidBodiesSink && actorName != "")
    {
        mRigidBodiesSink->eraseObject(actorName);
    }
    if (mTeleport && actorName != "")
    {
        mTeleport->eraseObject(actorName);
    }
}
void ScenarioFromMessage::setAppHandle(isaac_handle_t appHandle)
{
    mAppHandle = appHandle;
    mTeleport->setAppHandle(appHandle);
    mRigidBodiesSink->setAppHandle(appHandle);
}
}
}
}
