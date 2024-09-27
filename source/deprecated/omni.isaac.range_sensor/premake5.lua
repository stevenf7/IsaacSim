local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path.."/"..ext.id

project_ext (ext)

repo_build.prebuild_link {
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "omni", ext.target_dir.."/omni" },
}
