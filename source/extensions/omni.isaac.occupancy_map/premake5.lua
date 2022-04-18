local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.occupancy_map.plugin")
    dependson {"omni.isaac.debug_draw.primitive_drawing"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    include_physx()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{root}/_build/target-deps/octomap/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    }
    links {"octomap", "octomath", "usdUtils", "omni.usd", "omni.isaac.debug_draw.primitive_drawing", "usdPhysics", "sdf", "tf", "usd"}
    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        libdirs {
            "%{root}/_build/target-deps/octomap/lib64",
        }
    filter { "system:windows" }
        -- Warning C4099: 'omni::physx::IPhysx': type name first seen using 'class' now seen using 'struct'
        disablewarnings {"4099"}
        disablewarnings {"4251"}
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
            "%{root}/_build/target-deps/octomap/%{cfg.buildcfg}/lib",
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


    include_physx()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/octomap/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
    }
    links {"sdf", "tf", "usd", "usdUtils", "usdPhysics"}

    filter { "system:linux" }
        links {"tbb", "boost_python37", "pthread", "octomap", "octomath"}
        buildoptions { "-pthread"}
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        libdirs {
            "%{root}/_build/target-deps/octomap/lib64",
        }
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
        { "%{root}/_build/target-deps/octomap/%{config}/bin/*.dll", ext.target_dir.."/bin" },
    }
end