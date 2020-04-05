local ext_group = "omni.isaac"
local ext_name = "motion_planning"
local ext_version = ""
local ext_id = "omni/isaac/motion_planning"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/extensions/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.motion_planning"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/motion_planning/python")
    end

    -- repo_build.prebuild_link {
    --     { ext_source.."/config", ext_folder.."/config" },
    -- }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."" },
    }

    repo_build.prebuild_copy {
        { "_build/target-deps/lula/lib/**", ext_bin_folder },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.motion_planning.plugin"
        cppdialect "C++17"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/motion_planning")
        targetdir (target_dir.."/extensions/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps_dir.."/lula/include",
            target_deps_dir.."/python/include/python3.6m",
        }

        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/lula/lib"
        }
        links { 
            "gf", "sdf", "usdGeom", "usdUtils", "lula_opt", "lula_kinematics", "lula_math" , "lula_rmpflow", "lula_util", "yaml-cpp", "urdfdom_model", "glog"
        }

        filter { "configurations:debug" }
                defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}
        
    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.motion_planning.python"
        define_bindings_python("_motion_planning")
        add_impl_folder("bindings")
        targetdir (target_dir.."/extensions/"..ext_id.."/bindings")
        includedirs {target_deps_dir.."/lula/include"}
        cppdialect "C++17"
