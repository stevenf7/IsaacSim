local ext_name = "omni.isaac.decals"
local ext_version = ""
local ext_id = ext_name
local ext_source = "source/extensions/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.decals"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac.decals/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/decals/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/decals" },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.decals.plugin"
        removeplatforms { "aarch64" }
        define_plugin()

        dependson { "omni.usdpch" }
        removeflags { "NoPCH" }
        apply_pch()

        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/decals")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs { 
            "%{root}/source/pch",
            "%{root}/_build/target-deps/carb_gfx_plugins/include",
            "%{root}/_build/target-deps/rtx_plugins/include",
            "%{root}/_build/target-deps/python/include",
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost" }

        libdirs {   "%{root}/_build/target-deps/python/libs",
                    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
                    "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
                    "%{root}/_build/target-deps/nv_usd/release/lib",
                    "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins" 
                }

        links {
            "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
            "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "omni.usd"
        }
        filter { "system:linux" }
            exceptionhandling "On"
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            includedirs { "%{root}/_build/target-deps/python/include/python3.6m" }

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.decals.python"
        define_bindings_python("_decals")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/decals")
