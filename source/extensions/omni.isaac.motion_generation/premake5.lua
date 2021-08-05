local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/motion_generation/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/motion_generation/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "policy_configs", ext.target_dir.."/policy_configs"},
    { "%{root}/_build/target-deps/lula/data", ext.target_dir.."/linked_resources/lula/" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/motion_generation" },
}
