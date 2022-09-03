local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.robot_engine_bridge_gxf.plugin")
    add_files("impl", "plugins")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("iface", "%{root}/include/omni/isaac/robot_engine_bridge_gxf/**")

    include_physx()

    add_cuda_dependencies()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/isaac_gxf",
        "%{root}/_build/target-deps/isaac_gxf/include",
        "%{root}/_build/target-deps/isaac_gxf/include/external/com_nvidia_gxf",
        "%{root}/_build/target-deps/isaac_gxf/include/external/com_nvidia_isaac_engine",
        "%{root}/_build/target-deps/isaac_gxf/include/external/org_tuxfamily_eigen",
        "%{root}/_build/target-deps/isaac_gxf/include/external/capnproto/c++/src/",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/isaac_gxf/lib",
            "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
            "%{kit_sdk_bin_dir}/plugins",

    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", 
        "rangeSensorSchema", "robotEngineBridgeSchema", "physxSchema"
    }
    links{
        "gxf_core", "gxf_isaac_messages", "gxf_isaac_message_generators"
    }
    runpathdirs { ext.target_dir.."/gxf/lib", ext.target_dir.."/lib" }

    -- linkoptions{"-Wl,--whole-archive %{root}/_build/target-deps/isaac_engine/lib/libkj.a -Wl,--no-whole-archive"}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.robot_engine_bridge_gxf.python",
    module = "_robot_engine_bridge_gxf",
    src = "bindings",
    target_subdir = "omni/isaac/robot_engine_bridge_gxf"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/robot_engine_bridge_gxf/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/robot_engine_bridge_gxf/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "%{root}/_build/target-deps/isaac_gxf/lib", ext.target_dir.."/lib/" },
    -- { "%{root}/_build/target-deps/isaac_gxf/gxf", ext.target_dir.."/omni/isaac/pygxf" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/robot_engine_bridge_gxf" },
}