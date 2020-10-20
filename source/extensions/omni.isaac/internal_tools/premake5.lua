local ext_group = "omni.isaac"
local ext_name = "internal_tools"
local ext_version = ""
local ext_id = "omni.isaac.internal_tools"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/internal_tools" },
        { ext_source.."/python/utils/*.py", ext_folder.."/omni/isaac/internal_tools/utils" },
    }
