local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/sensors/rtx")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext(ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, ogn.plugin_project)
cppdialect("C++17")

add_files("impl", "plugins")
add_files("nodes", ogn.nodes_path)

add_ogn_dependencies(ogn, { "python/nodes" })

include_physx()
add_cuda_dependencies()

includedirs {
    "%{kit_sdk_bin_dir}/dev/fabric/include/",
    "%{kit_sdk_bin_dir}/dev/internal/include/",
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/source/extensions/isaacsim.core.nodes/include",
    "%{root}/source/extensions/isaacsim.sensors.rtx/include",
    targetDepsDir .. "/generic_model_output/%{platform}/%{config}/include",
    targetDepsDir .. "/omni_client_library/include",
    targetDepsDir .. "/python/include",
    targetDepsDir .. "/rtx_plugins/include",
}
libdirs {
    extsbuild_dir .. "/omni.usd.core/bin",
    targetDepsDir .. "/python/lib",
}

links {
    "omni.usd",
}

extra_usd_libs = {}

-- Begin OpenUSD
add_usd(extra_usd_libs)
-- End OpenUSD

filter { "system:linux" }
includedirs {
    targetDepsDir .. "/usd/%{cfg.buildcfg}/include/boost",
    targetDepsDir .. "/python/include/python3.11",
}
filter { "system:windows" }
libdirs {
    targetDepsDir .. "/tbb/lib/intel64/vc14",
}
filter {}

filter { "configurations:debug" }
defines { "_DEBUG" }
filter { "configurations:release" }
defines { "NDEBUG" }
filter {}

project_ext_ogn(ext, ogn)

project_ext_bindings {
    ext = ext,
    project_name = ogn.python_project,
    module = ogn.bindings_module,
    src = ogn.bindings_path,
    target_subdir = ogn.bindings_target_path,
}
add_files("bindings", "bindings/*.*")
add_files("python", "python/*.py")
add_files("python/scripts", "python/scripts/**.py")
add_files("python/tests", "python/tests/**.py")

add_ogn_dependencies(ogn)

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "python/scripts", ogn.python_target_path .. "/scripts" },
    { "python/tests", ogn.python_target_path .. "/tests" },
}

repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}
