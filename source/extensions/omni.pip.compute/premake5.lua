local ext = get_current_extension_info()

project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
    { "$root/_build/target-deps/pip_compute_prebundle", ext.target_dir.."/pip_prebundle" },
    -- { "$root/_build/target-deps/pip_archive", ext.target_dir.."/pip_archive" },
}