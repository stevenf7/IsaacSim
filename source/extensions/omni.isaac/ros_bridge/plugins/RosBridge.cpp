// Copyright (c) 2019-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#define CARB_EXPORTS
#include <omni/isaac/ros_bridge/RosBridge.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IStageUpdate.h>
#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/input/IInput.h>
#include <carb/logging/Log.h>
#include <carb/physics/usd/Physics.h>
#include <carb/physics/usd/PhysicsUsd.h>
#include <carb/physx/physx.h>
#include <carb/settings/ISettings.h>
#include "RosManager.h"
#include "RosGlobals.h"

#include <inttypes.h> // print 64 bit pointers
#include <memory>

using namespace carb::physics::usdparser;
using namespace omni::isaac::ros_bridge;

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.ros_bridge.plugin", "Isaac ROS Bridge", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };
CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::ros_bridge::RosBridge)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IStageUpdate,
                      carb::physics::PhysX,
                      carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      omni::isaac::dynamic_control::DynamicControl)

namespace
{
carb::Framework* g_framework = nullptr;
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
static pxr::UsdStageRefPtr g_stage = nullptr;
carb::physics::PhysX* g_physX = nullptr;
carb::dictionary::ISerializer* g_jsonSerializer = nullptr;
carb::dictionary::IDictionary* g_iDict = nullptr;
omni::isaac::dynamic_control::DynamicControl* g_dynamicControl = nullptr;
carb::settings::ISettings* g_settings = nullptr;

std::unique_ptr<RosManager> Manager;
std::unique_ptr<RosGlobals> Globals;

static void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    // CARB_LOG_INFO("onAttach RosBridge");

    // try and find USD stage from Id
    pxr::UsdStageRefPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

    if (!stage)
    {
        CARB_LOG_ERROR("Isaac RosBridge could not find USD stage");
        return;
    }

    g_stage = stage;

    Globals = std::make_unique<omni::isaac::ros_bridge::RosGlobals>();
    Globals->stage = g_stage;
    Globals->dynamic_control = g_dynamicControl;
    Globals->json_serializer = g_jsonSerializer;
    Globals->idict = g_iDict;
    Globals->stageUnits = UsdGeomGetStageMetersPerUnit(g_stage);

    Manager = std::make_unique<RosManager>(Globals.get());
    Manager->start();
}

void onDetach(void* userData)
{
    // CARB_LOG_INFO("onDetach RosBridge");
    Manager->stop();
    Manager.reset();
    Manager = nullptr;
}

void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    if (!settings->isPlaying)
    {
        return;
    }
    // CARB_LOG_INFO("Tick: %f - %f", currentTime, elapsedSecs);
#if 1
    // dt will run in realtime
    Manager->tick(elapsedSecs);
#else
    // to run in physics time:
    const float timestepsPerSecond =
        g_settings->isAccessibleAs(carb::dictionary::ItemType::eFloat, ("/physics/timeStepsPerSecond")) ?
            g_settings->getAsFloat("/physics/timeStepsPerSecond") :
            60.0f;
    const float fixedTimeStep = 1.0f / timestepsPerSecond;
    Manager->tick(fixedTimeStep);
#endif
}


void onResume(float currentTime, void* userData)
{
    // CARB_LOG_INFO("onResume RosBridge");
    // Empty
}

void onPause(void* userData)
{
    // CARB_LOG_INFO("onPause RosBridge");
    // Empty
}

} // anonymous namespace

using namespace omni::isaac;

CARB_EXPORT void carbOnPluginStartup()
{
    g_framework = carb::getFramework();
    g_stageUpdate = g_framework->acquireInterface<omni::kit::IStageUpdate>();

    g_jsonSerializer =
        carb::getFramework()->acquireInterface<carb::dictionary::ISerializer>("carb.dictionary.serializer-json.plugin");

    if (!g_jsonSerializer)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::ISerializer interface");
        return;
    }

    g_iDict = carb::getFramework()->acquireInterface<carb::dictionary::IDictionary>();

    if (!g_iDict)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::IDictionary interface");
        return;
    }


    g_physX = g_framework->acquireInterface<carb::physics::PhysX>();

    if (!g_physX)
    {
        CARB_LOG_ERROR("Failed to acquire carb::physics::PhysX interface");
        return;
    }

    g_dynamicControl = g_framework->acquireInterface<omni::isaac::dynamic_control::DynamicControl>();

    if (!g_dynamicControl)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }
    g_settings = carb::getFramework()->acquireInterface<carb::settings::ISettings>();


    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacRosBridge";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onResume = onResume;
    desc.onPause = onPause;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (Manager)
    {
        Manager->stop();
        Manager = nullptr;
    }

    Globals = nullptr;
    g_stage = nullptr;
    g_physX = nullptr;

    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
}


IsaacHandle addRosNode()
{
    return Manager->addNode();
}

bool deleteRosNode(IsaacHandle node_handle)
{
    return Manager->deleteNode(node_handle);
}

IsaacHandle addRosEvent(IsaacHandle node_handle,
                        const std::vector<std::string> paths,
                        std::string topic,
                        const int queue_size,
                        RosMessageType message_type,
                        RosEventType event_type)
{
    return Manager->addEvent(node_handle, paths, topic, queue_size, message_type, event_type);
}

bool deleteRosEvent(IsaacHandle node_handle, IsaacHandle event_handle)
{
    return Manager->deleteEvent(node_handle, event_handle);
}

void setClockState(const bool state)
{
    Manager->setClockState(state);
}

std::string getJsonString()
{
    return Manager->getJsonString();
}

void parseJsonString(std::string json_config)
{
    Manager->parseJsonString(json_config);
}

void fillInterface(omni::isaac::ros_bridge::RosBridge& iface)
{
    iface.addRosNode = addRosNode;
    iface.addRosEvent = addRosEvent;
    iface.deleteRosNode = deleteRosNode;
    iface.deleteRosEvent = deleteRosEvent;
    iface.setClockState = setClockState;
    iface.getJsonString = getJsonString;
    iface.parseJsonString = parseJsonString;
}
