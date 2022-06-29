local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/isaac_sensor")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.isaac_sensor.plugin")
    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin", "omni.isaac.debug_draw.primitive_drawing"}
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/isaac_sensor/**")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"nodes"})


    include_physx()

    includedirs {
        "%{root}/include/pch",
        targetDepsDir.."/physx/include",
        targetDepsDir.."/pxshared/include",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/include",
        targetDepsDir.."/omni_physics/include",
        targetDepsDir.."/rtx_plugins/include",
        targetDepsDir.."/client_library/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
     }
    libdirs {
        "%{root}/_build/target-deps/python/libs",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
    }

    links {"gf", "tf", "sdf", "usd", "usdGeom","usdUtils", "physxSchema","usdPhysics", "physicsSchemaTools", "omni.usd", "isaacSensorSchema",  "omni.isaac.debug_draw.primitive_drawing", "arch"}

    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m"
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


project_ext_ogn( ext, ogn )

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.isaac_sensor.python",
    module = "_isaac_sensor",
    src = "bindings",
    target_subdir = "omni/isaac/isaac_sensor"
}
    add_ogn_dependencies(ogn)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/isaac_sensor/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/isaac_sensor/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "python/impl", ogn.python_target_path.."/impl" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/isaac_sensor" },
}
