local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/robot_engine_bridge")
project_ext (ext, { 
    test_args = {
        extra_test_args = {"--/exts/omni.isaac.robot_engine_bridge/IsaacSDKLogLevel=-2"}
    }
})

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.robot_engine_bridge.plugin")
    dependson {"omni.isaac.occupancy_map.generator"}
    add_files("impl", "plugins")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("iface", "%{root}/include/omni/isaac/robot_engine_bridge/**")
    add_files("ogn", ogn.nodes_path)


    include_physx()

    add_cuda_dependencies()

    add_ogn_dependencies(ogn, {"nodes"})

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/isaac_engine/include",
        "%{root}/_build/target-deps/isaac_engine",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/isaac_engine/lib",
            "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
            "%{kit_sdk_bin_dir}/plugins",

    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "isaac_c_api_capnp", "capnp-json", "capnp", "omni.usd", 
        "rangeSensorSchema", "robotEngineBridgeSchema", "physxSchema", "physicsSchemaTools", "omni.isaac.occupancy_map.generator"
    }
    links{
        "isaac_c_api"
    }
    runpathdirs { ext.target_dir.."/lib" }

    linkoptions{"-Wl,--whole-archive %{root}/_build/target-deps/isaac_engine/lib/libkj.a -Wl,--no-whole-archive"}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

project_ext_ogn( ext, ogn )
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.robot_engine_bridge.python",
    module = "_robot_engine_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/robot_engine_bridge"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/robot_engine_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/robot_engine_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "%{root}/_build/target-deps/isaac_engine/data", ext.target_dir.."/resources/isaac_engine/" },
    { "%{root}/_build/target-deps/isaac_engine/packages", ext.target_dir.."/packages/" },
    { "%{root}/_build/target-deps/isaac_engine/lib", ext.target_dir.."/lib/" },
    { "%{root}/_build/target-deps/isaac_engine/packages/pyalice", ext.target_dir.."/omni/isaac/pyalice" },
    { "$root/_build/target-deps/isaac_reb_prebundle", ext.target_dir.."/pip_prebundle" },

}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/robot_engine_bridge" },
    -- { "%{root}/_build/target-deps/isaac_engine/lib/**", ext.target_dir.."/bin" },
    -- { "%{root}/_build/target-deps/isaac_engine/lib/libnpp*.so*", ext.target_dir.."/packages/viewers" },
}