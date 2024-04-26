local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/surface_gripper")

project_ext_ogn (ext, ogn)
project_ext( ext, { generate_ext_project=true })

    add_files("python", "*.py")
    add_files("python/nodes", "python/nodes/**.py")
    add_files("python/impl", "python/impl/**.py")

    add_ogn_dependencies(ogn, {"python/nodes"})


    repo_build.prebuild_link {
        { "python/impl", ogn.python_target_path.."/impl" },
        { "python/tests", ogn.python_target_path.."/tests" },
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "include", ext.target_dir.."/include" },
    }

    repo_build.prebuild_copy {
        { "python/__init__.py", ogn.python_target_path },
    }

-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.surface_gripper.python",
    module = "_surface_gripper",
    src = "bindings",
    target_subdir = "omni/isaac/surface_gripper"})
    
    include_physx()
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/source/extensions/omni.isaac.surface_gripper/include",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
        "%{root}/_build/target-deps/omni_physics/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils"}

    filter { "system:windows", "platforms:x86_64" }
        link_boost_for_windows({"boost_python310"})
    filter {}

    filter { "system:linux", "platforms:x86_64" }
        links {"tbb", "boost_python310" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}
