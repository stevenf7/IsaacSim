local ext = get_current_extension_info()
project_ext (ext)
-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.step_importer.plugin")


    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/step_importer/**")

    includedirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/stepreader/include",
        "%{root}/_build/target-deps/python/include/python3.6m",
    }
    libdirs {   
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib"
    }
    filter { "system:windows", "platforms:x86_64" }
    libdirs {
        
        "%{root}/_build/target-deps/stepreader/lib"
    }
    filter { "system:linux", "platforms:x86_64" }
    libdirs {
        
        "%{root}/_build/target-deps/stepreader/bin"
    }
    filter {}
    links { 
        "gf", "sdf", "usdGeom", "usdUtils", "step_reader"
    }

    filter { "configurations:debug" }
            defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
                            ext = ext,
                            project_name = "omni.isaac.step_importer.python",
                            module = "_step_importer",
                            src = "bindings",
                            target_subdir = "omni/isaac/step_importer"
                        })
    includedirs {
        "%{root}/_build/target-deps/stepreader/include",
    }

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/step_importer/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/step_importer/tests" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "%{root}/_build/target-deps/stepreader/bin/**", ext.target_dir.."/bin" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/step_importer" },
}
