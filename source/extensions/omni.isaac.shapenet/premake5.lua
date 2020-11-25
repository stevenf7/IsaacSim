local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/shapenet/scripts" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/shapenet" },
}
