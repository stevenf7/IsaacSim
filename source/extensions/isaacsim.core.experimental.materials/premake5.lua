-- Setup the basic extension variables
local ext = get_current_extension_info()
-- Set up the basic shared project information
project_ext (ext)

-- -------------------------------------
-- Link/copy folders and files to be packaged with the extension
repo_build.prebuild_link {
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "python/impl", ext.target_dir.."/isaacsim/core/experimental/materials/impl" },
    { "python/tests", ext.target_dir.."/isaacsim/core/experimental/materials/tests" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/isaacsim/core/experimental/materials" },
}
