local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path .. "/" .. ext.id
project_ext(ext)

repo_build.prebuild_copy {
    { "python/__init__.py", ext.target_dir .. "/omni/isaac/core_nodes" },
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir .. "/omni/isaac/core_nodes/scripts" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "python/impl", ext.target_dir .. "/omni/isaac/core_nodes/impl" },
}
