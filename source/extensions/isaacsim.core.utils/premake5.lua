local ext = get_current_extension_info()
project_ext(ext)

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.core.utils.python",
    module = "_isaac_utils",
    src = "bindings",
    target_subdir = "isaacsim/core/utils",
}
staticruntime("Off")
add_files("impl", "plugins")
add_files("iface", "include")
defines { "ISAACSIM_CORE_UTILS_EXPORT" }

include_physx()
includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/source/extensions/isaacsim.core.simulation_manager/include",
    "%{root}/source/deprecated/omni.isaac.dynamic_control/include",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{kit_sdk_bin_dir}/dev/fabric/include/",
    "%{root}/_build/target-deps/omni_client_library/include",
    extsbuild_dir .. "/usdrt.scenegraph/include",
    "%{root}/source/extensions/isaacsim.core.utils/include",
    "%{root}/source/extensions/isaacsim.core.utils/plugins",
    "%{root}/_build/target-deps/omni_physics/%{config}/include",
}

libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/nv_usd/release/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}
links { "omni.usd" }

extra_usd_libs = { "usdUtils", "usdGeom", "usdPhysics", "pcp" }

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "system:linux", "platforms:x86_64" }
links { "tbb" }
filter {}

filter { "system:windows", "platforms:x86_64" }
-- link_boost_for_windows({"boost_python310"})
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
}
filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

repo_build.prebuild_link {
    { "python/impl/numpy", ext.target_dir .. "/isaacsim/core/utils/numpy" },
    { "python/impl/torch", ext.target_dir .. "/isaacsim/core/utils/torch" },
    { "python/impl/warp", ext.target_dir .. "/isaacsim/core/utils/warp" },
    { "python/tests", ext.target_dir .. "/isaacsim/core/utils/tests" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
}

repo_build.prebuild_copy {
    { "python/impl/*.py", ext.target_dir .. "/isaacsim/core/utils" },
}
