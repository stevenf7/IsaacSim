// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "IOmniIsaacConveyor.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/settings/ISettings.h>

#include <omni/fabric/IToken.h>
#include <omni/graph/core/OgnHelpers.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IMinimal.h>

#include <algorithm>

const struct carb::PluginImplDesc pluginDesc = { "omni.isaac.conveyor.plugin", "OmniGraph Isaac Conveyor Node plugin.",
                                                 "NVIDIA", carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(pluginDesc, omni::isaac::conveyor::IOmniIsaacConveyor)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry, omni::fabric::IToken, carb::settings::ISettings)
DECLARE_OGN_NODES()

// carbonite interface for this plugin (may contain multiple compute nodes)
void fillInterface(omni::isaac::conveyor::IOmniIsaacConveyor& iface)
{
    iface = {};
}

// compute node plugin interface defined
CARB_EXPORT void carbOnPluginStartup(){ INITIALIZE_OGN_NODES() }

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
}
