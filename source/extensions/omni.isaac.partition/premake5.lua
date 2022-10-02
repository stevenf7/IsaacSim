local ext = get_current_extension_info()
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.partition.plugin")
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
 
    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin", "omni.kit.window.file_exporter"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/partition/**")

    include_physx()

    staticruntime "Off"

    includedirs {
        "%{root}/include/pch",
        targetDepsDir.."/carbonite/include",
        targetDepsDir.."/physx/include",
        targetDepsDir.."/pxshared/include",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/include",
        targetDepsDir.."/omni_physics/include",
        targetDepsDir.."/rtx_plugins/include",
        targetDepsDir.."/client_library/include",
        "./include",
        "%{root}/_build/target-deps/omni_client_library/include",
     }
    libdirs {
        "%{root}/_build/target-deps/python/libs",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/client_library/%{cfg.buildcfg}",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
    }

    links { "gf", "vt", "tf", "sdf", "usd", "usdGeom", "usdShade", "usdImaging", "usdUtils", "physxSchema", "usdPhysics", "physicsSchemaTools", "omni.usd", "arch", "work", "carb", "kind"}
 
    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m",
        }
        links {
            "stdc++fs"
        }
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

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.partition.python",
    module = "_partition",
    src = "bindings",
    target_subdir = "omni/isaac/partition"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/partition/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/partition/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/partition" },
}
