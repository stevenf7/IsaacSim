local ext_group = "omni.isaac"
local ext_name = "decals"
local ext_version = ""
local ext_id = "omni.isaac.decals"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.decals"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/decals/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/decals/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/decals" },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.decals.plugin"
        removeplatforms { "aarch64" }
        define_plugin()
        
        staticruntime "Off"
        exceptionhandling "On"

        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/decals")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs { 
            "%{root}/source/pch",
            target_deps_dir.."/carb_gfx_plugins/include",
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/python/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost" }

        libdirs {   target_deps_dir.."/python/libs",
                    target_deps_dir.."/tbb/lib/intel64/vc14",
                    target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
                    target_deps_dir.."/nv_usd/release/lib",
                    "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins" 
                }

        links {
            "gf", "sdf", "tf", "usd", "usdGeom", "vt", "usdUtils", "omni.usd"
        }
        filter { "system:linux" }
            exceptionhandling "On"
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs { target_deps_dir.."/python/include/python3.6m" }

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.decals.python"
        define_bindings_python("_decals")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/decals")
