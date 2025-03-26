local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path .. "/" .. ext.id
project_ext(ext)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir .. "/omni/isaac/utils/scripts" },
    { "python/tests", ext.target_dir .. "/omni/isaac/utils/tests" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/omni/isaac/utils" },
}
