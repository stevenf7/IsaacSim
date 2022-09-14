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

#include "Core/GxfContext.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/fastcache/FastCache.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/gxf_bridge/GxfBridge.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/physx/IPhysxUsdLoad.h>
#include <omni/renderer/IDebugDraw.h>
#include <uuid/uuid.h>

#include <dlfcn.h>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.gxf_bridge.plugin", "Isaac Gxf bridge", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::gxf_bridge::GxfBridge)
CARB_PLUGIN_IMPL_DEPS(carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      omni::syntheticdata::SyntheticData,
                      carb::settings::ISettings,
                      carb::tasking::ITasking,
                      carb::fastcache::FastCache,
                      omni::kit::IStageUpdate,
                      omni::renderer::IDebugDraw,
                      omni::physx::IPhysx,
                      omni::physx::usdparser::IPhysxUsdLoad,
                      omni::isaac::dynamic_control::DynamicControl,
                      omni::isaac::range_sensor::LidarSensorInterface)

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

std::unique_ptr<omni::isaac::gxf_bridge::GxfContext> g_gxf_context_handle;


bool CARB_ABI createDefaultContext(const std::string& basePath,
                                   const std::string& manifestFile,
                                   const std::vector<std::string>& graphFiles)
{


    gxf_result_t error = g_gxf_context_handle->create(basePath, manifestFile, graphFiles);
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    error = g_gxf_context_handle->start();
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    return true;
}
bool CARB_ABI destroyDefaultContext()
{
    gxf_result_t error = g_gxf_context_handle->stop();
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    error = g_gxf_context_handle->destroy();
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    return true;
}

uint64_t const CARB_ABI getDefaultContextHandle()
{
    if (g_gxf_context_handle)
    {
        return g_gxf_context_handle->getContextHandle();
    }
    else
    {
        return 0;
    }
}


void onUpdate(float currentTime, float elapsedSecs, const omni::kit::StageUpdateSettings* settings, void* userData)
{
    // Tick app
    if (!settings->isPlaying)
    {
        return;
    }

    if (g_gxf_context_handle)
    {
        g_gxf_context_handle->tick(elapsedSecs);
    }
}

void onStop(void* userData)
{

    if (g_stage && g_gxf_context_handle)
    {
        g_gxf_context_handle->onStop();
    }
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

    g_gxf_context_handle = std::make_unique<omni::isaac::gxf_bridge::GxfContext>(g_dynamicControl);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "GxfBridge";
    desc.onUpdate = onUpdate;
    desc.onStop = onStop;
    desc.order = 100;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);

    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_gxf_context_handle.reset();
    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);

    RELEASE_OGN_NODES()
}

void fillInterface(omni::isaac::gxf_bridge::GxfBridge& iface)
{
    using namespace omni::isaac::gxf_bridge;

    memset(&iface, 0, sizeof(iface));

    iface.createDefaultContext = createDefaultContext;
    iface.destroyDefaultContext = destroyDefaultContext;
    iface.getDefaultContextHandle = getDefaultContextHandle;
}
