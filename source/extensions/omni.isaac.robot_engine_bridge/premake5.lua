local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.robot_engine_bridge.plugin")

    disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable", "error=unused-function"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/robot_engine_bridge/**")

    include_physx()

    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.6m",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/isaac_engine/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/cuda/include",
        "%{root}/_build/target-deps/client_library/include",
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
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "isaac_c_api_capnp", "capnp-json", "capnp", "omni.usd", "lidarSchema", "robotEngineBridgeSchema", "physxSchema", "PhysXVehicle_static_64"
    }

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
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/robot_engine_bridge" },
}
