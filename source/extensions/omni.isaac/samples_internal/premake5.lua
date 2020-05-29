local ext_group = "omni.isaac"
local ext_name = "samples_internal"
local ext_version = ""
local ext_id = "omni.isaac.samples_internal"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id

group ("extensions/"..ext_id)
    
if os.target() == "linux" then
    repo_build.prebuild_link {
        { ext_source.."/config/linux", ext_folder.."/config" },
    }
else
    repo_build.prebuild_link {
        { ext_source.."/config/windows", ext_folder.."/config" },
    }
end

    repo_build.prebuild_link {
        { ext_source.."/python/scripts", ext_folder.."/omni/isaac/samples_internal/scripts" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/samples_internal" },
    }