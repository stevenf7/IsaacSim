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
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include "ros/ros.h"
#undef BOOST_BIND_GLOBAL_PLACEHOLDERS

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/tasking/ITasking.h>

#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdTypes.h>

#include <DynamicControl.h>
#include <RosBridge.h>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.ros_bridge.plugin", "Isaac ROS bridge", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::ros_bridge::RosBridge)
CARB_PLUGIN_IMPL_DEPS(carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      omni::isaac::dynamic_control::DynamicControl,
                      omni::kit::IStageUpdate,
                      omni::syntheticdata::SyntheticData,
                      omni::physx::IPhysx,
                      carb::tasking::ITasking,
                      carb::settings::ISettings,
                      omni::graph::core::IGraphRegistry,
                      omni::fabric::IToken)
DECLARE_OGN_NODES()

// private stuff
namespace
{
}

CARB_EXPORT void carbOnPluginStartup()
{
    auto settings = carb::getCachedInterface<carb::settings::ISettings>();
    if (!settings)
    {
        CARB_LOG_ERROR("Failed to acquire Settings interface");
        return;
    }

    settings->setDefaultString("/exts/omni.isaac.ros_bridge/nodeName", "OmniIsaacRosBridge");
    std::string nodeName = settings->get<const char*>("/exts/omni.isaac.ros_bridge/nodeName");
    if (nodeName.size() == 0)
    {
        nodeName = "OmniIsaacRosBridge";
    }
    // This node is needed for the bridge omnigraph nodes to work properly
    if (!ros::isInitialized())
    {
        CARB_LOG_INFO("ros::init()");
        int argc = 0;
        char** argv = nullptr;
        ros::init(argc, argv, nodeName, ros::init_options::NoSigintHandler);
        ros::Time::init();
    }
    else
    {
        CARB_LOG_INFO("ROS already initialized");
    }
    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{

    if (ros::isInitialized())
    {
        CARB_LOG_INFO("ros::shutdown()");
        ros::Time::shutdown();
        ros::shutdown();
    }
    RELEASE_OGN_NODES()
}

void fillInterface(omni::isaac::ros_bridge::RosBridge& iface)
{
    using namespace omni::isaac::ros_bridge;

    memset(&iface, 0, sizeof(iface));
}
