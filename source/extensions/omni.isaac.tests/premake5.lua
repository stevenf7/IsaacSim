local ext = get_current_extension_info()
project_ext (ext)


if os.target() == "linux" then
    repo_build.prebuild_link {
        { "config/linux", ext.target_dir.."/config" },
    }
else
    repo_build.prebuild_link {
        { "config/windows", ext.target_dir.."/config" },
    }
end

-- no data exists currently, need to add back once we have multi-extension unit tests here. 
-- repo_build.prebuild_link {
--     { "data", ext.target_dir.."/data" },
-- }

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/tests" },
}
