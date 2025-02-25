local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path .. "/" .. ext.id

project_ext(ext, {
    define_test = false,
})

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
}
