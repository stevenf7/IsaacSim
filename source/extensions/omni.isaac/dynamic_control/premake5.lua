local ext_group = "omni.isaac"
local ext_name = "dynamic_control"
local ext_version = ""
local ext_id = "omni/isaac/dynamic_control"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/extensions/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.dynamic_control"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/dynamic_control/python")
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

    -- C++ Carbonite plugin
    project "omni.isaac.dynamic_control.plugin"
        removeplatforms { "aarch64" }
        define_plugin()

        dependson { "omni.usdpch" }
        removeflags { "NoPCH" }
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/dynamic_control")

        targetdir (target_dir.."/extensions/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        -- physx libs
        filter { "system:windows", "platforms:x86_64", "configurations:debug" }
            libdirs { 
                target_deps_dir.."/physx/bin/win.x86_64.vc141.md/debug", 
                target_deps_dir.."/vhacd/bin/win.x86_64.vc141.md/debug" 
            }
            defines {  "PX_PHYSX_STATIC_LIB", "_DEBUG" }
        filter { "system:windows", "platforms:x86_64", "configurations:release" }
            libdirs { 
                target_deps_dir.."/physx/bin/win.x86_64.vc141.md/"..physxLibs, 
                target_deps_dir.."/vhacd/bin/win.x86_64.vc141.md/release" 
            }
            defines {  "PX_PHYSX_STATIC_LIB", "NDEBUG" }
        filter { "system:windows", "platforms:x86_64" }
            libdirs { "_build/target-deps/nvtx/lib/x64" }
            links { "nvToolsExt64_1","PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"}
        filter {}

        includedirs {
            "%{root}/source/pch",
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/include"
        }

        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib"
                }

        links {
            "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils"
        }
        filter { "system:linux" }
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs {
                target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
                target_deps_dir.."/python/include/python3.6m"
            }
        filter { "system:windows" }
            libdirs {
                target_deps_dir.."/tbb/lib/intel64/vc14"
            }
        filter {}

        filter { "configurations:debug" }
            defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.dynamic_control.python"
        define_bindings_python("_dynamic_control")
        add_impl_folder("bindings")
        targetdir (target_dir.."/extensions/"..ext_id.."/bindings")
