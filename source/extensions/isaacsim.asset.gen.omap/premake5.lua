local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/asset/gen/omap")
project_ext(ext)

project_with_location("isaacsim.asset.gen.omap.generator")
targetdir(ext.bin_dir)
kind("SharedLib")
language("C++")
defines { "OMGENERATOREXPORT" }

pic("On")
staticruntime("Off")
include_physx()
add_files("impl", "library")
includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/omni_physics/%{config}/include",
    "%{root}/_build/target-deps/octomap/include",
    "%{root}/source/extensions/isaacsim.asset.gen.omap/include",
}
libdirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
}
links { "octomap", "octomath", "usdPhysics", "sdf", "tf", "usd" }

filter { "system:linux" }
disablewarnings { "error=pragmas" }
includedirs {
    "%{root}/_build/target-deps/python/include/python3.10",
}
buildoptions("-fvisibility=default")
libdirs {
    "%{root}/_build/target-deps/octomap/lib64",
}
filter { "system:windows" }
-- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
disablewarnings { "4099" }
disablewarnings { "4251" }
--  needed to static link against physx
-- linkoptions { "/ltcg" }
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
    "%{root}/_build/target-deps/octomap/lib",
}
filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "isaacsim.asset.gen.omap.plugin")
dependson { "isaacsim.asset.gen.omap.generator" }
dependson { "isaacsim.util.debug_draw.primitive_drawing" }

add_files("impl", "plugins")
include_physx()

includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/rtx_plugins/include",
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/omni_physics/%{config}/include",
    "%{root}/_build/target-deps/omni_client_library/include",
    "%{root}/source/extensions/isaacsim.asset.gen.omap/include",
    "%{root}/source/extensions/isaacsim.util.debug_draw/include",
}
libdirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    extsbuild_dir .. "/omni.usd.core/bin",
}
links {
    "usdUtils",
    "omni.usd",
    "isaacsim.util.debug_draw.primitive_drawing",
    "usdPhysics",
    "isaacsim.asset.gen.omap.generator",
    "sdf",
    "tf",
    "usd",
}
filter { "system:linux" }
disablewarnings { "error=pragmas" }
includedirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
    "%{root}/_build/target-deps/python/include/python3.10",
}
libdirs {
    "%{root}/_build/target-deps/octomap/lib64",
}
links { "octomap", "octomath" }
filter { "system:windows" }
-- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
disablewarnings { "4099" }
disablewarnings { "4251" }
libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
    "%{root}/_build/target-deps/octomap/lib",
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
    project_name = "isaacsim.asset.gen.omap.python",
    module = "_omap",
    src = ogn.bindings_path,
    target_subdir = ogn.bindings_target_path,
}

add_files("bindings", "bindings/*.*")

dependson { "isaacsim.asset.gen.omap.generator" }

include_physx()

includedirs {
    "%{root}/source/extensions/isaacsim.core.includes/include",
    "%{root}/_build/target-deps/omni_physics/%{config}/include",
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    "%{root}/source/extensions/isaacsim.asset.gen.omap/include",
}

libdirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
}
links { "sdf", "tf", "usd", "usdUtils", "usdPhysics", "isaacsim.asset.gen.omap.generator" }

filter { "system:linux" }
links { "tbb", "boost_python310", "pthread" }
buildoptions { "-pthread" }
includedirs {
    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    "%{root}/_build/target-deps/python/include/python3.10",
}
-- libdirs {
--     "%{root}/_build/target-deps/octomap/lib64",
-- }
filter { "system:windows" }
-- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
disablewarnings { "4099" }
disablewarnings { "4251" }
link_boost_for_windows { "boost_python310" }

libdirs {
    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
}
filter {}

repo_build.prebuild_link {
    { "python/impl", ogn.python_target_path .. "/impl" },
    { "python/tests", ogn.python_target_path .. "/tests" },
    { "python/utils", ogn.python_target_path .. "/utils" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "include", ext.target_dir .. "/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ogn.python_target_path },
}

if os.target() == "linux" then
    -- repo_build.prebuild_copy {
    --     { "%{root}/_build/target-deps/octomap/lib64/*.so.*", ext.target_dir.."/bin" },
    -- }
else
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/octomap/bin/*.dll", ext.target_dir .. "/bin" },
    }
end
