local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/range_sensor")
project_ext (ext)

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
}