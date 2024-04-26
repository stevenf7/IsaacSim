local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/conveyor")


-- Put this project into the omnigraph IDE group
ext.group = "omnigraph"

project_ext(ext)

project_ext_plugin(ext, "omni.isaac.conveyor.plugin")
    add_files("impl", "plugins")
    add_files("ogn", ogn.nodes_path)

    
    include_physx()
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        target_deps.."/rtx_plugins/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include",
        target_deps.."/nv_usd/%{cfg.buildcfg}/include/boost",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/include",
        target_deps.."/omni_physics/include",
        target_deps.."/omni_client_library/include"
    }
    libdirs {
        target_deps.."/nv_usd/%{cfg.buildcfg}/lib",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }

    -- Linux-specific compile information
    filter { "system:linux" }
    exceptionhandling "On"
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
    includedirs {
        target_deps.."/nv_usd/%{config}/include/boost",
        target_deps.."/python/include/python3.10"
    }
    filter {}
    
    add_ogn_dependencies(ogn)
    -- Specifies the external libraries required by the nodes
    links {"vt", "gf", "sdf", "arch", "usd", "tf", "usdUtils", "usdShade", "usdGeom", "usdSkel", "omni.usd", "usdPhysics",}


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
    add_files("python/impl", "python/impl/**.py")
    add_files("python/tests", "python/tests/**.py")
    add_files("python/conveyor_builder", "python/conveyor_builder/**.py")

    add_ogn_dependencies(ogn)

    repo_build.prebuild_link {
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "python/impl", ogn.python_target_path.."/impl" },    
        { "python/tests", ogn.python_target_path.."/tests" },    
        { "python/commands", ogn.python_target_path.."/commands" },    
        { "python/conveyor_builder", ogn.python_target_path.."/conveyor_builder" },  
    }

    repo_build.prebuild_copy {
        { "python/__init__.py", ogn.python_target_path },
    }