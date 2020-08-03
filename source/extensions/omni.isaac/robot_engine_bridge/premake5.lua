local ext_group = "omni.isaac"
local ext_name = "robot_engine_bridge"
local ext_version = ""
local ext_id = "omni.isaac.robot_engine_bridge"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/robot_engine_bridge/scripts" },
        { "%{root}/_build/target-deps/isaac_engine/data/", ext_folder.."/resources/isaac_engine/" },
        { "%{root}/_build/target-deps/isaac_engine/packages/", ext_folder.."/packages/" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/robot_engine_bridge" },
        { ext_source.."/python/__init__.py", target_deps_dir.."/kit_sdk_$config/_build/$platform/$config/exts/omni.syntheticdata/omni/syntheticdata/__init__.py" },
        { "%{root}/_build/target-deps/isaac_engine/lib/**", ext_bin_folder },
        { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RobotEngineBridgeSchema/**", ext_folder.."/omni/isaac/RobotEngineBridgeSchema" },
        { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}robotEngineBridgeSchema${lib_ext}", ext_folder.."/bin/$platform/$config"},
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

        filter { "files:**.cu", "system:linux", "configurations:debug"}
            make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC -g", "-g")
        filter { "files:**.cu", "system:linux", "configurations:release" }
            make_nvcc_command(nvccPath, nvccHostCompilerVS, "-fPIC", "")
        filter {}

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
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/include",
            target_deps_dir.."/omni_physics/include",
            target_deps_dir.."/cuda/include"
        }

        libdirs {   
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib",
            target_deps_dir.."/isaac_engine/lib",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
            "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins" 
        }

        filter { "system:linux", "platforms:x86_64", "configurations:debug" }
            libdirs { 
                target_deps_dir.."/physx/bin/linux.clang/debug", 
            }
            defines {  "PX_PHYSX_STATIC_LIB", "_DEBUG" }
        filter { "system:linux", "platforms:x86_64", "configurations:release" }
            libdirs { 
                target_deps_dir.."/physx/bin/linux.clang/"..physxLibs, 
            }
            defines {  "PX_PHYSX_STATIC_LIB", "NDEBUG" }
        filter {}
        links { 
            "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "isaac_c_api_capnp", "capnp-json", "kj", "capnp", "omni.usd", "lidarSchema", "robotEngineBridgeSchema", "physxSchema", "PhysXVehicle_static_64"
        }


        filter { "system:linux", "platforms:x86_64" }
            libdirs { target_deps_dir.."/cuda/lib64" }
            links { "cudart_static" }
        filter {}

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
