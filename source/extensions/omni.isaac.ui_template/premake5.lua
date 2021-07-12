local ext = get_current_extension_info()
project_ext (ext)    

repo_build.prebuild_link {
    { "config", ext.target_dir.."/config" },
    { "python/scripts", ext.target_dir.."/omni/isaac/ui_template/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/ui_template/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/ui_template" },
}