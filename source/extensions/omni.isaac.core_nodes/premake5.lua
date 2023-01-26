local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/core_nodes")
project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.core_nodes.plugin")
    add_files("impl", "plugins")
    add_files("impl", "%{root}/include/omni/isaac/utils/", "CameraKernels.cu")
    add_files("iface", "%{root}/include/omni/isaac/core_nodes/**")
    add_files("ogn", ogn.nodes_path)

    add_cuda_dependencies()

    filter { "system:linux", "platforms:x86_64" }
        disablewarnings {"error=narrowing", "error=unused-but-set-variable", "error=unused-variable"}
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    add_ogn_dependencies(ogn, {"python/nodes"})

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/carbonite/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/include", 
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include"
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin"
    }

     links {
        "gf", "sdf", "tf", "usd", "usdGeom", "usdUtils", "omni.usd",
    }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

project_ext_ogn( ext, ogn )

project_ext_bindings {
    ext = ext,
    project_name = ogn.python_project,
    module = ogn.bindings_module,
    src = ogn.bindings_path,
    target_subdir = ogn.bindings_target_path
}
    add_files("bindings", "bindings")
    add_files("python", "python/*.py")
    add_files("python/tests", "python/tests/*.py")

    -- Add the standard dependencies all OGN projects have
repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}

repo_build.prebuild_link {
    { "python/scripts", ogn.python_target_path.."/scripts" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "python/impl", ogn.python_target_path.."/impl" },
    { "python/tests", ogn.python_tests_target_path },
}
