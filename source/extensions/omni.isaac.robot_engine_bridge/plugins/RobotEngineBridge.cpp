// Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include "Core/IsaacApplication.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/fastcache/FastCache.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <messages/uuid.capnp.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/isaac_sensor/IsaacSensor.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/robot_engine_bridge/IsaacCApi.h>
#include <omni/isaac/robot_engine_bridge/IsaacMessage.h>
#include <omni/isaac/robot_engine_bridge/RobotEngineBridge.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxUsdLoad.h>
#include <omni/renderer/IDebugDraw.h>
#include <packages/engine_c_api/isaac_c_api.h>
#include <uuid/uuid.h>

#include <dlfcn.h>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.robot_engine_bridge.plugin", "Isaac Robot Engine bridge",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::robot_engine_bridge::RobotEngineBridge)
CARB_PLUGIN_IMPL_DEPS(carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      omni::syntheticdata::SyntheticData,
                      omni::kit::IViewport,
                      carb::settings::ISettings,
                      carb::tasking::ITasking,
                      carb::fastcache::FastCache,
                      omni::kit::IStageUpdate,
                      omni::renderer::IDebugDraw,
                      omni::physx::IPhysx,
                      omni::physx::usdparser::IPhysxUsdLoad,
                      omni::isaac::dynamic_control::DynamicControl,
                      omni::isaac::range_sensor::LidarSensorInterface,
                      omni::isaac::range_sensor::UltrasonicSensorInterface,
                      omni::isaac::isaac_sensor::ContactSensorInterface,
                      omni::graph::core::IGraphRegistry)

DECLARE_OGN_NODES()

// private stuff
namespace
{
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
carb::dictionary::ISerializer* g_jsonSerializer = nullptr;
omni::isaac::dynamic_control::DynamicControl* g_dynamicControl = nullptr;
carb::dictionary::IDictionary* g_iDict = nullptr;
pxr::UsdStageWeakPtr g_stage = nullptr;

std::unique_ptr<omni::isaac::robot_engine_bridge::IsaacCApi> g_c_api;
std::unique_ptr<omni::isaac::robot_engine_bridge::IsaacApplication> g_application_handle;


bool CARB_ABI createApplication(std::string asset_path,
                                std::string app_file,
                                std::vector<const char*> module_paths,
                                std::vector<const char*> json_files)
{


    isaac_error_t error = g_application_handle->create(asset_path, app_file, module_paths, json_files);
    if (error != isaac_error_t::isaac_error_success)
    {
        return false;
    }
    error = g_application_handle->start();
    if (error != isaac_error_t::isaac_error_success)
    {
        return false;
    }
    return true;
}
bool CARB_ABI destroyApplication()
{
    isaac_error_t error = g_application_handle->stop();
    if (error != isaac_error_t::isaac_error_success)
    {
        return false;
    }
    error = g_application_handle->destroy();
    if (error != isaac_error_t::isaac_error_success)
    {
        return false;
    }
    return true;
}

bool CARB_ABI tickComponent(const std::string& primPath)
{
    if (g_stage)
    {
        return g_application_handle->tickComponent(g_stage->GetPrimAtPath(pxr::SdfPath(primPath)));
    }
    return false;
}
std::string const CARB_ABI getLastError()
{
    if (g_application_handle)
    {
        return g_application_handle->getLastError();
    }
    else
    {
        return "";
    }
}

int64_t const CARB_ABI getSimTimeNano()
{
    if (g_application_handle)
    {
        return g_application_handle->getSimTimeNano();
    }
    else
    {
        return 0;
    }
}

int64_t const CARB_ABI getAppOffsetNano()
{
    if (g_application_handle)
    {
        return g_application_handle->getAppOffsetNano();
    }
    else
    {
        return 0;
    }
}

int64_t const CARB_ABI getAppHandle()
{
    if (g_application_handle)
    {
        return g_application_handle->getAppHandle();
    }
    else
    {
        return 0;
    }
}

void* const CARB_ABI getCApiHandle()
{
    if (g_c_api)
    {
        return g_c_api.get();
    }
    else
    {
        return nullptr;
    }
}

void CARB_ABI initializeStageLoader(const std::string& inputComponent,
                                    const std::string& requestChannelName,
                                    const std::string& cameraRequestChannelName,
                                    const std::string& outputComponent,
                                    const std::string& replyChannelName)
{
    g_application_handle->initializeStageLoader(
        inputComponent, requestChannelName, cameraRequestChannelName, outputComponent, replyChannelName);
}


bool CARB_ABI executeCommand(const std::string& command)
{

    return carb::getCachedInterface<omni::kit::IApp>()->getPythonScripting()->executeString(command.c_str());
}

void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("Isaac Robot Engine Bridge could not find USD stage");
        return;
    }

    g_stage = stage;
    if (g_application_handle)
    {
        g_application_handle->initialize(g_stage);
        g_application_handle->initComponents();
    }
}
void onDetach(void* userData)
{
    // Delete all components
    if (g_application_handle)
    {
        g_application_handle->deleteAllComponents();
    }
}
void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    // Tick app
    if (!settings->isPlaying)
    {
        return;
    }
    if (g_application_handle)
    {
        g_application_handle->tick(elapsedSecs);
    }
}
void onResume(float currentTime, void* userData)
{
}

void onPause(void* userData)
{
}
void onStop(void* userData)
{
    if (g_stage && g_application_handle)
    {
        g_application_handle->onStop();
    }
}
void onPrimAdd(const pxr::SdfPath& primPath, void* userData)
{
    // printf("++ REB: Prim Add: %s\n", primPath,
    //        g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (g_application_handle)
    {
        pxr::UsdPrim addedPrim = g_stage->GetPrimAtPath(primPath);
        if (!addedPrim)
        {
            return;
        }
        // Add the root prim
        if (g_application_handle)
        {
            g_application_handle->onComponentAdd(addedPrim);
        }

        // Check if it has any descendants that need to be added
        pxr::UsdPrimSubtreeRange range = addedPrim.GetDescendants();
        for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            if (g_application_handle)
            {
                g_application_handle->onComponentAdd(prim);
            }
        }
    }
}
void onComponentChange(const pxr::SdfPath& primOrPropertyPath, void* userData)
{
    // printf("++ REB: Prim Change: %s of type %s\n", primPath,
    //        g_stage->GetPrimAtPath(pxr::SdfPath(primPath)).GetTypeName().GetString().c_str());
    if (g_stage && g_application_handle)
    {
        g_application_handle->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    // printf("++ REB: Prim Remove: %s\n", primPath);
    if (g_application_handle)
    {
        g_application_handle->onComponentRemove(primPath);
    }
}
bool publishJsonMessage(std::string node, std::string component, std::string channel, uint64_t typeID, std::string jsonString)
{
    if (g_application_handle)
    {
        return g_application_handle->publishJsonMessage(node, component, channel, typeID, jsonString);
    }
    return false;
}
}


CARB_EXPORT void carbOnPluginStartup()
{
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();
    g_jsonSerializer = carb::getCachedInterface<carb::dictionary::ISerializer>();
    if (!g_jsonSerializer)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::ISerializer interface");
        return;
    }
    g_dynamicControl = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

    if (!g_dynamicControl)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }

    g_iDict = carb::getCachedInterface<carb::dictionary::IDictionary>();

    if (!g_iDict)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::IDictionary interface");
        return;
    }
    g_c_api = std::make_unique<omni::isaac::robot_engine_bridge::IsaacCApi>();

    g_application_handle = std::make_unique<omni::isaac::robot_engine_bridge::IsaacApplication>(
        g_c_api.get(), g_dynamicControl, g_jsonSerializer, g_iDict);


    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacRobotEngineBridge";
    desc.onAttach = onAttach;
    desc.onDetach = onDetach;
    desc.onUpdate = onUpdate;
    desc.onResume = onResume;
    desc.onPause = onPause;
    desc.onStop = onStop;
    desc.onPrimAdd = onPrimAdd;
    desc.onPrimOrPropertyChange = onComponentChange;
    desc.onPrimRemove = onPrimRemove;
    desc.order = 100;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);
    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_c_api.reset();
    g_application_handle.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
    RELEASE_OGN_NODES()
}

void fillInterface(omni::isaac::robot_engine_bridge::RobotEngineBridge& iface)
{
    using namespace omni::isaac::robot_engine_bridge;

    memset(&iface, 0, sizeof(iface));

    iface.createApplication = createApplication;
    iface.destroyApplication = destroyApplication;
    iface.tickComponent = tickComponent;
    iface.getLastError = getLastError;
    iface.initializeStageLoader = initializeStageLoader;
    iface.executeCommand = executeCommand;
    iface.publishJsonMessage = publishJsonMessage;
    iface.getSimTimeNano = getSimTimeNano;
    iface.getAppOffsetNano = getAppOffsetNano;
    iface.getAppHandle = getAppHandle;
    iface.getCApiHandle = getCApiHandle;
}
