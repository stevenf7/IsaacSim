local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/benchmark_environments/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/benchmark_environments/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/benchmark_environments" },
}
