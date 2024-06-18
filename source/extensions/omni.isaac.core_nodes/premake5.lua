local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/core_nodes")
project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.core_nodes.plugin")
    add_files("impl", "plugins")
    add_files("impl", "cuda")
    add_files("iface","%{root}/source/extensions/omni.isaac.core_nodes/include/**")
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

    include_physx()

    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/python/include/python3.10",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/omni_physics/%{config}/include",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/source/extensions/omni.isaac.core_nodes/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/_build/target-deps/python/include",

     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_audio_schema/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }

     links {
        "gf", "sdf", "tf", "usd", "usdGeom", "usdUtils", "omni.usd", "vt"
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

    includedirs {
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/source/extensions/omni.isaac.core_nodes/include",
     }

    -- Add the standard dependencies all OGN projects have
repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}

repo_build.prebuild_link {
    { "python/scripts", ogn.python_target_path.."/scripts" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
    { "python/impl", ogn.python_target_path.."/impl" },
    { "python/tests", ogn.python_tests_target_path },
}
