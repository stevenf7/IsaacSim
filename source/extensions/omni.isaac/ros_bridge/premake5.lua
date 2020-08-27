local ext_group = "omni.isaac"
local ext_name = "ros_bridge"
local ext_version = ""
local ext_id = "omni.isaac.ros_bridge"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.ros_bridge"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/ros_bridge/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/ros_bridge/scripts" },

    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/ros_bridge" },
        { "%{root}/_build/target-deps/nv_ros/lib/lib**", ext_bin_folder },
        { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RosBridgeSchema/**", ext_folder.."/omni/isaac/RosBridgeSchema" },
        { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}rosBridgeSchema${lib_ext}", ext_folder.."/bin/$platform/$config"},
    }

    -- C++ Carbonite plugin
    project "omni.isaac.ros_bridge.plugin"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/ros_bridge")
        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        filter { "files:**.cu", "system:linux", "configurations:debug"}
            make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC -g", "-g")
        filter { "files:**.cu", "system:linux", "configurations:release" }
            make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC", "")
        filter {}

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
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/omni_physics/include",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/include",
            "%{root}/source/extensions/omni.isaac/ros_bridge/msgs/melodic",
            target_deps_dir.."/cuda/include"
        }

        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_audio_schema/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_ros/lib",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/lib",
            target_deps_dir.."/cuda/lib64"
        }

        links {
            "gf", "sdf", "usdGeom", "usdUtils", "actionlib", "tf2", "tf2_ros", "roscpp" , "rosBridgeSchema", "cudart_static", "lidarSchema"
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
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/ros_bridge")
