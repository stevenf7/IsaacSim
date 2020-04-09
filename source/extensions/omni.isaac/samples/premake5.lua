local ext_group = "omni.isaac"
local ext_name = "samples"
local ext_version = ""
local ext_id = "omni.isaac.samples"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)

    repo_build.prebuild_link {
        { ext_source.."/leonardo_preview", ext_folder..".leonardo_preview".."/omni/isaac/samples/leonardo_preview" },
        { ext_source.."/utils", ext_folder..".leonardo_preview".."/omni/isaac/samples/utils" },
    }

    repo_build.prebuild_link {
        { ext_source.."/ur10_preview", ext_folder..".ur10_preview".."/omni/isaac/samples/ur10_preview" },
        { ext_source.."/utils", ext_folder..".ur10_preview".."/omni/isaac/samples/utils" },
    }

    -- Example of python extension. Contains python sources, doesn't build or run, only for MSVS.
    -- if os.target() == "windows" then
    --     project "omni.isaac.samples"
    --         kind "None"
    --         --add_impl_folder("")

    --         vpaths { ["*"] = ext_folder }
    --         files { ext_folder.."/**.py" }
    --         files { ext_folder.."/**.toml" }
        
    -- end
