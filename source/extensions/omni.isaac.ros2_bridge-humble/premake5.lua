local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/ros2_bridge-humble")
-- This is a workaround to have two projects that write the same python module. 
ogn.import_path = "omni/isaac/ros2_bridge"
ogn.module = "omni.isaac.ros2_bridge"
ogn.python_target_path = ext.target_dir.."/"..ogn.import_path
ogn.python_tests_target_path = ogn.python_target_path.."/tests"
ogn.icon_target_path="%{root}/_build/%{platform}/%{config}/exts/omni.isaac.ros2_bridge/temp"
project_ext (ext)

dependson { "omni.isaac.ros2_bridge" }

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.ros2_humble_bridge.plugin")

    cppdialect "C++17"
    disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable", "error=deprecated-declarations"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/ros2_bridge/**")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("ogn", ogn.nodes_path)

    add_cuda_dependencies()

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.10",
        "%{root}/_build/target-deps/nv_ros2_humble/include",
        "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_runtime_cpp",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_ros2_humble/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/lib",
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
        "test_msgs__rosidl_typesupport_cpp",
        "actionlib_msgs__rosidl_typesupport_cpp",
        "diagnostic_msgs__rosidl_typesupport_cpp",
        "pendulum_msgs__rosidl_typesupport_cpp",
        "map_msgs__rosidl_typesupport_cpp",
        "action_msgs__rosidl_typesupport_cpp",
        "rmw_dds_common__rosidl_typesupport_cpp",
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
    project_name = "omni.isaac.ros2_humble_bridge.python",
    module = "_ros2_humble_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/ros2_bridge"
}

-- This is a WAR so that we can copy the correctly named icons
-- filter { "configurations:debug" }
--     os.mkdir (root.."/_build/"..os.target().."-x86_64/".."debug".."/exts/omni.isaac.ros2_bridge/ogn")
-- filter { "configurations:release" }
--     os.mkdir (root.."/_build/"..os.target().."-x86_64/".."release".."/exts/omni.isaac.ros2_bridge/ogn")
-- filter {}
repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros2_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ros2_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    -- This is a WAR so that we can copy the correctly named icons
    -- { "%{root}/_build/%{platform}/%{config}/exts/omni.isaac.ros2_bridge/omni/isaac/ros2_bridge/ogn", ext.target_dir.."/omni/isaac/ros2_bridge/ogn" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros2_bridge" },
    { "rclpy/*.py", ext.target_dir.."/omni/isaac/rclpy" },
    { "%{root}/_build/target-deps/nv_ros2_humble/lib/lib**", ext.target_dir.."/bin" },
    { "%{root}/_build/target-deps/nv_ros2_humble/lib/python3.10/site-packages", ext.target_dir.."/omni/isaac/rclpy" },
    {"%{root}/_build/target-deps/nv_ros2_humble/local/lib/python3.10/dist-packages", ext.target_dir.."/omni/isaac/rclpy" },
    { "%{root}/_build/target-deps/tinyxml2/lib/lib**", ext.target_dir.."/bin" },
    { "%{root}/_build/target-deps/openssl/lib/*.so**", ext.target_dir.."/bin" },
}
