local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.gamepad.plugin")

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/gamepad/**")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
     }
     libdirs {
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    }

     links {
        "sdf", "usdUtils",
    }

    filter { "system:linux" }
        buildoptions { "-pthread" }
        includedirs { "%{root}/_build/target-deps/python/include/python3.7m" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.gamepad.python",
    module = "_gamepad",
    src = "bindings",
    target_subdir = "omni/isaac/gamepad"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/gamepad/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/gamepad/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/gamepad" },
}
