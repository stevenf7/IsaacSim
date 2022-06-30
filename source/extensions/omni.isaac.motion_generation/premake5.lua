local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
    { "motion_policy_configs", ext.target_dir.."/motion_policy_configs"},
    { "path_planner_configs", ext.target_dir.."/path_planner_configs"},
}
