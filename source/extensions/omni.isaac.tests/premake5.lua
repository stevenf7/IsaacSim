local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
{ "python/tests", ext.target_dir.."/omni/isaac/tests/tests" },
{ "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/tests" },
}
