local ext_group = "omni.isaac"
local ext_name = "utils"
local ext_version = ""
local ext_id = "omni.isaac.utils"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.utils"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/utils/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/utils" },
    }

    -- Python Bindings for Carobnite Plugin
    project "omni.isaac.utils.python"
        define_bindings_python("_isaac_utils")
        add_impl_folder("bindings")
        targetdir (target_dir.."/exts/"..ext_id.."/omni/isaac/utils")
        includedirs {
            "%{root}/source/pch",
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/include",
            target_deps_dir.."/carb_gfx_plugins/include",
            target_deps_dir.."/rtx_plugins/include",
            target_deps_dir.."/physx/include",
            target_deps_dir.."/pxshared/include",
        }

        libdirs {   
            target_deps_dir.."/python/libs", 
            target_deps_dir.."/nv_usd/%{cfg.buildcfg}/lib",
            target_deps_dir.."/nv_usd/release/lib"
        }
        links {"gf", "sdf"}

        filter { "system:linux", "platforms:x86_64" }
            links {"tbb", "boost_python36" }
        filter {}

        filter { "configurations:debug" }
            defines { "_DEBUG" }
        filter { "configurations:release" }
            defines { "NDEBUG" }
        filter {}

