// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
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

#include <isaacsim/robot/wheeled_robots/IWheeledRobots.h>
#include <omni/fabric/IToken.h>
#include <omni/graph/core/NodeTypeRegistrar.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IMinimal.h>

namespace
{

/**
 * @brief Plugin descriptor for the Wheeled Robots module
 */
const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.robot.wheeled_robots",
                                                    "Isaac Sim Wheeled Robot Controllers", "NVIDIA",
                                                    carb::PluginHotReload::eEnabled, "dev" };

} // anonymous namespace

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::robot::wheeled_robots::IWheeledRobots)
CARB_PLUGIN_IMPL_DEPS(omni::graph::core::IGraphRegistry, omni::fabric::IToken, carb::settings::ISettings)
DECLARE_OGN_NODES()

/**
 * @brief Fills the interface with required functionality
 */
void fillInterface(isaacsim::robot::wheeled_robots::IWheeledRobots& iface)
{
    iface = {};
}

CARB_EXPORT void carbOnPluginStartup(){ INITIALIZE_OGN_NODES() }

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
}
