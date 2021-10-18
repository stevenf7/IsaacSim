local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
    { "policy_configs", ext.target_dir.."/policy_configs"},
    { "%{root}/_build/target-deps/lula/data", ext.target_dir.."/linked_resources/lula/" }
}
