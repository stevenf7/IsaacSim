local ext = get_current_extension_info()
project_ext (ext)


-- if os.target() == "linux" then
--     repo_build.prebuild_link {
--         { ext_source.."/config/linux", ext_folder.."/config" },
--         { ext_source.."/python/motion_planning", ext_folder.."/omni/isaac/tests/motion_planning" },
--         { ext_source.."/python/robot_engine_bridge", ext_folder.."/omni/isaac/tests/robot_engine_bridge" },
--     }
-- else
--     repo_build.prebuild_link {
--         { ext_source.."/config/windows", ext_folder.."/config" },
--     }
-- end
-- repo_build.prebuild_link {
--     { ext_source.."/python/utils", ext_folder.."/omni/isaac/tests/utils" },
--     { ext_source.."/python/dynamic_control", ext_folder.."/omni/isaac/tests/dynamic_control" },
--     { ext_source.."/python/samples", ext_folder.."/omni/isaac/tests/samples" },
--     { ext_source.."/python/urdf", ext_folder.."/omni/isaac/tests/urdf" },
--     { ext_source.."/python/step_importer", ext_folder.."/omni/isaac/tests/step_importer" },
--     { ext_source.."/python/lidar", ext_folder.."/omni/isaac/tests/lidar" },
--     { ext_source.."/python/domain_randomizer", ext_folder.."/omni/isaac/tests/domain_randomizer" },
-- }

-- repo_build.prebuild_copy {
--     { ext_source.."/python/*.py", ext_folder.."/omni/isaac/tests" },
--     { ext_source.."/data/**", ext_folder.."/omni/isaac/tests/data" },
-- }
