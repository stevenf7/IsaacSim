local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/robot_benchmark/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/robot_benchmark/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "benchmark_config", ext.target_dir.."/benchmark_config" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/robot_benchmark" },
}
