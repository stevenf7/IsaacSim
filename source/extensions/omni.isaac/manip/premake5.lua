local ext_group = "omni.isaac"
local ext_name = "manip"
local ext_version = ""
local ext_id = "omni.isaac.manip"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.manip"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/manip/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/manip/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/manip" },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.manip.plugin"
        removeplatforms { "aarch64" }
        define_plugin()

        staticruntime "Off"
        exceptionhandling "On"

        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/manip")
        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            "%{root}/source/pch",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/carb_gfx_plugins/include",
            target_deps_dir.."/rtx_plugins/include"
        }

        libdirs {   
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib"
        }
        links { 
            "sdf", "usdUtils",
        }

        filter { "system:windows" }
            libdirs {target_deps_dir.."/tbb/lib/intel64/vc14"}
        filter {}

        filter { "system:linux" }
            exceptionhandling "On"
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs { target_deps_dir.."/python/include/python3.6m" }
        filter {}

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.manip.python"
        define_bindings_python("_manip")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/manip")
