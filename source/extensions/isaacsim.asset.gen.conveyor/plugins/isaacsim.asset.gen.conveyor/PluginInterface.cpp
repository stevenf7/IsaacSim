// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/settings/ISettings.h>

#include <isaacsim/asset/gen/conveyor/IOmniIsaacConveyor.h>
#include <omni/fabric/IToken.h>
#include <omni/graph/core/OgnHelpers.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IMinimal.h>

#include <algorithm>

/**
 * @brief Plugin descriptor for the conveyor belt plugin
 */
const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.asset.gen.conveyor.plugin",
                                                    "OmniGraph Isaac Conveyor Node plugin.", "NVIDIA",
                                                    carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::asset::gen::conveyor::IOmniIsaacConveyor)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry, omni::fabric::IToken, carb::settings::ISettings)
DECLARE_OGN_NODES()

/**
 * @brief Fills the interface implementation
 * @param iface Interface to initialize
 */
void fillInterface(isaacsim::asset::gen::conveyor::IOmniIsaacConveyor& iface)
{
    iface = {};
}

/**
 * @brief Plugin startup handler
 */
CARB_EXPORT void carbOnPluginStartup(){ INITIALIZE_OGN_NODES() }

/**
 * @brief Plugin shutdown handler
 */
CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
}
