
local ext = get_current_extension_info()

local ogn = get_ogn_project_information(ext, "omni/isaac/kaya")

project_ext (ext)

project_ext_plugin(ext, "omni.isaac.kaya.plugin")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn)

project_ext_ogn( ext, ogn )

project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.kaya",
    module = "_kaya",
    src = "bindings",
    target_subdir = "omni/isaac/kaya"
}

    add_ogn_dependencies(ogn,"omni/isaac/kaya/nodes")

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "omni", ext.target_dir.."/omni" },
}
