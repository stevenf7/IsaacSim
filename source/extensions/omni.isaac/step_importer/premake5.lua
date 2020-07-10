local ext_group = "omni.isaac"
local ext_name = "step_importer"
local ext_version = ""
local ext_id = "omni.isaac.step_importer"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.step_importer"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/step_importer/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/step_importer/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/step_importer" },
        { "%{root}/_build/target-deps/stepreader/bin/**", ext_bin_folder },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.step_importer.plugin"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()

        staticruntime "Off"
        exceptionhandling "On"

        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/step_importer")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps_dir.."/stepreader/include",
            target_deps_dir.."/python/include/python3.6m",
        }
        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib"
        }
        filter { "system:windows", "platforms:x86_64" }
        libdirs {
            
            target_deps_dir.."/stepreader/lib"
        }
        filter { "system:linux", "platforms:x86_64" }
        libdirs {
            
            target_deps_dir.."/stepreader/bin"
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
    project "omni.isaac.step_importer.python"
        define_bindings_python("_step_importer")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/step_importer")
        includedirs {
            target_deps_dir.."/stepreader/include",
        }

        