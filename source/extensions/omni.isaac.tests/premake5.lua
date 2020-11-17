local ext = get_current_extension_info()
project_ext (ext)


if os.target() == "linux" then
    repo_build.prebuild_link {
        { "config/linux", ext.target_dir.."/config" },
        { "python/motion_planning", ext.target_dir.."/omni/isaac/tests/motion_planning" },
        { "python/robot_engine_bridge", ext.target_dir.."/omni/isaac/tests/robot_engine_bridge" },
    }
else
    repo_build.prebuild_link {
        { "config/windows", ext.target_dir.."/config" },
    }
end

repo_build.prebuild_link {
    { "python/utils", ext.target_dir.."/omni/isaac/tests/utils" },
    { "python/dynamic_control", ext.target_dir.."/omni/isaac/tests/dynamic_control" },
    { "python/samples", ext.target_dir.."/omni/isaac/tests/samples" },
    { "python/urdf", ext.target_dir.."/omni/isaac/tests/urdf" },
    { "python/step_importer", ext.target_dir.."/omni/isaac/tests/step_importer" },
    { "python/lidar", ext.target_dir.."/omni/isaac/tests/lidar" },
    { "python/domain_randomizer", ext.target_dir.."/omni/isaac/tests/domain_randomizer" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/tests" },
    { "data/**", ext.target_dir.."/omni/isaac/tests/data" },
}
