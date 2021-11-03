local ext = get_current_extension_info()
project_ext (ext, { 
    test_args = {
        extra_test_args = {"--/exts/omni.isaac.robot_engine_bridge/IsaacSDKLogLevel=-2"}
    }
})

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.robot_engine_bridge.plugin")
    dependson {"omni.isaac.occupancy_map.generator"}
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/robot_engine_bridge/**")

    include_physx()

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
        "%{root}/_build/target-deps/cuda/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/nv_usd/release/lib",
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
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/robot_engine_bridge" },
    -- { "%{root}/_build/target-deps/isaac_engine/lib/**", ext.target_dir.."/bin" },
    -- { "%{root}/_build/target-deps/isaac_engine/lib/libnpp*.so*", ext.target_dir.."/packages/viewers" },
    { "%{root}/_build/target-deps/isaac_engine/*.whl", ext.target_dir.."/pip-packages/" },
}