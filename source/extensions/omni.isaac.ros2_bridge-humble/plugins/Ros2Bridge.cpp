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

#include "rclcpp/rclcpp.hpp"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>

#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/ros2_bridge/Ros2Bridge.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/IViewport.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdTypes.h>

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.ros2_bridge.plugin", "Isaac ROS2 bridge", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::ros2_bridge::Ros2Bridge)
CARB_PLUGIN_IMPL_DEPS(carb::dictionary::ISerializer,
                      carb::dictionary::IDictionary,
                      omni::isaac::dynamic_control::DynamicControl,
                      omni::kit::IStageUpdate,
                      omni::isaac::range_sensor::LidarSensorInterface,
                      omni::syntheticdata::SyntheticData,
                      omni::kit::IViewport,
                      omni::physx::IPhysx,
                      carb::tasking::ITasking,
                      carb::settings::ISettings)
DECLARE_OGN_NODES()

// private stuff
namespace
{
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
carb::settings::ISettings* g_settings = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;

void onResume(float currentTime, void* userData)
{
    if (!rclcpp::ok())
    {
        CARB_LOG_INFO("rclcpp::init()");
        int argc = 0;
        char** argv = nullptr;
        using rclcpp::contexts::get_global_default_context;
        get_global_default_context()->init(argc, argv);
        // rclcpp::Time::init();
    }
    else
    {
        CARB_LOG_INFO("ROS2 already initialized");
    }
}

void onStop(void* userData)
{

    if (rclcpp::ok())
    {
        CARB_LOG_INFO("rclcpp::shutdown()");
        // rclcpp::Time::shutdown();
        rclcpp::shutdown();
    }
}
}


CARB_EXPORT void carbOnPluginStartup()
{

    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();

    g_settings = carb::getCachedInterface<carb::settings::ISettings>();
    if (!g_settings)
    {
        CARB_LOG_ERROR("Failed to acquire Settings interface");
        return;
    }


    g_settings->setDefaultString("/exts/omni.isaac.ros2_bridge/nodeName", "OmniIsaacRos2Bridge");

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacRos2Bridge";
    desc.onResume = onResume;
    desc.onStop = onStop;
    desc.order = 100;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);

    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (g_stageUpdateNode)
    {
        g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
        g_stageUpdateNode = nullptr;
    }

    RELEASE_OGN_NODES()
}

void fillInterface(omni::isaac::ros2_bridge::Ros2Bridge& iface)
{
    using namespace omni::isaac::ros2_bridge;

    memset(&iface, 0, sizeof(iface));
}
