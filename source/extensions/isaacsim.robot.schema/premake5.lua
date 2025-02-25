local ext = get_current_extension_info()
project_ext(ext)

repo_build.prebuild_link {
    { "config", ext.target_dir .. "/config" },
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "include", ext.target_dir .. "/include" },
    { "robot_schema", ext.target_dir .. "/usd/schema/isaac/robot_schema" },
}
repo_build.prebuild_copy {
    { "python/__init__.py", ext.target_dir .. "/usd/schema/isaac" },
}

repo_build.prebuild_copy {
    { "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}", ext.target_dir .. "/plugins" },
}
