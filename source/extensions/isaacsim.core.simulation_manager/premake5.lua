-- Setup the basic extension variables
local ext = get_current_extension_info()
-- Set up the basic shared project information
project_ext(ext)

-- -------------------------------------
-- Build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "isaacsim.core.simulation_manager.plugin")
add_files("include", "include/isaacsim/core/simulation_manager")
add_files("source", "plugins/isaacsim.core.simulation_manager")
includedirs {
    "include",
    "plugins/isaacsim.core.simulation_manager",
    target_deps .. "/rtx_plugins/include",
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{target_deps}/nv_usd/%{cfg.buildcfg}/include",
    "%{target_deps}/nv_usd/%{cfg.buildcfg}/include/boost",
    "%{target_deps}/python/include/python3.10",
    target_deps .. "/usd_ext_physics/%{cfg.buildcfg}/include",
    target_deps .. "/omni_physics/%{config}/include",
}

libdirs {
    target_deps .. "/nv_usd/%{cfg.buildcfg}/lib",
    target_deps .. "/usd_ext_physics/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}

links {
    "vt",
    "gf",
    "sdf",
    "arch",
    "usd",
    "tf",
    "usdUtils",
    "usdShade",
    "usdGeom",
    "usdSkel",
    "omni.usd",
    "usdPhysics",
    "physxSchema",
}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

-- -------------------------------------
-- Build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.core.simulation_manager.python",
    module = "_simulation_manager",
    src = "bindings/isaacsim.core.simulation_manager",
    target_subdir = "isaacsim/core/simulation_manager",
}
dependson { "isaacsim.core.simulation_manager.plugin" }
libdirs {
    target_deps .. "/nv_usd/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}
links { "isaacsim.core.simulation_manager.plugin" }

includedirs {
    "include",
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
    "%{root}/_build/target-deps/omni_client_library/include",
    extsbuild_dir .. "/usdrt.scenegraph/include",
    "%{root}/source/extensions/isaacsim.core.simulation_manager/include",
    "%{root}/source/extensions/isaacsim.core.simulation_manager/plugins",
}

libdirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/nv_usd/release/lib",
}
links { "arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils", "usdPhysics" }

filter { "system:linux", "platforms:x86_64" }
links { "tbb", "boost_python310" }
filter {}

filter { "system:windows", "platforms:x86_64" }
link_boost_for_windows { "boost_python310" }
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
}
filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

-- -------------------------------------
-- Link/copy folders and files to be packaged with the extension
repo_build.prebuild_link {
    { "data", ext.target_dir .. "/data" },
    { "docs", ext.target_dir .. "/docs" },
    { "python/impl", ext.target_dir .. "/isaacsim/core/simulation_manager/impl" },
    { "python/tests", ext.target_dir .. "/isaacsim/core/simulation_manager/tests" },
    { "include", ext.target_dir .. "/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/isaacsim/core/simulation_manager" },
}
