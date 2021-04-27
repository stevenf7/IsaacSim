local ext = get_current_extension_info()
project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.ros_bridge.plugin")

    disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/ros_bridge/**")

    filter { "files:**.cu", "system:linux", "configurations:debug"}
        make_nvcc_command("-fPIC -g", "-g")
    filter { "files:**.cu", "system:linux", "configurations:release" }
        make_nvcc_command("-fPIC", "")
    filter {}

    filter { "system:linux", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/cuda/lib64" }
        links { "cudart_static" }
    filter {}

    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/carbonite/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/include", 
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/nv_ros/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
        "%{root}/source/extensions/omni.isaac.ros_bridge/msgs/melodic",
        "%{root}/_build/target-deps/cuda/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_ros/lib",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/cuda/lib64"
    }

     links {
        "gf", "sdf", "usdGeom", "usdUtils", "actionlib", "tf2", "tf2_ros", "roscpp" , "rosBridgeSchema", "cudart_static", "rangeSensorSchema"
    }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.ros_bridge.python",
    module = "_ros_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/ros_bridge"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ros_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros_bridge" },
    { "%{root}/_build/target-deps/nv_ros/lib/lib**", ext.target_dir.."/bin" },
}

repo_build.prebuild_copy {
    { "rospy/*.py", ext.target_dir.."/omni/isaac/rospy" },
    { "%{root}/_build/target-deps/nv_ros/", ext.target_dir.."/noetic" },
}