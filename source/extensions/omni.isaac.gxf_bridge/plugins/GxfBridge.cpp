// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
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
#include <carb/logging/Log.h>

#include <libuuid/uuid.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/gxf_bridge/GxfBridge.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>

#include <dlfcn.h>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.gxf_bridge.plugin", "Isaac Gxf bridge", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::gxf_bridge::GxfBridge)
CARB_PLUGIN_IMPL_DEPS(omni::kit::IStageUpdate, omni::isaac::dynamic_control::DynamicControl)

DECLARE_OGN_NODES()

// private stuff
namespace
{
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
omni::isaac::core_nodes::CoreNodes* g_coreNodeFramework = nullptr;
uint64_t g_gxf_context_handle = 0;
std::shared_ptr<omni::isaac::gxf_bridge::GxfContext> g_gxf_context;


bool CARB_ABI createDefaultContext(const std::string& basePath,
                                   const std::string& manifestFile,
                                   const std::vector<std::string>& graphFiles,
                                   const std::string& clockEntity,
                                   const std::string& clockComponent,
                                   const std::string& atlasEntity,
                                   const std::string& atlasComponent)
{

    if (g_gxf_context->create() != gxf_result_t::GXF_SUCCESS)
    {
        g_gxf_context->destroy();
        return false;
    }
    if (g_gxf_context->loadManifest(basePath, manifestFile) != gxf_result_t::GXF_SUCCESS)
    {
        g_gxf_context->destroy();
        return false;
    }
    if (g_gxf_context->loadGraphsFromFile(graphFiles) != gxf_result_t::GXF_SUCCESS)
    {
        g_gxf_context->destroy();
        return false;
    }
    if (g_gxf_context->start(clockEntity, clockComponent, atlasEntity, atlasComponent) != gxf_result_t::GXF_SUCCESS)
    {
        g_gxf_context->stop();
        g_gxf_context->destroy();
        return false;
    }
    g_gxf_context_handle = g_coreNodeFramework->addHandle(&g_gxf_context);

    return true;
}
bool CARB_ABI destroyDefaultContext()
{
    gxf_result_t error = g_gxf_context->stop();
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    error = g_gxf_context->destroy();
    if (error != gxf_result_t::GXF_SUCCESS)
    {
        return false;
    }
    g_coreNodeFramework->removeHandle(g_gxf_context_handle);
    g_gxf_context_handle = 0;

    return true;
}

uint64_t const CARB_ABI getDefaultContextHandle()
{
    if (g_gxf_context && g_gxf_context_handle)
    {
        return g_gxf_context_handle;
    }
    else
    {
        return 0;
    }
}

}


CARB_EXPORT void carbOnPluginStartup()
{
    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();


    g_gxf_context = std::make_unique<omni::isaac::gxf_bridge::GxfContext>();
    g_coreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();

    if (!g_coreNodeFramework)
    {
        CARB_LOG_ERROR("Failed to acquire omni::isaac::core_nodes::CoreNodes interface");
        return;
    }

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "GxfBridge";
    desc.order = 100;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);

    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    g_gxf_context.reset();
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
