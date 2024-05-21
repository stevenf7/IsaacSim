// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
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
#include <pch/UsdPCH.h>
#include <pxr/usd/usd/inherits.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/dictionary/DictionaryUtils.h>
#include <carb/logging/Log.h>
#include <carb/tasking/ITasking.h>
#include <carb/tokens/ITokens.h>
#include <carb/tokens/TokensUtils.h>

#include <experimental/filesystem>
#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/graph/core/iComputeGraph.h>
#include <omni/graph/core/ogn/Registration.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
#include <omni/kit/syntheticdata/SyntheticData.h>
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdTypes.h>

#include <DynamicControl.h>
#include <LibraryLoader.h>
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
                      omni::syntheticdata::SyntheticData,
                      omni::physx::IPhysx,
                      carb::tasking::ITasking,
                      carb::tokens::ITokens)
DECLARE_OGN_NODES()

// private stuff
namespace
{
omni::kit::StageUpdatePtr g_stageUpdate = nullptr;
omni::kit::StageUpdateNode* g_stageUpdateNode = nullptr;
std::shared_ptr<Ros2HandleBase> g_defaultHandle;
std::shared_ptr<omni::isaac::utils::LibraryLoader> g_factoryLoader;
omni::isaac::utils::MultiLibraryLoader g_backupLibLoader;
Ros2Factory* g_Factory = nullptr;
std::string g_extensionPath;

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
    if (g_Factory && g_defaultHandle)
    {
        return true;
    }
    return false;
}


}


CARB_EXPORT void carbOnPluginStartup()
{
    omni::kit::IApp* app = carb::getCachedInterface<omni::kit::IApp>();
    std::vector<std::string> lib_list = {
        "rcutils",
        "rosidl_runtime_c",
        "rmw",
        "yaml",
        "rcl_yaml_param_parser",
        "rcpputils",
        "rmw_implementation",
#ifndef _WIN32
        "spdlog",
        "tracetools",
#endif
        "rcl_logging_spdlog",
        "rosidl_typesupport_c",
        "builtin_interfaces__rosidl_generator_c",
        "builtin_interfaces__rosidl_typesupport_c",
        "rcl_interfaces__rosidl_typesupport_c",
        "rcl_interfaces__rosidl_generator_c",
        "rcl",
        "action_msgs__rosidl_typesupport_c",
        "std_msgs__rosidl_generator_c",
        "geometry_msgs__rosidl_generator_c",
        "geometry_msgs__rosidl_typesupport_c",
        "unique_identifier_msgs__rosidl_generator_c",
        "unique_identifier_msgs__rosidl_typesupport_c",
        "tf2_msgs__rosidl_typesupport_c",
        "tf2_msgs__rosidl_generator_c",
        "nav_msgs__rosidl_typesupport_c",
        "nav_msgs__rosidl_generator_c",
        "std_msgs__rosidl_typesupport_c",
        "std_msgs__rosidl_generator_c",
        "rosgraph_msgs__rosidl_typesupport_c",
        "rosgraph_msgs__rosidl_generator_c",
        "sensor_msgs__rosidl_typesupport_c",
        "sensor_msgs__rosidl_generator_c",
        "rcl_action",
        "lifecycle_msgs__rosidl_generator_c",
        "lifecycle_msgs__rosidl_typesupport_c",
        "vision_msgs__rosidl_typesupport_c",
        "vision_msgs__rosidl_generator_c",
        "ackermann_msgs__rosidl_generator_c",
        "ackermann_msgs__rosidl_typesupport_c",
        // "fastcdr",
        // "tinyxml2",
        // "crypto",
        // "ssl",
        // "fastrtps",
        // "rmw_dds_common",
        // "rmw_fastrtps_shared_cpp",
        // "rosidl_typesupport_fastrtps_c",
        // "rosidl_typesupport_fastrtps_cpp",
        // "rosidl_typesupport_cpp",
        // "rmw_dds_common__rosidl_typesupport_cpp",
        // "rmw_fastrtps_cpp",
    };

    char* rosDistro = getenv("ROS_DISTRO");

    if (strcmp(rosDistro, "humble") == 0)
    {
        lib_list.insert(lib_list.begin() + 5, std::string("ament_index_cpp"));
        lib_list.insert(lib_list.begin() + 8, std::string("rcl_logging_interface"));
        lib_list.insert(lib_list.end(), std::string("rcl_lifecycle"));
    }
    if (strcmp(rosDistro, "foxy") == 0)
    {
        CARB_LOG_WARN("Support for ROS 2 Foxy is deprecated and will be removed in a future release");
    }
    // attempt to load a ros library
    // if it fails, force load internal distro
    if (rosDistro && strcmp(rosDistro, "foxy") != 0 && strcmp(rosDistro, "humble") != 0)
    {
        CARB_LOG_ERROR("Unsupported ROS_DISTRO or ROS_DISTRO env var not specified: %s", rosDistro);
        return;
    }
    else
    {
        // load test library, print error if it fails
        auto temp_loader = std::make_shared<omni::isaac::utils::LibraryLoader>("rosidl_runtime_c", "", false);
        if (temp_loader->loadedLibrary == carb::extras::kInvalidLibraryHandle)
        {
#ifdef _WIN32
            app->printAndLog(
                "Loading rosidl_runtime_c.dll from sourced ROS_DISTRO failed, falling back to internal libraries.");
#else
            app->printAndLog(
                "Loading librosidl_runtime_c.so from sourced ROS_DISTRO failed, falling back to internal libraries.");
#endif

            carb::tokens::ITokens* tokens = carb::getCachedInterface<carb::tokens::ITokens>();
            std::experimental::filesystem::path p = carb::tokens::resolveString(tokens, "${app}");
            g_extensionPath =
                p.parent_path().string() + "/exts/omni.isaac.ros2_bridge/" + std::string(rosDistro) + "/lib/";

            // Try and load internal lib, this will fail if ENV vars are not set correctly due to dependency tree
            // Do not print lib specific error
            auto temp_loader =
                std::make_shared<omni::isaac::utils::LibraryLoader>("rosidl_runtime_c", g_extensionPath, true);
            if (temp_loader->loadedLibrary == carb::extras::kInvalidLibraryHandle)
            {
                CARB_LOG_WARN(
                    "Could not load ROS2 Bridge due to missing library dependencies, please make sure your sourced ROS2 workspace has the correct packages/libraries installed");
                return;
            }
            for (std::string lib : lib_list)
            {
                g_backupLibLoader.LoadLibrary(lib, g_extensionPath);
            }
        }
        g_factoryLoader =
            std::make_shared<omni::isaac::utils::LibraryLoader>("omni.isaac.ros2_bridge." + std::string(rosDistro));
    }


    g_stageUpdate = carb::getCachedInterface<omni::kit::IStageUpdate>()->getStageUpdate();

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

        if (createFactory)
        {
            g_Factory = (Ros2Factory*)createFactory();
        }
        else
        {
            CARB_LOG_WARN(
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
