local ext = get_current_extension_info()

project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
    { "$root/_build/target-deps/pip_cloud_prebundle", ext.target_dir.."/pip_prebundle" },
    -- { "$root/_build/target-deps/pip_archive", ext.target_dir.."/pip_archive" },
}
if os.target() == "windows" then
    local currentAbsPath = repo_build.get_abs_path(".");
    repo_build.copy_to_dir (currentAbsPath.."/pywin32/*.py", ext.target_dir.."/pip_prebundle/pywin32_system32")
end