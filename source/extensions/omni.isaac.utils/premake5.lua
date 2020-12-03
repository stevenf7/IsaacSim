local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.utils.plugin")

    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
    
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/utils/**")

-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
                        ext = ext,
                        project_name = "omni.isaac.utils.python",
                        module = "_isaac_utils",
                        src = "bindings",
                        target_subdir = "omni/isaac/utils"
                    })

    includedirs {
        "%{root}/source/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
    }

    libdirs {   
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"gf", "sdf"}

    filter { "system:linux", "platforms:x86_64" }
        links {"tbb", "boost_python36" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}



repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/utils/scripts" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/utils" },
}
