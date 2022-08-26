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
#include "ScenarioFromMessage.h"

#include "../Actuator/Teleport.h"
#include "../Core/IsaacComponent.h"
#include "../Monitor/RigidBodiesSink.h"

#include <carb/InterfaceUtils.h>
#include <carb/filesystem/IFileSystem.h>
#include <carb/profiler/Profile.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/robot_engine_bridge/IsaacConversions.h>
#include <omni/isaac/utils/Transforms.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <robotEngineBridgeSchema/robotEngineRigidBodySink.h>
#include <robotEngineBridgeSchema/robotEngineTeleport.h>

#include <memory>
#include <string>
#include <vector>

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
                                     const pxr::RobotEngineBridgeSchemaRobotEngineBridgeComponent& prim,
                                     pxr::UsdStageWeakPtr stage)
{
    IsaacComponent::initialize(isaacCApiPtr, appHandle, prim, stage);
    initSubComponents();
    onComponentChange();
}

void ScenarioFromMessage::tick()
{
    CARB_PROFILE_ZONE(0, "REB ScenarioFromMessage Tick");

    IsaacMessage<isaac_message::ActorGroup> actorGroup;

    {
        // Receive current command
        MessageHeader header;
        if (checkErrorCode(receive(mInputComponent, mRequestChannelName, header, actorGroup)))
        {
            auto actorGroupProto = actorGroup.getProto();
            LoadScenarioFromMessage(actorGroupProto);
        }
    }
    mTeleport->updateTimestamp(mTimeSeconds, mTimeDelta, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
    mTeleport->tick();

    mRigidBodiesSink->updateTimestamp(mTimeSeconds, mTimeDelta, mTimeNanoSeconds, mTimeDifferenceNanoSeconds);
    mRigidBodiesSink->tick();
    mRigidBodiesSink->publishAllMessages();
}

void ScenarioFromMessage::onStart()
{
    onComponentChange();
}

void ScenarioFromMessage::onComponentChange()
{

    IsaacComponent::onComponentChange();
    const pxr::RobotEngineBridgeSchemaRobotEngineScenarioFromMessage& typedPrim =
        (pxr::RobotEngineBridgeSchemaRobotEngineScenarioFromMessage)mPrim;

    isaac::utils::safeGetAttribute(typedPrim.GetInputComponentAttr(), mInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetInputChannelAttr(), mRequestChannelName);

    std::string teleportInputComponent = "input";
    std::string teleportInputChannel = "teleport";

    std::string rigidBodySinkOutputComponent = "output";
    std::string rigidBodySinkOutputChannel = "bodies";

    isaac::utils::safeGetAttribute(typedPrim.GetTeleportInputComponentAttr(), teleportInputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetTeleportInputChannelAttr(), teleportInputChannel);

    isaac::utils::safeGetAttribute(typedPrim.GetRigidBodySinkOutputComponentAttr(), rigidBodySinkOutputComponent);
    isaac::utils::safeGetAttribute(typedPrim.GetRigidBodySinkOutputChannelAttr(), rigidBodySinkOutputChannel);

    mTeleport->updateComponent(teleportInputComponent, teleportInputChannel);
    mRigidBodiesSink->updateComponent(rigidBodySinkOutputComponent, rigidBodySinkOutputChannel);
    mInvUnitScale = 1.0 / UsdGeomGetStageMetersPerUnit(mStage);
}
void ScenarioFromMessage::initSubComponents()
{

    mTeleport = std::make_unique<Teleport>(mDynamicControlPtr);
    mTeleport->initialize(mIsaacCApiPtr, mAppHandle, mPrim, mStage);

    mRigidBodiesSink = std::make_unique<RigidBodiesSink>(mDynamicControlPtr);
    mRigidBodiesSink->initialize(mIsaacCApiPtr, mAppHandle, mPrim, mStage);
}

void ScenarioFromMessage::LoadScenarioFromMessage(isaac_message::ActorGroup::Reader& request)
{
    // handle spawn request
    auto actorCreateRequests = request.getSpawnRequests();
    if (actorCreateRequests.size() > 0)
    {
        for (size_t i = 0; i < actorCreateRequests.size(); i++)
        {
            std::string actorName = actorCreateRequests[i].getName();
            std::string mUsdAsset = actorCreateRequests[i].getPrefab();
            carb::extras::Path mUsdAssetPath(mUsdAsset);
            std::string warningMsg;
            // make name an absolute path if it is not already.
            if (actorName[0] != '/')
            {
                actorName = "/" + actorName;
            }
            CARB_LOG_INFO("spawn %s %s", actorName.c_str(), mUsdAsset.c_str());
            auto prim = omni::usd::UsdUtils::createExternalRefNodeAtPath(
                mStage, mUsdAsset.c_str(), actorName.c_str(), warningMsg, false);
            if (warningMsg.size() > 0)
            {
                CARB_LOG_WARN("%s", warningMsg.c_str());
            }
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

                    isaac::utils::transforms::setTransform(
                        mDynamicControlPtr, prim, pxBodyTranslation * mInvUnitScale, toGfQuatf(isaacBodyRotation));
                }
                AddObject(actorName, prim);
            }
            else
            {
                CARB_LOG_WARN("Could not create %s", actorName.c_str());
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
            std::string actorName = actorDestroyRequests[i];
            // make name an absolute path if it is not already.
            if (actorName[0] != '/')
            {
                actorName = "/" + actorName;
            }
            auto prim = mStage->GetPrimAtPath(pxr::SdfPath(actorName));

            CARB_LOG_INFO("Destroy %s", actorName.c_str());
            if (prim)
            {
                omni::usd::UsdUtils::removePrim(prim);
                RemoveObject(actorName);
            }
            else
            {
                CARB_LOG_WARN("Could not destroy %s, actor doesn't exist", actorName.c_str());
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
