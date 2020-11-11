local ext = get_current_extension_info()
project_ext (ext)


-- if os.target() == "linux" then
--     repo_build.prebuild_link {
--         { "%{root}/source/extensions/omni.isaac.tests/config/linux", ext.target_dir.."/config" },
--         { "%{root}/source/extensions/omni.isaac.tests/python/motion_planning", ext.target_dir.."/omni/isaac/tests/motion_planning" },
--         { "%{root}/source/extensions/omni.isaac.tests/python/robot_engine_bridge", ext.target_dir.."/omni/isaac/tests/robot_engine_bridge" },
--     }
-- else
--     repo_build.prebuild_link {
--         { "%{root}/source/extensions/omni.isaac.tests/config/windows", ext.target_dir.."/config" },
--     }
-- end
-- repo_build.prebuild_link {
--     { "%{root}/source/extensions/omni.isaac.tests/python/utils", ext.target_dir.."/omni/isaac/tests/utils" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/dynamic_control", ext.target_dir.."/omni/isaac/tests/dynamic_control" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/samples", ext.target_dir.."/omni/isaac/tests/samples" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/urdf", ext.target_dir.."/omni/isaac/tests/urdf" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/step_importer", ext.target_dir.."/omni/isaac/tests/step_importer" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/lidar", ext.target_dir.."/omni/isaac/tests/lidar" },
--     { "%{root}/source/extensions/omni.isaac.tests/python/domain_randomizer", ext.target_dir.."/omni/isaac/tests/domain_randomizer" },
-- }

-- repo_build.prebuild_copy {
--     { "%{root}/source/extensions/omni.isaac.tests/python/*.py", ext.target_dir.."/omni/isaac/tests" },
--     { "%{root}/source/extensions/omni.isaac.tests/data/**", ext.target_dir.."/omni/isaac/tests/data" },
-- }
