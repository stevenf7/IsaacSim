local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/ros2_bridge")
project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.ros2_bridge.plugin")


    add_files("impl", "plugins")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("iface", "%{root}/include/omni/isaac/ros2_bridge/**")
    add_files("ogn", ogn.nodes_path)

    add_cuda_dependencies()

    add_ogn_dependencies(ogn, {"python/nodes"})

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/carbonite/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/include", 
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/nv_ros2/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_ros2/lib",
        "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin",
        "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/lib",
    }
    -- Add link below to use cyclonedds
    -- "rmw_cyclonedds_cpp"
    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace",
        "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", "usdPhysics",
        "sdf", "usdGeom", "rangeSensorSchema", "isaacSensorSchema",
        "rcutils", "rcl", "rmw", "libstatistics_collector",
        "tf2", "tf2_ros", "rclcpp" , 
        "tf2_msgs__rosidl_typesupport_cpp",
        "geometry_msgs__rosidl_typesupport_cpp",
        "move_base_msgs__rosidl_typesupport_cpp",
        "test_msgs__rosidl_typesupport_cpp",
        "actionlib_msgs__rosidl_typesupport_cpp",
        "diagnostic_msgs__rosidl_typesupport_cpp",
        "pendulum_msgs__rosidl_typesupport_cpp",
        "map_msgs__rosidl_typesupport_cpp",
        "action_msgs__rosidl_typesupport_cpp",
        "rmw_dds_common__rosidl_typesupport_cpp",
        "libstatistics_collector_test_msgs__rosidl_typesupport_cpp",
        "stereo_msgs__rosidl_typesupport_cpp",
        "composition_interfaces__rosidl_typesupport_cpp",
        "statistics_msgs__rosidl_typesupport_cpp",
        "unique_identifier_msgs__rosidl_typesupport_cpp",
        "nav_msgs__rosidl_typesupport_cpp",
        "std_srvs__rosidl_typesupport_cpp",
        "std_msgs__rosidl_typesupport_cpp",
        "rcl_interfaces__rosidl_typesupport_cpp",
        "lifecycle_msgs__rosidl_typesupport_cpp",
        "trajectory_msgs__rosidl_typesupport_cpp",
        "rosgraph_msgs__rosidl_typesupport_cpp",
        "sensor_msgs__rosidl_typesupport_cpp",
        "shape_msgs__rosidl_typesupport_cpp",
        "builtin_interfaces__rosidl_typesupport_cpp",
        "rosidl_typesupport_cpp",
        "visualization_msgs__rosidl_typesupport_cpp",
        "isaac_ros2_messages__rosidl_typesupport_cpp",
        "composition_interfaces__rosidl_typesupport_introspection_cpp",
        "map_msgs__rosidl_typesupport_introspection_cpp",
        "visualization_msgs__rosidl_typesupport_introspection_cpp",
        "sensor_msgs__rosidl_typesupport_introspection_cpp",
        "diagnostic_msgs__rosidl_typesupport_introspection_cpp",
        "std_msgs__rosidl_typesupport_introspection_cpp",
        "test_msgs__rosidl_typesupport_introspection_cpp",
        "statistics_msgs__rosidl_typesupport_introspection_cpp",
        "isaac_ros2_messages__rosidl_typesupport_introspection_cpp",
        "geometry_msgs__rosidl_typesupport_introspection_cpp",
        "move_base_msgs__rosidl_typesupport_introspection_cpp",
        "libstatistics_collector_test_msgs__rosidl_typesupport_introspection_cpp",
        "rcl_interfaces__rosidl_typesupport_introspection_cpp",
        "shape_msgs__rosidl_typesupport_introspection_cpp",
        "lifecycle_msgs__rosidl_typesupport_introspection_cpp",
        "action_msgs__rosidl_typesupport_introspection_cpp",
        "trajectory_msgs__rosidl_typesupport_introspection_cpp",
        "builtin_interfaces__rosidl_typesupport_introspection_cpp",
        "rosgraph_msgs__rosidl_typesupport_introspection_cpp",
        "pendulum_msgs__rosidl_typesupport_introspection_cpp",
        "actionlib_msgs__rosidl_typesupport_introspection_cpp",
        "nav_msgs__rosidl_typesupport_introspection_cpp",
        "tf2_msgs__rosidl_typesupport_introspection_cpp",
        "stereo_msgs__rosidl_typesupport_introspection_cpp",
        "std_srvs__rosidl_typesupport_introspection_cpp",
        "rmw_dds_common__rosidl_typesupport_introspection_cpp",
        "unique_identifier_msgs__rosidl_typesupport_introspection_cpp",
        "vision_msgs__rosidl_typesupport_cpp",
        "vision_msgs__rosidl_typesupport_introspection_cpp",
    }

    filter { "system:linux" }
        disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable"}
        links {"boost_system"}
    filter { "system:windows" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

project_ext_ogn( ext, ogn )
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.ros2_bridge.python",
    module = "_ros2_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/ros2_bridge"
}


repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros2_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ros2_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros2_bridge" },
}

if os.target() == "linux" then
    repo_build.prebuild_copy {
        { "rclpy/*.py", ext.target_dir.."/omni/isaac/rclpy" },
        { "%{root}/_build/target-deps/nv_ros2/lib/lib**", ext.target_dir.."/bin" },
        { "%{root}/_build/target-deps/nv_ros2/lib/python3.7/site-packages", ext.target_dir.."/omni/isaac/rclpy" },
        { "%{root}/_build/target-deps/tinyxml2/lib/lib**", ext.target_dir.."/bin" },
    }
end

if os.target() == "windows" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/nv_ros2/bin/**", ext.target_dir.."/bin" },
    }
end