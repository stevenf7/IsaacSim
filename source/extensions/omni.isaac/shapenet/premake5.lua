local ext_group = "omni.isaac"
local ext_name = "shapenet"
local ext_version = ""
local ext_id = "omni.isaac.shapenet"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)

    repo_build.prebuild_link {
        { ext_source.."/config", ext_folder.."/config" },
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/shapenet/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/shapenet" },
    }

    -- Example of python extension. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.shapenet"
            kind "None"
            --add_impl_folder("")

            vpaths { ["*"] = ext_folder }
            files { ext_folder.."/**.py" }
            files { ext_folder.."/**.toml" }
        
    end
