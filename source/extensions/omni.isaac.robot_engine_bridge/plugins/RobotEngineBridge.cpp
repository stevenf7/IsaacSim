// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <omni/isaac/robot_engine_bridge/RobotEngineBridge.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <carb/sensors/Sensors.h>
#include <carb/syntheticdata/SyntheticData.h>

#include <omni/kit/IStageUpdate.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/fastcache/FastCache.h>
#include <omni/physx/IPhysx.h>
#include <omni/renderer/IDebugDraw.h>

#include <unordered_map>
#include <string>
#include <vector>
#include <memory>

#include <packages/engine_c_api/isaac_c_api.h>

#include <messages/uuid.capnp.h>
#include <uuid/uuid.h>
#include "Core/IsaacMessage.h"
#include "Core/IsaacCApi.h"
#include "Core/IsaacApplication.h"

#include <dlfcn.h>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.robot_engine_bridge.plugin", "Isaac Robot Engine bridge",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::robot_engine_bridge::RobotEngineBridge)
CARB_PLUGIN_IMPL_DEPS(carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      carb::syntheticdata::SyntheticData,
                      carb::sensors::Sensors,
                      carb::settings::ISettings,
                      carb::tasking::ITasking,
                      carb::fastcache::FastCache,
                      omni::kit::IStageUpdate,
                      omni::renderer::IDebugDraw,
                      omni::physx::IPhysx,
                      omni::isaac::dynamic_control::DynamicControl,
                      omni::isaac::range_sensor::LidarSensorInterface,
                      omni::isaac::range_sensor::UltrasonicSensorInterface)

// private stuff
namespace
{
carb::Framework* g_framework = nullptr;
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
std::string const CARB_ABI getLastError()
{
    return g_application_handle->getLastError();
}
void CARB_ABI initializeStageLoader(std::string inputComponent,
                                    std::string requestChannelName,
                                    std::string cameraRequestChannelName,
                                    std::string outputComponent,
                                    std::string replyChannelName)
{
    g_application_handle->initializeStageLoader(
        inputComponent, requestChannelName, cameraRequestChannelName, outputComponent, replyChannelName);
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
        g_application_handle->onComponentAdd(addedPrim);
        // Check if it has any descendants that need to be added
        pxr::UsdPrimSubtreeRange range = addedPrim.GetDescendants();
        for (pxr::UsdPrimSubtreeRange::iterator iter = range.begin(); iter != range.end(); ++iter)
        {
            pxr::UsdPrim prim = *iter;
            g_application_handle->onComponentAdd(prim);
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
}


CARB_EXPORT void carbOnPluginStartup()
{
    g_framework = carb::getFramework();
    g_stageUpdate = g_framework->acquireInterface<omni::kit::IStageUpdate>();
    g_jsonSerializer =
        g_framework->acquireInterface<carb::dictionary::ISerializer>("carb.dictionary.serializer-json.plugin");
    if (!g_jsonSerializer)
    {
        CARB_LOG_ERROR("Failed to acquire carb::dictionary::ISerializer interface");
        return;
    }
    g_dynamicControl = g_framework->acquireInterface<omni::isaac::dynamic_control::DynamicControl>();

    if (!g_dynamicControl)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
        return;
    }

    g_iDict = g_framework->acquireInterface<carb::dictionary::IDictionary>();

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
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_c_api.reset();
    g_application_handle.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
}

void fillInterface(omni::isaac::robot_engine_bridge::RobotEngineBridge& iface)
{
    using namespace omni::isaac::robot_engine_bridge;

    memset(&iface, 0, sizeof(iface));

    iface.createApplication = createApplication;
    iface.destroyApplication = destroyApplication;
    iface.getLastError = getLastError;
    iface.initializeStageLoader = initializeStageLoader;
}
