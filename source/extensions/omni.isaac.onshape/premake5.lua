local ext = get_current_extension_info()
local targetDepsDir = "%{root}/_build/target-deps"
project_ext (ext)
    
repo_build.prebuild_link {
    { "config", ext.target_dir.."/config" },
}

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "icons", ext.target_dir.."/icons" },
    
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/onshape" },
}
