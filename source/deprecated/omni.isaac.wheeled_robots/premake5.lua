local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path.."/"..ext.id

project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "python/controllers", ext.target_dir.."/omni/isaac/wheeled_robots/controllers" },
    { "python/robots", ext.target_dir.."/omni/isaac/wheeled_robots/robots" },
}
