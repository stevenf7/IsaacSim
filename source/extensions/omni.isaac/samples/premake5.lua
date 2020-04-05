local ext_group = "omni.isaac"
local ext_name = "samples"
local ext_version = ""
local ext_id = "omni.isaac.samples"
local ext_source = "source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)

repo_build.prebuild_link {
    { ext_source.."/python/scripts", ext_folder.."/omni/isaac/samples/scripts" },
}

    -- Example of python extension. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.samples"
            kind "None"
            --add_impl_folder("")

            vpaths { ["*"] = ext_folder }
            files { ext_folder.."/**.py" }
            files { ext_folder.."/**.toml" }
        
    end
