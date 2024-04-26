local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/ros_bridge")

project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.ros_bridge.plugin")

    disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable"}

    add_files("impl", "plugins")
    add_files("impl", "cuda")
    add_files("ogn", ogn.nodes_path)

    add_cuda_dependencies()

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.10",
        "%{root}/_build/target-deps/nv_ros/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/source/extensions/omni.isaac.ros_bridge",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/include",
        "%{root}/_build/target-deps/nlohmann-json/include",
        "%{root}/source/extensions/omni.isaac.ros_bridge/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_ros/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/lib",
    }

     links {
        "gf", "sdf", "usdGeom", "usdUtils", "omni.usd", "actionlib", "tf2", "tf2_ros", "roscpp" , "rangeSensorSchema",
        "carb", "isaacSensorSchema", "usdPhysics"
    }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

project_ext_ogn( ext, ogn )
    
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.ros_bridge.python",
    module = "_ros_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/ros_bridge"
}

includedirs {
    "%{root}/source/extensions/omni.isaac.ros_bridge/include",
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/ros_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ros_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ros_bridge" },
    { "%{root}/_build/target-deps/nv_ros/lib/lib**", ext.target_dir.."/bin" },
}

repo_build.prebuild_copy {
    { "rospy/*.py", ext.target_dir.."/omni/isaac/rospy" },
    { "%{root}/_build/target-deps/nv_ros/", ext.target_dir.."/noetic" },
}