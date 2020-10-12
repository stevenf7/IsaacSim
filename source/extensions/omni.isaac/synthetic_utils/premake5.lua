local ext_group = "omni.isaac"
local ext_name = "synthetic_utils"
local ext_version = ""
local ext_id = "omni.isaac.synthetic_utils"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.synthetic_utils"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/synthetic_utils/python")
    end

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/synthetic_utils/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/synthetic_utils" },
    }
