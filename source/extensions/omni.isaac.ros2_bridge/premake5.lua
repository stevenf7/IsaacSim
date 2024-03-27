local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/ros2_bridge")
project_ext (ext)


project_with_location("omni.isaac.ros2_bridge.foxy")
    targetdir (ext.bin_dir)
    kind "SharedLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "backend/foxy")
    add_files("iface", "include")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/nv_ros2/include",
        "%{root}/_build/target-deps/nlohmann-json/include",
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
        "%{root}/_build/target-deps/nv_ros2/lib",
    }
    links{
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace",
        "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", "usdPhysics",
        "sdf", "usdGeom", "carb",
        "rosidl_runtime_c", "rcutils", "rcl", "rmw",
        "tf2_msgs__rosidl_typesupport_c", "tf2_msgs__rosidl_generator_c",
        "geometry_msgs__rosidl_typesupport_c", "geometry_msgs__rosidl_generator_c",
        "nav_msgs__rosidl_typesupport_c", "nav_msgs__rosidl_generator_c",
        "std_msgs__rosidl_typesupport_c", "std_msgs__rosidl_generator_c",
        "rosgraph_msgs__rosidl_typesupport_c", "rosgraph_msgs__rosidl_generator_c",
        "sensor_msgs__rosidl_typesupport_c", "sensor_msgs__rosidl_generator_c",
        -- "vision_msgs__rosidl_typesupport_c", "vision_msgs__rosidl_generator_c"
        -- "ackermann_msgs__rosidl_typesupport_c", "ackermann_msgs__rosidl_generator_c"
    }

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.10"
        }
        buildoptions("-fvisibility=default")
        linkoptions { "-Wl,--export-dynamic" }
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- Humble stuff
project_with_location("omni.isaac.ros2_bridge.humble")
    targetdir (ext.bin_dir)
    kind "SharedLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "backend/humble")
    add_files("iface", "include")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/nv_ros2_humble/include",
        "%{root}/_build/target-deps/nlohmann-json/include",
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
        "%{root}/_build/target-deps/nv_ros2_humble/lib",
    }
    links{
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace",
        "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", "usdPhysics",
        "sdf", "usdGeom", "carb",
        "rosidl_runtime_c", "rcutils", "rcl", "rmw",
        "tf2_msgs__rosidl_typesupport_c", "tf2_msgs__rosidl_generator_c",
        "geometry_msgs__rosidl_typesupport_c", "geometry_msgs__rosidl_generator_c",
        "nav_msgs__rosidl_typesupport_c", "nav_msgs__rosidl_generator_c",
        "std_msgs__rosidl_typesupport_c", "std_msgs__rosidl_generator_c",
        "rosgraph_msgs__rosidl_typesupport_c", "rosgraph_msgs__rosidl_generator_c",
        "sensor_msgs__rosidl_typesupport_c", "sensor_msgs__rosidl_generator_c",
        -- "vision_msgs__rosidl_typesupport_c", "vision_msgs__rosidl_generator_c"
        -- "ackermann_msgs__rosidl_typesupport_c", "ackermann_msgs__rosidl_generator_c"
    }

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.10"
        }
        buildoptions("-fvisibility=default")
        linkoptions { "-Wl,--export-dynamic" }
    filter { "system:windows" }
        includedirs {
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_runtime_c",
            "%{root}/_build/target-deps/nv_ros2_humble/include/builtin_interfaces",
            "%{root}/_build/target-deps/nv_ros2_humble/include/geometry_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/nav_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/sensor_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/tf2_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/vision_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/std_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosgraph_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_typesupport_interface",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_typesupport_introspection_c",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rcl",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rcutils",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rmw",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rcl_yaml_param_parser",
            "%{root}/_build/target-deps/nv_ros2_humble/include/ackermann_msgs",
        }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.ros2_bridge.plugin")


    add_files("impl", "plugins")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("iface", "include")
    add_files("ogn", ogn.nodes_path)
    link_boost_for_windows({"boost_python310"})
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
        "%{root}/_build/target-deps/python/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/include",
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
        "%{root}/_build/target-deps/nlohmann-json/include",
        "%{root}/source/extensions/omni.isaac.core_nodes/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/lib",
    }
    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace",
        "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", "usdPhysics",
        "physxSchema", "sdf", "usdGeom", "rangeSensorSchema", "isaacSensorSchema", "carb",
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
    includedirs {
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
    }

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros2_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ros2_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros2_bridge" },
    { "rclpy/*.py", ext.target_dir.."/foxy/rclpy" },
    { "rclpy/*.py", ext.target_dir.."/humble/rclpy" },
}

if os.target() == "linux" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/nv_ros2/lib/lib**", ext.target_dir.."/foxy/lib" },
        { "%{root}/_build/target-deps/nv_ros2_humble/lib/lib**", ext.target_dir.."/humble/lib" },
        { "%{root}/_build/target-deps/nv_ros2/lib/python3.10/site-packages", ext.target_dir.."/foxy/rclpy" },
        { "%{root}/_build/target-deps/nv_ros2_humble/lib/python3.10/site-packages", ext.target_dir.."/humble/rclpy" },
        { "%{root}/_build/target-deps/nv_ros2_humble/local/lib/python3.10/dist-packages", ext.target_dir.."/humble/rclpy" },

    }
end

if os.target() == "windows" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/nv_ros2/bin/**.dll", ext.target_dir.."/foxy/lib" },
        { "%{root}/_build/target-deps/nv_ros2_humble/bin/**.dll", ext.target_dir.."/humble/lib" },
        { "%{root}/_build/target-deps/nv_ros2/Lib/site-packages", ext.target_dir.."/foxy/rclpy" },
        { "%{root}/_build/target-deps/nv_ros2_humble/Lib/site-packages", ext.target_dir.."/humble/rclpy" },
        { "%{root}/_build/target-deps/tinyxml2/bin/**.dll", ext.target_dir.."/foxy/lib" },
        { "%{root}/_build/target-deps/tinyxml2/bin/**.dll", ext.target_dir.."/humble/lib" },
        { "%{root}/_build/target-deps/openssl/lib/release/rt_dynamic/**.dll", ext.target_dir.."/foxy/lib" },
        { "%{root}/_build/target-deps/openssl/lib/release/rt_dynamic/**.dll", ext.target_dir.."/humble/lib" },
    }
end
