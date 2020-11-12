local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.manip.plugin")
    disablewarnings {"error=unused-variable"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/manip/**")
    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib",
    }

     links {
        "sdf", "usdUtils",
    }

    filter { "system:linux" }
        buildoptions { "-pthread" }
        includedirs { "%{root}/_build/target-deps/python/include/python3.6m" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.manip.python",
    module = "_manip",
    src = "bindings",
    target_subdir = "omni/isaac/manip"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/manip/scripts" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/manip" },
}
