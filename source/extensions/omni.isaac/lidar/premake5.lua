local ext_group = "omni.isaac"
local ext_name = "lidar"
local ext_version = ""
local ext_id = "omni.isaac.lidar"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.lidar"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/lidar/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/lidar/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/lidar" },
    }

    repo_build.prebuild_copy {
        { "_build/target-deps/usd_ext_isaac/$config/lib/python/LidarSchema/**", ext_folder.."/omni/isaac/LidarSchema" },
        { "_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}lidarSchema${lib_ext}", ext_folder.."/bin/$platform/$config"},
    }

    -- C++ Carbonite plugin
    project "omni.isaac.lidar.plugin"
        removeplatforms { "aarch64" }
        define_plugin()
        
        rtti "On"  -- fixes: 'dynamic_cast' used on polymorphic type
        staticruntime "Off"
        exceptionhandling "On"

        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/lidar")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")
        -- physx libs
        filter { "system:windows", "platforms:x86_64", "configurations:debug" }
        libdirs { 
            target_deps_dir.."/physx/bin/win.x86_64.vc141.md/debug", 
            target_deps_dir.."/vhacd/bin/win.x86_64.vc141.md/debug" 
        }
        filter { "system:windows", "platforms:x86_64", "configurations:release" }
            libdirs { 
                target_deps_dir.."/physx/bin/win.x86_64.vc141.md/"..physxLibs, 
                target_deps_dir.."/vhacd/bin/win.x86_64.vc141.md/release" 
            }
        filter { "system:windows", "platforms:x86_64" }
            libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
            links { "nvToolsExt64_1"}
        filter { "system:linux", "platforms:x86_64", "configurations:debug" }
            libdirs { 
                target_deps_dir.."/physx/bin/linux.clang/debug", 
                target_deps_dir.."/vhacd/bin/linux.clang/debug" 
            }
        filter { "system:linux", "platforms:x86_64", "configurations:release" }
            libdirs { 
                target_deps_dir.."/physx/bin/linux.clang/"..physxLibs, 
                target_deps_dir.."/vhacd/bin/linux.clang/release" 
            }
        filter { "system:linux", "platforms:x86_64" }
            libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
            links { "nvToolsExt"}
        filter {}
        defines {  "PX_PHYSX_STATIC_LIB"}
        includedirs { 
            "%{root}/source/pch",
            "%{root}/source/extensions/omni.isaac/utils",
            ext_source.."/plugins/",
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/carb_gfx_plugins/include",
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/include",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/include",
            target_deps_dir.."/omni_physics/include"

        }

        libdirs {               
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib",
            target_deps_dir.."/usd_ext_isaac/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
            "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins" 
        }
        links {
            "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "lidarSchema", "omni.usd", "physicsSchema",
            "PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"
        }
        filter { "system:windows" }
            libdirs {target_deps_dir.."/tbb/lib/intel64/vc14"}
        filter {}
        removeflags { "FatalCompileWarnings"}
        filter { "system:linux" }
            exceptionhandling "On"
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs { target_deps_dir.."/python/include/python3.6m" }
        filter {}

        filter { "configurations:debug" }
            defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.lidar.python"
        define_bindings_python("_lidar")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/lidar")
