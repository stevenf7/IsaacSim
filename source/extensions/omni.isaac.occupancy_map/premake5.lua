local ext = get_current_extension_info()
project_ext (ext)


project_with_location("omni.isaac.occupancy_map.generator")
    targetdir (ext.bin_dir)
    kind "SharedLib"
    language "C++"
    defines { "OMGENERATOREXPORT" }
    
    pic "On"
    staticruntime "Off"
    include_physx()
    add_files("impl", "library")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/octomap/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        
    }
    links{"octomap", "octomath", "usdPhysics", "sdf", "tf", "usd"}

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        buildoptions("-fvisibility=default")
        libdirs {
            "%{root}/_build/target-deps/octomap/lib64",
        }
    filter { "system:windows" }
        -- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
        disablewarnings {"4099"}
        disablewarnings {"4251"}
        --  needed to static link against physx
        -- linkoptions { "/ltcg" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
            "%{root}/_build/target-deps/octomap/lib",
        }
    filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.occupancy_map.plugin")
    dependson {"omni.isaac.occupancy_map.generator"}
    dependson {"omni.isaac.debug_draw.primitive_drawing"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    include_physx()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/omni_client_library/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    }
    links {"usdUtils", "omni.usd", "omni.isaac.debug_draw.primitive_drawing", "usdPhysics", "omni.isaac.occupancy_map.generator", "sdf", "tf", "usd"}
    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        libdirs {
            "%{root}/_build/target-deps/octomap/lib64",
        }
        links{"octomap", "octomath"}
    filter { "system:windows" }
        -- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
        disablewarnings {"4099"}
        disablewarnings {"4251"}
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
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.occupancy_map.python",
    module = "_occupancy_map",
    src = "bindings",
    target_subdir = "omni/isaac/occupancy_map"})

    dependson {"omni.isaac.occupancy_map.generator"}

    include_physx()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    }
    links {"sdf", "tf", "usd", "usdUtils", "usdPhysics", "omni.isaac.occupancy_map.generator"}

    filter { "system:linux" }
        links {"tbb", "boost_python37", "pthread"}
        buildoptions { "-pthread"}
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        -- libdirs {
        --     "%{root}/_build/target-deps/octomap/lib64",
        -- }
    filter { "system:windows" }
        -- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
        disablewarnings {"4099"}
        disablewarnings {"4251"} 
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
}

if os.target() == "linux" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/octomap/lib64/*.so.*", ext.target_dir.."/bin" },
    }
else
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/octomap/bin/*.dll", ext.target_dir.."/bin" },
    }
end