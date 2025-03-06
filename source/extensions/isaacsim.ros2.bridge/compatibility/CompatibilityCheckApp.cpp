// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
// A simple executable to check if the users system is compatible with ROS 2

#include <isaacsim/ros2/bridge/LibraryLoader.h>
#include <isaacsim/ros2/bridge/Ros2Distro.h>
#include <rcl/error_handling.h>
#include <rcl/rcl.h>


int main(int argc, char* argv[])
{
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
#endif
        "rcl_logging_spdlog",
        "rosidl_typesupport_c",
        "builtin_interfaces__rosidl_generator_c",
        "builtin_interfaces__rosidl_typesupport_c",
        "rcl_interfaces__rosidl_typesupport_c",
        "rcl_interfaces__rosidl_generator_c",
        "rcl",
    };

    char* rosDistro = getenv("ROS_DISTRO");

    if (!rosDistro || !isaacsim::ros2::bridge::isRos2DistroSupported(rosDistro))
    {
        CARB_LOG_ERROR(
            "Unsupported ROS_DISTRO '%s' - Supported distributions: Humble, Jazzy", rosDistro ? rosDistro : "null");
        return EXIT_FAILURE;
    }

    const auto distro = isaacsim::ros2::bridge::stringToRos2Distro(rosDistro).value();
    if (distro == isaacsim::ros2::bridge::Ros2Distro::eHumble)
    {
        lib_list.insert(lib_list.begin() + 5, std::string("ament_index_cpp"));
        lib_list.insert(lib_list.begin() + 8, std::string("rcl_logging_interface"));
        lib_list.insert(lib_list.end(), std::string("lifecycle_msgs__rosidl_generator_c"));
        lib_list.insert(lib_list.end(), std::string("lifecycle_msgs__rosidl_typesupport_c"));
        lib_list.insert(lib_list.end(), std::string("rcl_lifecycle"));
    }

    isaacsim::core::utils::MultiLibraryLoader g_backupLibLoader;
    std::string path = "";
    if (argc == 2)
    {
        path = argv[1];
    }
    for (std::string lib : lib_list)
    {
        if (g_backupLibLoader.LoadLibrary(lib, path).get()->loadedLibrary == nullptr)
        {
            exit(EXIT_FAILURE);
        }
    }
    printf("Checking to see if RMW can be loaded:\n");
    auto rcl = std::make_shared<isaacsim::core::utils::LibraryLoader>("rcl", path, false);
    auto rcutils = std::make_shared<isaacsim::core::utils::LibraryLoader>("rcutils", path, false);

    rcl_init_options_t initOptions = rcl->callSymbolWithArg<rcl_init_options_t>("rcl_get_zero_initialized_init_options");
    auto allocator = rcutils->callSymbolWithArg<rcutils_allocator_t>("rcutils_get_default_allocator");
    rcl_ret_t rc = rcl->callSymbolWithArg<rcl_ret_t>("rcl_init_options_init", &initOptions, allocator);
    if (rc != RCL_RET_OK)
    {
        do
        {
            printf("%s\n", rcutils->callSymbolWithArg<rcutils_error_string_t>("rcutils_get_error_string").str);
            rcutils->callSymbolWithArg<rcutils_error_string_t>("rcutils_reset_error");
        } while (0);
        printf("RMW was not loaded\n");
        exit(EXIT_FAILURE);
    }

    rcl->callSymbolWithArg<rcl_init_options_t>("rcl_init_options_fini", &initOptions);

    return 0;
}
