local ext_group = "omni.isaac"
local ext_name = "ros_bridge"
local ext_version = ""
local ext_id = "omni/isaac/ros_bridge"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/extensions/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.ros_bridge"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/ros_bridge/python")
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
    project "omni.isaac.ros_bridge.plugin"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/ros_bridge")
        targetdir (target_dir.."/extensions/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            "%{root}/source/pch",
            "%{root}/source/extensions/omni.isaac/utils", 
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
            target_deps_dir.."/carbonite/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps_dir.."/usd_ext/%{cfg.buildcfg}/include", 
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/include",
            target_deps_dir.."/usd_audio_schema/%{cfg.buildcfg}/include",
            target_deps_dir.."/python/include/python3.6m",
            target_deps_dir.."/nv_ros/include",
            target_deps_dir.."/omni_physics/include",
            "%{root}/source/extensions/omni.isaac/ros_bridge/msgs/melodic"
        }

        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_audio_schema/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_ros/lib"
        }
        links {
            "gf", "sdf", "usdGeom", "usdUtils", "actionlib", "tf2", "tf2_ros", "roscpp" 
        }
        filter { "configurations:debug" }
                defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}
        
    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.ros_bridge.python"
        define_bindings_python("_ros_bridge")
        add_impl_folder("bindings")
        targetdir (target_dir.."/extensions/"..ext_id.."/bindings")
