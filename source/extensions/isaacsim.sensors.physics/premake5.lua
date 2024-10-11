local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/sensors/physics")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "isaacsim.sensors.physics.plugin")
    cppdialect "C++17"

    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin"}
    add_files("impl", "plugins")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    add_cuda_dependencies()

    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/include",
        targetDepsDir.."/omni_physics/%{config}/include",
        targetDepsDir.."/rtx_plugins/include",
        extsbuild_dir.."/usdrt.scenegraph/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        targetDepsDir.."/omni_client_library/include",
        targetDepsDir.."/python/include",
        "%{root}/source/extensions/isaacsim.core.nodes/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/source/extensions/isaacsim.sensors.physics/include",
        "%{root}/source/deprecated/omni.isaac.dynamic_control/include",
    }
    libdirs {
        targetDepsDir.."/python/lib",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/lib",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
        extsbuild_dir.."/omni.usd.core/bin"
    }

    links {"carb", "gf", "tf", "sdf", "usd", "usdGeom","usdUtils", "physxSchema","usdPhysics", "physicsSchemaTools", "omni.usd", "isaacSensorSchema", "arch", "vt"}

    filter { "system:linux" }
        includedirs {
            targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include/boost",
            targetDepsDir.."/python/include/python3.10"
        }
    filter { "system:windows" }
        libdirs {
            targetDepsDir.."/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}


project_ext_ogn( ext, ogn )

-- Python Bindings for Carbonite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.sensors.physics.python",
    module = "_sensor",
    src = "bindings",
    target_subdir = "isaacsim/sensors/physics"
}

    includedirs {
        "%{root}/source/extensions/isaacsim.sensors.physics/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
    }

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/isaacsim/sensors/physics/scripts" },
    { "python/tests", ext.target_dir.."/isaacsim/sensors/physics/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/isaacsim/sensors/physics" },
}
