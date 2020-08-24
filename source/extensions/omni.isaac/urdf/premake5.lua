local ext_group = "omni.isaac"
local ext_name = "urdf"
local ext_version = ""
local ext_id = "omni.isaac.urdf"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.urdf"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/urdf/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/urdf/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/urdf" },
        { "%{root}/_build/target-deps/assimp/lib/lib**", ext_bin_folder },
        { "%{root}/_build/target-deps/tinyxml2/lib/lib**", ext_bin_folder },
    }

    -- C++ Carbonite plugin
    project "omni.isaac.urdf.plugin"
        removeplatforms { "aarch64" }
        removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
        define_plugin()
        staticruntime "Off"
        apply_pch()
        add_impl_folder("plugins")
        add_iface_folder("%{root}/include/omni/isaac/urdf")

        targetdir (target_dir.."/exts/"..ext_id.."/bin/%{platform}/%{cfg.buildcfg}")

        includedirs {
            "%{root}/source/pch",
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/include",
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/assimp/include",
            target_deps_dir.."/python/include",
            target_deps_dir.."/tinyxml2/include",
        }

        libdirs {   
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib",
            target_deps_dir.."/usd_ext_physics/%{cfg.buildcfg}/lib",
            target_deps_dir.."/assimp/lib",
            target_deps_dir.."/tinyxml2/lib",
            "%{kit_sdk}/_build/%{platform}/%{cfg.buildcfg}/plugins"   
        }

        links { 
            "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", "physicsSchema", "physicsSchemaTools", "physxSchema", "omni.usd", "assimp", "tinyxml2"
        }
        
        if os.target() == "linux" then
            includedirs {
                target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include/boost",
                target_deps_dir.."/python/include/python3.6m",
            }
        else
            libdirs {
                target_deps_dir.."/tbb/lib/intel64/vc14",
            }
        end
        
    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.urdf.python"
        define_bindings_python("_urdf")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/urdf")

