// Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS


#ifdef _WIN32
#    pragma warning(push)
#    pragma warning(disable : 4996)
#endif

// clang-format off
#include "UsdPCH.h"
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>

#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/isaac/range_sensor/RangeSensorInterface.h>
#include <omni/isaac/utils/LibraryLoader.h>
#include <omni/kit/IStageUpdate.h>
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
                      omni::physx::IPhysx,
                      carb::tasking::ITasking)
DECLARE_OGN_NODES()

// private stuff
namespace
{
omni::kit::IStageUpdate* g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
std::shared_ptr<Ros2HandleBase> g_defaultHandle;
std::shared_ptr<omni::isaac::utils::LibraryLoader> g_factoryLoader;

Ros2Factory* g_Factory = nullptr;

void onResume(float currentTime, void* userData)
{
    if (!g_defaultHandle->is_valid())
    {
        CARB_LOG_INFO("rcl::init()");
        int argc = 0;
        char** argv = nullptr;

        g_defaultHandle->init(argc, argv);
    }
    else
    {
        CARB_LOG_INFO("ROS2 already initialized");
    }
}

void onStop(void* userData)
{

    if (g_defaultHandle->is_valid())
    {
        CARB_LOG_INFO("rcl::shutdown()");
        g_defaultHandle->shutdown();
    }
}

uint64_t const CARB_ABI getDefaultContextHandle()
{
    return reinterpret_cast<uint64_t>(&g_defaultHandle);
}

Ros2Factory* const CARB_ABI getFactory()
{
    return g_Factory;
}

bool const CARB_ABI getStartupStatus()
{
    if (g_Factory)
    {
        return true;
    }
    return false;
}


}


CARB_EXPORT void carbOnPluginStartup()
{
    char* rosDistro = getenv("ROS_DISTRO");
    if (rosDistro && strcmp(rosDistro, "foxy") == 0)
    {
        g_factoryLoader = std::make_shared<omni::isaac::utils::LibraryLoader>("omni.isaac.ros2_bridge.foxy");
    }
    else if (rosDistro && strcmp(rosDistro, "humble") == 0)
    {
        g_factoryLoader = std::make_shared<omni::isaac::utils::LibraryLoader>("omni.isaac.ros2_bridge.humble");
    }
    else
    {
        CARB_LOG_ERROR("Unsupported ROS_DISTRO or ROS_DISTRO env var not specified: %s", rosDistro);
        return;
    }


    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>();

    omni::kit::StageUpdateNodeDesc desc = { 0 };
    desc.displayName = "IsaacRos2Bridge";
    desc.onResume = onResume;
    desc.onStop = onStop;
    desc.order = 100;
    g_stageUpdateNode = g_stageUpdate->createStageUpdateNode(desc);

    if (g_factoryLoader)
    {
        typedef Ros2Factory* (*createFactory_binding)(void);
        createFactory_binding createFactory = (g_factoryLoader->getSymbol<createFactory_binding>("createFactory"));

        // typedef __typeof__(createFactory) createFactory_binding;
        // std::function<createFactory_binding> createFactory;
        // createFactory = reinterpret_cast<createFactory_binding*>(dlsym(g_factoryLoader->loadedLibrary,
        // "createFactory"));

        if (createFactory)
        {
            g_Factory = (Ros2Factory*)createFactory();
        }
        else
        {
            CARB_LOG_ERROR(
                "Could not load ROS2 Bridge due to missing library dependencies, please make sure your sourced ROS2 workspace has the correct packages/libraries installed");
            return;
        }
    }

    g_defaultHandle = g_Factory->CreateHandle();

    INITIALIZE_OGN_NODES()
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (g_stageUpdateNode)
    {
        g_stageUpdate->destroyStageUpdateNode(g_stageUpdateNode);
        g_stageUpdateNode = nullptr;
    }
    g_defaultHandle.reset();

    RELEASE_OGN_NODES()
    g_factoryLoader.reset();
    if (g_Factory)
    {
        delete g_Factory;
        g_Factory = nullptr;
    }
}

void fillInterface(omni::isaac::ros2_bridge::Ros2Bridge& iface)
{
    using namespace omni::isaac::ros2_bridge;

    memset(&iface, 0, sizeof(iface));
    iface.getDefaultContextHandle = getDefaultContextHandle;
    iface.getFactory = getFactory;
    iface.getStartupStatus = getStartupStatus;
}

#ifdef _WIN32
#    pragma warning(pop)
#endif
