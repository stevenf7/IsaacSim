local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.urdf.plugin")

    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
    staticruntime "Off"
    exceptionhandling "On"
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/urdf/**")

    includedirs {
        "%{root}/source/pch",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/assimp/include",
        "%{root}/_build/target-deps/python/include",
        "%{root}/_build/target-deps/tinyxml2/include",
        "%{root}/_build/target-deps/client_library/include",
    }

    libdirs {   
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/assimp/lib",
        "%{root}/_build/target-deps/tinyxml2/lib",
        "%{kit_sdk_bin_dir}/plugins",
    }

    links { 
        "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", "usdPhysics", "physicsSchemaTools", "physxSchema", "omni.usd", "assimp", "tinyxml2"
    }
    
    if os.target() == "linux" then
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.6m",
        }
    else
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
        }
    end
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.urdf.python",
    module = "_urdf",
    src = "bindings",
    target_subdir = "omni/isaac/urdf"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/urdf/scripts" },
}

repo_build.prebuild_copy {
    { "%{root}/_build/target-deps/assimp/lib/lib**", ext.target_dir.."/bin" },
    { "%{root}/_build/target-deps/tinyxml2/lib/lib**", ext.target_dir.."/bin" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/urdf" },
}
