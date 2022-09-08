local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.dynamic_control.plugin")

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/dynamic_control/**")

    include_physx()   

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/carbonite/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_client_library/include",



     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib"
    }

    links {"gf", "sdf", "usd", "usdGeom","usdUtils", "tf", "arch"}

    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.dynamic_control.python",
    module = "_dynamic_control",
    src = "bindings",
    target_subdir = "omni/isaac/dynamic_control"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/dynamic_control/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/dynamic_control/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/dynamic_control" },
}
