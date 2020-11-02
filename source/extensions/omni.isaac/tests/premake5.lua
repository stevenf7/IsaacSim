local ext_group = "omni.isaac"
local ext_name = "tests"
local ext_version = ""
local ext_id = "omni.isaac.tests"
local ext_source = "%{root}/source/extensions/"..ext_group.."/"..ext_name
local ext_folder = "%{root}/_build/$platform/$config/exts/"..ext_id
local ext_bin_folder = ext_folder.."/bin/$platform/$config"

group ("extensions/"..ext_id)

    -- Python code. Contains python sources, doesn't build or run, only for MSVS.
    if os.target() == "windows" then
        project "omni.isaac.tests"
            kind "None"
            add_impl_folder("source/extensions/omni.isaac/tests/python")
    end

    if os.target() == "linux" then
    repo_build.prebuild_link {
        { ext_source.."/config/linux", ext_folder.."/config" },
        { ext_source.."/python/motion_planning", ext_folder.."/omni/isaac/tests/motion_planning" },
        { ext_source.."/python/robot_engine_bridge", ext_folder.."/omni/isaac/tests/robot_engine_bridge" },
    }
    else
    repo_build.prebuild_link {
        { ext_source.."/config/windows", ext_folder.."/config" },
    }
    end
    repo_build.prebuild_link {
        { ext_source.."/python/utils", ext_folder.."/omni/isaac/tests/utils" },
        { ext_source.."/python/dynamic_control", ext_folder.."/omni/isaac/tests/dynamic_control" },
        { ext_source.."/python/samples", ext_folder.."/omni/isaac/tests/samples" },
        { ext_source.."/python/urdf", ext_folder.."/omni/isaac/tests/urdf" },
        { ext_source.."/python/step_importer", ext_folder.."/omni/isaac/tests/step_importer" },
        { ext_source.."/python/lidar", ext_folder.."/omni/isaac/tests/lidar" },
        { ext_source.."/python/domain_randomizer", ext_folder.."/omni/isaac/tests/domain_randomizer" },
    }

    repo_build.prebuild_copy {
        { ext_source.."/python/*.py", ext_folder.."/omni/isaac/tests" },
        { ext_source.."/data/**", ext_folder.."/omni/isaac/tests/data" },
    }
