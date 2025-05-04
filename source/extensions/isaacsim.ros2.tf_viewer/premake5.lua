local ext = get_current_extension_info()
project_ext(ext)

local ros_distributions = { "humble", "jazzy" }

for _, ros_distro in ipairs(ros_distributions) do
    project_with_location("isaacsim.ros2.tf_viewer." .. ros_distro)
    targetdir(ext.bin_dir)
    kind("SharedLib")
    language("C++")

    pic("On")
    staticruntime("Off")
    defines { "ROS2_BACKEND_" .. string.upper(ros_distro) }
    add_files("impl", "library/backend")
    add_files("iface", "include")
    add_files("source", "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/src/geometry2/tf2/src")
    includedirs {
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/rosidl_runtime_cpp",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/console_bridge_vendor",
        "%{root}/source/extensions/isaacsim.ros2.tf_viewer/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/lib",
    }
    links {
        "rcutils",
    }

    if ros_distro == "humble" then
        links {
            "console_bridge",
        }
    end

    filter { "system:linux" }
    disablewarnings { "error=pragmas" }
    buildoptions("-fvisibility=default")
    linkoptions { "-Wl,--export-dynamic" }
    filter { "system:windows" }
    includedirs {
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/rosidl_runtime_c",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/rosidl_runtime_cpp",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/rosidl_typesupport_interface",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/rcutils",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/builtin_interfaces",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/std_msgs",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/geometry_msgs",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/tf2_msgs",
        "%{root}/_build/target-deps/nv_ros2_" .. ros_distro .. "/include/tf2",
        "%{root}/source/extensions/isaacsim.ros2.bridge/include",
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
end

-- build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "isaacsim.ros2.tf_viewer.plugin")
rtti("On")

add_files("include", "include")
add_files("source", "plugins")
-- link_boost_for_windows({"boost_python310"})
includedirs {
    "include",
    "plugins",
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include/boost",
    "%{root}/_build/target-deps/python/include/python3.11",
    "%{root}/_build/target-deps/python/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
    "%{root}/_build/target-deps/nlohmann_json/include",
    "%{root}/source/extensions/isaacsim.ros2.bridge",
    "%{root}/source/extensions/isaacsim.ros2.bridge/include",
    "%{root}/source/extensions/isaacsim.core.nodes/include",
    "%{root}/source/extensions/isaacsim.ros2.tf_viewer/include",
}
libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
}

extra_usd_libs = {}

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "system:linux" }
disablewarnings { "error=narrowing", "error=unused-but-set-variable", "error=unused-variable" }
links {
    "boost_system",
}
filter {}

-- build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.ros2.tf_viewer.python",
    module = "_transform_listener",
    src = "bindings",
    target_subdir = "isaacsim/ros2/tf_viewer",
}
includedirs {
    "include",
}

-- link/copy folders and files that should be packaged with the extension
repo_build.prebuild_link {
    { "python/impl", ext.target_dir .. "/isaacsim/ros2/tf_viewer/impl" },
    { "python/tests", ext.target_dir .. "/isaacsim/ros2/tf_viewer/tests" },
    { "data", ext.target_dir .. "/data" },
    { "docs", ext.target_dir .. "/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/isaacsim/ros2/tf_viewer" },
}
