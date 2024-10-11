local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/sensors/rtx")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, ogn.plugin_project)
    cppdialect "C++17"

    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin"}
    add_files("impl", "plugins")
    add_files("nodes", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    add_cuda_dependencies()

    includedirs {
        "%{root}/source/extensions/isaacsim.core.includes/include",
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
        "%{root}/source/deprecated/omni.isaac.dynamic_control/include",
        bin_dir.."/extsbuild/omni.sensors.nv.common/include",
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

project_ext_bindings {
    ext = ext,
    project_name = ogn.python_project,
    module = ogn.bindings_module,
    src = ogn.bindings_path,
    target_subdir = ogn.bindings_target_path
}
    add_files("bindings", "bindings/*.*")
    add_files("python", "python/*.py")
    add_files("python/scripts", "python/scripts/**.py")
    add_files("python/tests", "python/tests/**.py")


    add_ogn_dependencies(ogn)

    repo_build.prebuild_link {
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "python/scripts", ogn.python_target_path.."/scripts" },
        { "python/tests", ogn.python_target_path.."/tests" },
    }

    repo_build.prebuild_copy {
        { "python/__init__.py", ogn.python_target_path },
    }
