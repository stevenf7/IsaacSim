local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "omni", ext.target_dir.."/omni" },
}
