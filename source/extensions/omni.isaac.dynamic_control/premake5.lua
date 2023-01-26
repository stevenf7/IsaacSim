local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.dynamic_control.plugin")

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/dynamic_control/**")

    include_physx()   

    includedirs {
        "%{root}/include/pch",
        target_deps.."/physx/include",
        target_deps.."/pxshared/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include/boost",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/include",
        target_deps.."/omni_physics/include",
        target_deps.."/carbonite/include",
        target_deps.."/rtx_plugins/include",
        target_deps.."/omni_client_library/include",



     }
     libdirs {
        target_deps.."/nv_usd/%{cfg.buildcfg}/lib",
        target_deps.."/usd_ext/%{cfg.buildcfg}/lib",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin"
    }

    links {"gf", "sdf", "usd", "usdGeom","usdUtils", "tf", "arch",  "omni.usd"}

    filter { "system:linux" }
        includedirs {
            target_deps.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps.."/python/include/python3.7m"
        }
    filter { "system:windows" }
        libdirs {
            target_deps.."/tbb/lib/intel64/vc14"
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
