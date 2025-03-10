local ext = get_current_extension_info()
project_ext(ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
}

repo_build.prebuild_link {
    { "python/tests", ext.target_dir .. "/isaacsim/core/api/tests" },
    { "python/impl/world", ext.target_dir .. "/isaacsim/core/api/world" },
    { "python/impl/simulation_context", ext.target_dir .. "/isaacsim/core/api/simulation_context" },
    { "python/impl/scenes", ext.target_dir .. "/isaacsim/core/api/scenes" },
    { "python/impl/sensors", ext.target_dir .. "/isaacsim/core/api/sensors" },
    { "python/impl/objects", ext.target_dir .. "/isaacsim/core/api/objects" },
    { "python/impl/physics_context", ext.target_dir .. "/isaacsim/core/api/physics_context" },
    { "python/impl/articulations", ext.target_dir .. "/isaacsim/core/api/articulations" },
    { "python/impl/controllers", ext.target_dir .. "/isaacsim/core/api/controllers" },
    { "python/impl/loggers", ext.target_dir .. "/isaacsim/core/api/loggers" },
    { "python/impl/materials", ext.target_dir .. "/isaacsim/core/api/materials" },
    { "python/impl/robots", ext.target_dir .. "/isaacsim/core/api/robots" },
    { "python/impl/tasks", ext.target_dir .. "/isaacsim/core/api/tasks" },
}

repo_build.prebuild_copy {
    { "python/impl/*.py", ext.target_dir .. "/isaacsim/core/api" },
}

-- Build the C++ plugin that will be loaded by the extension.
project_ext_plugin(ext, "isaacsim.core.api.plugin")
targetdir(ext.bin_dir)
language("C++")
-- pic "On"
staticruntime("Off")
add_files("impl", "plugins")
add_files("iface", "include")

includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/generated/include/",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include",
    "%{kit_sdk_bin_dir}/dev/fabric/include/",
    "%{target_deps}/carb_sdk_plugins/include",
}
libdirs {
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}

extra_usd_libs = {}

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "system:linux" }
disablewarnings { "error=pragmas" }
includedirs {
    "%{root}/_build/target-deps/python/include/python3.11",
    "%{root}/_build/target-deps/usd/%{cfg.buildcfg}/include/boost",
}
buildoptions("-fvisibility=default")
filter { "system:windows" }
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
}
filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}
