local ext = get_current_extension_info()
project_ext (ext, { 
    define_test = false
})

repo_build.prebuild_link {
    { "python", ext.target_dir.."/omni/isaac/internal_tools" },
}