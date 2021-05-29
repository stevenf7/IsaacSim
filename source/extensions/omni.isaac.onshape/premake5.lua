local ext = get_current_extension_info()
project_ext (ext)
    
repo_build.prebuild_link {
    { "config", ext.target_dir.."/config" },
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/onshape/scripts" },
    { "python/widgets", ext.target_dir.."/omni/isaac/onshape/widgets" },
    { "python/tests", ext.target_dir.."/omni/isaac/onshape/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "icons", ext.target_dir.."/icons" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/onshape" },
}
