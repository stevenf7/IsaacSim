
local ext = get_current_extension_info()
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "isaacsim", ext.target_dir.."/isaacsim" },
    { "$root/_build/target-deps/isaac_usd_to_urdf_prebundle", ext.target_dir.."/pip_prebundle" },
}
