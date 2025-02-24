local ext = get_current_extension_info()
project_ext(ext)

repo_build.prebuild_link {
    { "icons", ext.target_dir .. "/icons" },
    { "docs", ext.target_dir .. "/docs" },
    { "isaacsim", ext.target_dir .. "/isaacsim" },
}
