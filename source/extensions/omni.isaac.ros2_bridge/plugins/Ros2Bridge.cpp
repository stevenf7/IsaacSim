// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/isaac/ros2_bridge/Ros2Bridge.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <carb/sensors/Sensors.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/kit/IViewport.h>

#include <omni/kit/IStageUpdate.h>

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>
#include <carb/settings/ISettings.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <omni/physx/IPhysx.h>

#include <unordered_map>
#include <string>
#include <vector>
#include <memory>

#include "Core/IsaacApplication.h"
#include "rclcpp/rclcpp.hpp"

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
                      carb::sensors::Sensors,
                      carb::tasking::ITasking,
                      carb::settings::ISettings)

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
omni::physx::IPhysx* g_physx = nullptr;
carb::settings::ISettings* g_settings = nullptr;

std::unique_ptr<omni::isaac::ros2_bridge::IsaacApplication> g_application_handle;


void onAttach(long int stageId, double metersPerUnit, void* userData)
{
    pxr::UsdStageWeakPtr stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
    if (!stage)
    {
        CARB_LOG_ERROR("Isaac ROS2  Bridge could not find USD stage");
        return;
    }

    g_stage = stage;
    if (g_application_handle)
    {
        g_application_handle->initialize(g_stage);
        g_application_handle->setRosState(false);
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
    if (!rclcpp::ok())
    {
        if (g_application_handle->getRosState() == true)
        {
            CARB_LOG_INFO("ROS Master was/is not running, cleaning up any running nodes");
        }
        g_application_handle->setRosState(false);
        g_application_handle->deleteAllComponents();
        g_application_handle->deleteRosNodes();
        return;
    }

    // Tick app
    if (!settings->isPlaying)
    {
        return;
    }

    if (g_application_handle)
    {
        if (g_application_handle->getRosState() == false)
        {
            g_application_handle->initComponents();
            g_application_handle->setRosState(true);
            return;
        }
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
    // Adding prims also initializes ROS nodes, which will cause errors if ROS is not running
    // Only add components if ros state is good
    if (g_application_handle && g_application_handle->getRosState() == true)
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

    if (g_stage && g_application_handle)
    {
        g_application_handle->onComponentChange(g_stage->GetPrimAtPath(primOrPropertyPath));
    }
}

void onPrimRemove(const pxr::SdfPath& primPath, void* userData)
{
    if (g_application_handle)
    {
        g_application_handle->onComponentRemove(primPath);
    }
}
}


void CARB_ABI setUseSimTime(const bool useSimTime)
{
    if (g_application_handle)
    {
        CARB_LOG_INFO("ROS will use %s time for publishers", useSimTime ? "simulation" : "system");
        g_application_handle->setUseSimTime(useSimTime);
    }
}
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
    g_physx = g_framework->acquireInterface<omni::physx::IPhysx>();
    if (!g_physx)
    {
        CARB_LOG_ERROR("Failed to acquire PhysX interface");
        return;
    }
    g_settings = g_framework->acquireInterface<carb::settings::ISettings>();
    if (!g_settings)
    {
        CARB_LOG_ERROR("Failed to acquire Settings interface");
        return;
    }


    g_settings->setDefaultString("/exts/omni.isaac.ros2_bridge/nodeName", "OmniIsaacRos2Bridge");
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
        CARB_LOG_INFO("ROS already initialized");
    }

    g_application_handle = std::make_unique<omni::isaac::ros2_bridge::IsaacApplication>(g_dynamicControl);

    g_settings->setDefaultBool("/exts/omni.isaac.ros2_bridge/useSimTime", true);
    bool useSimTime = g_settings->get<bool>("/exts/omni.isaac.ros2_bridge/useSimTime");
    setUseSimTime(useSimTime);

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacRos2Bridge";
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
    g_application_handle.reset();
    if (rclcpp::ok())
    {
        CARB_LOG_INFO("rclcpp::shutdown()");
        // rclcpp::Time::shutdown();
        rclcpp::shutdown();
        // rclcpp::spinOnce();
        // while (rclcpp::ok())
        // {
        //     CARB_LOG_INFO("SPIN");
        //     rclcpp::spinOnce();
        // }
    }

    g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
}

void fillInterface(omni::isaac::ros2_bridge::Ros2Bridge& iface)
{
    using namespace omni::isaac::ros2_bridge;

    memset(&iface, 0, sizeof(iface));
    iface.setUseSimTime = setUseSimTime;
}
