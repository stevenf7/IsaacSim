local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.decals.plugin")

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/decals/**")
    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/client_library/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",             
    }

     links {
        "gf", "sdf", "tf", "usd", "usdGeom", "vt", "usdUtils", "omni.usd"
    }

    filter { "system:linux" }
        includedirs { "%{root}/_build/target-deps/python/include/python3.6m" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.decals.python",
    module = "_decals",
    src = "bindings",
    target_subdir = "omni/isaac/decals"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/decals/scripts" },
}