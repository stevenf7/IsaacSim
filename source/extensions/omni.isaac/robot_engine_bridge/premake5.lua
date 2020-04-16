local ext_group = "omni.isaac"
local ext_name = "robot_engine_bridge"
local ext_version = ""
local ext_id = "omni.isaac.robot_engine_bridge"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.robot_engine_bridge"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/robot_engine_bridge/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/robot_engine_bridge/scripts" },
    }

    repo_build.prebuild_link {
        { "_build/target-deps/isaac_engine/data/", "_build/$platform/$config/resources/isaac_engine/" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/robot_engine_bridge" },
    }

    repo_build.prebuild_copy {
        { "_build/target-deps/isaac_engine/lib/**", ext_bin_folder },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.robot_engine_bridge.plugin"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/robot_engine_bridge")
        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")


        includedirs {
            "%{root}/source/pch",
            "%{root}/source/extensions/omni.isaac/utils",     
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/python/include/python3.6m",
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
            target_deps_dir.."/isaac_engine/include",
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/include",
            target_deps_dir.."/omni_physics/include",
        }

        libdirs {   
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib",
            target_deps_dir.."/isaac_engine/lib",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/lib",
            "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins" 
        }
        links { 
            "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "isaac_c_api_capnp", "capnp-json", "kj", "capnp", "omni.usd", "lidarSchema"
        }

        filter { "configurations:debug" }
            defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.robot_engine_bridge.python"
        define_bindings_python("_robot_engine_bridge")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/robot_engine_bridge")
