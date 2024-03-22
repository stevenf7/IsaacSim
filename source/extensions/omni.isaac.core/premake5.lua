local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}



repo_build.prebuild_link {
    {"python/tests", ext.target_dir.."/omni/isaac/core/tests"},
    {"python/scripts/world", ext.target_dir.."/omni/isaac/core/world"},
    {"python/scripts/simulation_context", ext.target_dir.."/omni/isaac/core/simulation_context"},
    {"python/scripts/utils", ext.target_dir.."/omni/isaac/core/utils"},
    {"python/scripts/prims", ext.target_dir.."/omni/isaac/core/prims"},
    {"python/scripts/scenes", ext.target_dir.."/omni/isaac/core/scenes"},
    {"python/scripts/objects", ext.target_dir.."/omni/isaac/core/objects"},
    {"python/scripts/physics_context", ext.target_dir.."/omni/isaac/core/physics_context"},
    {"python/scripts/articulations", ext.target_dir.."/omni/isaac/core/articulations"},
    {"python/scripts/controllers", ext.target_dir.."/omni/isaac/core/controllers"},
    {"python/scripts/loggers", ext.target_dir.."/omni/isaac/core/loggers"},
    {"python/scripts/materials", ext.target_dir.."/omni/isaac/core/materials"},
    {"python/scripts/robots", ext.target_dir.."/omni/isaac/core/robots"},
    {"python/scripts/tasks", ext.target_dir.."/omni/isaac/core/tasks"}}
    

repo_build.prebuild_copy {
        { "python/scripts/*.py", ext.target_dir.."/omni/isaac/core" }}

-- Build the C++ plugin that will be loaded by the extension.
project_with_location("omni.isaac.core.plugins")
    targetdir (ext.bin_dir)
    kind "StaticLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "plugins")
    add_files("iface", "include")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/source/extensions/omni.isaac.core/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }
    links{"sdf", "omni.usd", "usd", "usdGeom", "usdUtils"}

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.10",
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost"
        }
        buildoptions("-fvisibility=default")
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}


-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.core.python",
    module = "_core",
    src = "bindings",
    target_subdir = "omni/isaac/core"})
    
    -- Add the standard dependencies all OGN projects have, and link directories with Python nodes
    dependson {"omni.isaac.core.plugins"}
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/source/extensions/omni.isaac.core/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"sdf", "usd", "tf","usdUtils", "omni.isaac.core.plugins"}

    filter { "system:linux", "platforms:x86_64" }        
        links {"tbb", "boost_python310" }
    filter {}

    filter { "system:windows", "platforms:x86_64" }
        link_boost_for_windows({"boost_python310"})

    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}
