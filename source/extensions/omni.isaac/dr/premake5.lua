local ext_group = "omni.isaac"
local ext_name = "dr"
local ext_version = ""
local ext_id = "omni.isaac.dr"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.dr"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/dr/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/dr/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/dr" },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.dr.plugin"
        removeplatforms { "aarch64" }
        define_plugin()

        staticruntime "Off"
        exceptionhandling "On"

        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/dr")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            "%{root}/source/pch",
            "%{root}/source/extensions/omni.isaac/utils", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/usd_audio_schema/%{cfg.buildcfg}/include",
            target_deps_dir.."/carb_gfx_plugins/include",
            target_deps_dir.."/rtx_plugins/include"
         }

        libdirs {
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib",
            target_deps_dir.."/usd_audio_schema/%{cfg.buildcfg}/lib",
            "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins"             
        }

        links {
            "arch", "gf", "pcp", "tf", "sdf", "usd", "usdGeom", "usdShade", "vt", "usdUtils", "audioSchema", "omni.usd"
        }
        filter { "system:linux" }
            exceptionhandling "On"
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs { target_deps_dir.."/python/include/python3.6m" }
        filter {}

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.dr.python"
        define_bindings_python("_dr")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/dr")
