local ext_group = "omni.isaac"
local ext_name = "exploded_view"
local ext_version = ""
local ext_id = "omni.isaac.exploded_view"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)
    

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/exploded_view/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/exploded_view" },
    }

    -- project "omni.isaac.exploded_view"
    -- kind "None"
    -- --add_impl_folder("")

    -- vpaths { ["*"] = ext_folder }
    -- files { ext_folder.."/**.py" }
    -- files { ext_folder.."/**.toml" }