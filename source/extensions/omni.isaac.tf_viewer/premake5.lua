local ext = get_current_extension_info()
project_ext (ext)

-- backend (ROS2 Humble)
project_with_location("omni.isaac.transform_listener.humble")
    targetdir (ext.bin_dir)
    kind "SharedLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "backend/humble")
    add_files("iface", "include")
    add_files("source", "%{root}/_build/target-deps/nv_ros2_humble/src/geometry2/tf2/src")
    includedirs {
        "%{root}/_build/target-deps/nv_ros2_humble/include",
        "%{root}/_build/target-deps/nv_ros2_humble/include/console_bridge_vendor",
        "%{root}/source/extensions/omni.isaac.tf_viewer",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_ros2_humble/lib",
    }
    links{
        "rcutils"
    }

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        buildoptions("-fvisibility=default")
        linkoptions { "-Wl,--export-dynamic" }
    filter { "system:windows" }
        includedirs {
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_runtime_c",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_runtime_cpp",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rosidl_typesupport_interface",
            "%{root}/_build/target-deps/nv_ros2_humble/include/rcutils",
            "%{root}/_build/target-deps/nv_ros2_humble/include/builtin_interfaces",
            "%{root}/_build/target-deps/nv_ros2_humble/include/std_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/geometry_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/tf2_msgs",
            "%{root}/_build/target-deps/nv_ros2_humble/include/tf2",
        }
        links{
            "console_bridge"
        }
        -- avoid inconsistent dll linkage
        defines { "TF2__VISIBILITY_CONTROL_H_" }
        buildoptions { "-DTF2_PUBLIC=" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- backend (ROS2 Foxy) -- Linux only
if os.target() == "linux" then
    project_with_location("omni.isaac.transform_listener.foxy")
        targetdir (ext.bin_dir)
        kind "SharedLib"
        language "C++"

        pic "On"
        staticruntime "Off"
        add_files("impl", "backend/foxy")
        add_files("iface", "include")
        add_files("source", "%{root}/_build/target-deps/nv_ros2/src/geometry2/tf2/src")
        includedirs {
            "%{root}/_build/target-deps/nv_ros2/include",
            "%{root}/source/extensions/omni.isaac.tf_viewer",
        }
        libdirs {
            "%{root}/_build/target-deps/nv_ros2/lib",
        }
        links{
            "rcutils"
        }

        filter { "system:linux" }
            disablewarnings {"error=pragmas"}
            buildoptions{"-fvisibility=default", "-Wno-sign-compare", "-Wno-reorder"}
            linkoptions { "-Wl,--export-dynamic" }
        filter {}

        filter { "configurations:debug" }
            defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}
end

-- build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "omni.isaac.transform_listener.plugin")
    rtti "On"

    add_files("include", "include")
    add_files("source", "plugins")
    link_boost_for_windows({"boost_python310"})
    includedirs {
        "include",
        "plugins",
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/python/include/python3.10",
        "%{root}/_build/target-deps/python/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nlohmann-json/include",
        "%{root}/source/extensions/omni.isaac.ros2_bridge",
        "%{root}/source/extensions/omni.isaac.ros2_bridge/include",
        "%{root}/source/extensions/omni.isaac.core_nodes/include",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
    }
    libdirs {
       "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    }
    filter { "system:linux" }
        disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable"}
        links {
            "boost_system",
            "boost_python310",
        }
    filter { "system:windows" }
        links {
            "usd", "sdf",
        }
    filter {}

-- build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.transform_listener.python",
    module = "_transform_listener",
    src = "bindings",
    target_subdir = "omni/isaac/tf_viewer"
}
    includedirs {
        "include",
    }

-- link/copy folders and files that should be packaged with the extension
repo_build.prebuild_link {
    { "python/impl", ext.target_dir.."/omni/isaac/tf_viewer/impl" },
    { "python/tests", ext.target_dir.."/omni/isaac/tf_viewer/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/tf_viewer" },
}
