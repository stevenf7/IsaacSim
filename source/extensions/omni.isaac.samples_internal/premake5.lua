local ext = get_current_extension_info()
project_ext (ext)

    
-- if os.target() == "linux" then
--     repo_build.prebuild_link {
--         { ext_source.."/config/linux", ext_folder.."/config" },
--     }
-- else
--     repo_build.prebuild_link {
--         { ext_source.."/config/windows", ext_folder.."/config" },
--     }
-- end

--     repo_build.prebuild_link {
--         { ext_source.."/python/scripts", ext_folder.."/omni/isaac/samples_internal/scripts" },
--     }

--     repo_build.prebuild_copy {
--         { ext_source.."/python/*.py", ext_folder.."/omni/isaac/samples_internal" },
--     }