local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.mjcf.plugin")

    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/mjcf/**")
    add_files("iface", "%{root}/include/omni/isaac/math/**")


    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/assimp/include",
        "%{root}/_build/target-deps/python/include",
        "%{root}/_build/target-deps/tinyxml2/include",
        "%{root}/_build/target-deps/omni_client_library/include",
    }

    libdirs {   
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/client_library/%{cfg.buildcfg}",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",

        "%{root}/_build/target-deps/tinyxml2/lib",
        "%{root}/_build/target-deps/assimp/lib64",
        "%{kit_sdk_bin_dir}/plugins",
        "%{root}/_build/target-deps/omni_client_library/%{cfg.buildcfg}",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin"
    }

    links { 
        "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", 
        "usdPhysics", "physicsSchemaTools", "physxSchema", "omni.usd", "tinyxml2", "assimp", "tbb", "omniclient"
    }
    
    if os.target() == "linux" then
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m",
        }
        libdirs {
            "%{root}/_build/target-deps/assimp/lib64",
        }
        links {
            "stdc++fs"
        }
    else
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
            "%{root}/_build/target-deps/assimp/lib",
        }
    end
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.mjcf.python",
    module = "_mjcf",
    src = "bindings",
    target_subdir = "omni/isaac/mjcf"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/mjcf/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/mjcf/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

if os.target() == "linux" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/assimp/lib64/lib**", ext.target_dir.."/bin" },
        { "%{root}/_build/target-deps/tinyxml2/lib/lib**", ext.target_dir.."/bin" },
    }
else
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/assimp/bin/*.dll", ext.target_dir.."/bin" },
        { "%{root}/_build/target-deps/tinyxml2/bin/*.dll", ext.target_dir.."/bin" },
    }
end

repo_build.prebuild_copy {
    
    { "python/*.py", ext.target_dir.."/omni/isaac/mjcf" },
}

