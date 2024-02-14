-- Use folder name to build extension name and tag. 
local ext = get_current_extension_info()

project_ext (ext, { 
    define_test = false
})

-- Link only those files and folders into the extension target directory
repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
}