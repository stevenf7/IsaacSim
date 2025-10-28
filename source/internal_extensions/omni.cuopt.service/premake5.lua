local ext = get_current_extension_info()
ext.target_dir = isaac_sim_extra_extsbuild_dir .. "/" .. ext.id

project_ext(ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "omni", ext.target_dir .. "/omni" },
}
