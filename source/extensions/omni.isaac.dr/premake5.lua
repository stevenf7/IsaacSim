local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.dr.plugin")
    disablewarnings {"error=unused-variable"} 
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/dr/**")
    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
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
        "arch", "gf", "pcp", "tf", "sdf", "usd", "usdGeom", "usdShade", "vt", "usdUtils", "audioSchema", "omni.usd", "drSchema"
    }

    filter { "system:linux" }
        buildoptions { "-pthread" }
        includedirs { "%{root}/_build/target-deps/python/include/python3.7m" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.dr.python",
    module = "_dr",
    src = "bindings",
    target_subdir = "omni/isaac/dr"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/dr/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/dr/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/dr" },
}

repo_build.prebuild_copy {
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/DrSchema/**", ext.target_dir.."/omni/isaac/DrSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}drSchema${lib_ext}", ext.target_dir.."/bin"},
}