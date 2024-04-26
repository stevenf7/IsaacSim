local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.dynamic_control.plugin")

    add_files("impl", "plugins")

    include_physx()   

    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include/boost",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/include",
        target_deps.."/omni_physics/include",
        target_deps.."/rtx_plugins/include",
        target_deps.."/omni_client_library/include",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
     }
     libdirs {
        target_deps.."/nv_usd/%{cfg.buildcfg}/lib",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }

    links {"gf", "sdf", "usd", "usdGeom","usdUtils", "tf", "arch",  "omni.usd"}

    filter { "system:linux" }
        includedirs {
            target_deps.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps.."/python/include/python3.10"
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

    includedirs {
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
    }

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/dynamic_control/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/dynamic_control/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/dynamic_control" },
}
