local ext = get_current_extension_info()
ext.target_dir = deprecated_exts_path .. "/" .. ext.id

project_ext(ext)

repo_build.prebuild_link {
    { "config", ext.target_dir .. "/config" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
}
-- Don't copy files as the renamed extension provides the same module
-- repo_build.prebuild_copy
-- {
--     { "python/__init__.py", ext.target_dir.."/usd/schema/isaac" },
-- }
