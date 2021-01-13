local ext = get_current_extension_info()
project_ext (ext)


project_with_location("omni.isaac.occupancy_map.generator")
    targetdir (ext.bin_dir)
    kind "SharedLib"
    language "C++"
    
    disablewarnings {"error=pragmas"}

    include_physx()
    add_files("impl", "library")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
    --     "%{root}/_build/target-deps/client_library/include",
    --     "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/octomap/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    --     "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    --     "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",             
        "%{root}/_build/target-deps/octomap/lib",
    --     "%{root}/_build/target-deps/omni_physics/lib",
    }
    links{"octomap", "octomath", "usdPhysics"}
    
    -- links {"ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
    -- "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "octomap", "octomath", "omni.usd", "usdPhysics"}


    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.6m"
        }
        buildoptions("-fvisibility=default")
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.occupancy_map.plugin")
    dependson {"omni.isaac.occupancy_map.generator"}
    disablewarnings {"error=pragmas"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    include_physx()

    includedirs {
        "%{root}/source/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/client_library/include",
    }
    libdirs {
        "%{kit_sdk_bin_dir}/plugins",             
    }
    links {"usdUtils", "omni.isaac.occupancy_map.generator"}
    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.6m"
        }
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
    project_name = "omni.isaac.occupancy_map.python",
    module = "_occupancy_map",
    src = "bindings",
    target_subdir = "omni/isaac/occupancy_map"})

    dependson {"omni.isaac.occupancy_map.generator"}

    include_physx()

    includedirs {
        "%{root}/source/pch",
        "%{root}/_build/target-deps/omni_physics/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
    }
    links {"tf", "usdUtils", "usd", "omni.isaac.occupancy_map.generator"}

    filter { "system:linux" }
        links {"tbb", "boost_python36", "pthread"}
        buildoptions { "-pthread"}
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/python/include/python3.6m"
        }
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}


repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/occupancy_map/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/occupancy_map/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/occupancy_map" },
    { "%{root}/_build/target-deps/octomap/lib/**", ext.target_dir.."/bin" },
}
