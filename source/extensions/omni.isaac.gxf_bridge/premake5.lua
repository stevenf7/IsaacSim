local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/gxf_bridge")

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.gxf_bridge.plugin")
    cppdialect "C++17"

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/gxf_bridge/**")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    -- NOTE: CUDA dependencies must be brought in via isaac_gxf package, due to patch made to CUDA cmath in Isaac to 
    --       ensure C++17 compatibility

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.10",
        "%{root}/_build/target-deps/isaac_gxf",
        "%{root}/_build/target-deps/isaac_gxf/include",
        "%{root}/_build/target-deps/isaac_gxf/include/external",
        "%{root}/_build/target-deps/isaac_gxf/include/external/com_nvidia_gxf",
        "%{root}/_build/target-deps/isaac_gxf/include/external/com_nvidia_isaac_engine",
        "%{root}/_build/target-deps/isaac_gxf/include/external/cuda_x86_64_11080/usr/local/cuda-11.8/targets/x86_64-linux/include",
        "%{root}/_build/target-deps/isaac_gxf/include/external/org_tuxfamily_eigen",
        "%{root}/_build/target-deps/isaac_gxf/include/external/yaml-cpp/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/include",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/source/extensions/omni.isaac.gxf_bridge/",
     }
     libdirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
            "%{root}/_build/target-deps/isaac_gxf/lib",
            "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
            "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/lib",
            "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
            "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"

    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd", 
        "rangeSensorSchema", "physxSchema"
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

project_ext_ogn( ext, ogn )

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.gxf_bridge.python",
    module = "_gxf_bridge",
    src = "bindings",
    target_subdir = "omni/isaac/gxf_bridge"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/gxf_bridge/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/gxf_bridge/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "%{root}/_build/target-deps/isaac_gxf/lib", ext.target_dir.."/lib/" },
    { "%{root}/_build/target-deps/isaac_gxf/gxf", ext.target_dir.."/omni/isaac/pygxf" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/gxf_bridge" },
}