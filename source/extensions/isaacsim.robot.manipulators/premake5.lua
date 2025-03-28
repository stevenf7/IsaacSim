local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/robot/manipulators")

project_ext(ext)

add_ogn_dependencies(ogn, { "python/nodes" })

project_ext_ogn(ext, ogn)

-- Add the standard dependencies all OGN projects have
repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}

repo_build.prebuild_link {
    { "docs", ext.target_dir .. "/docs" },
    { "data", ext.target_dir .. "/data" },
    { "python/controllers", ogn.python_target_path .. "/controllers" },
    { "python/nodes", ogn.python_target_path .. "/nodes" },
    { "python/manipulators", ogn.python_target_path .. "/manipulators" },
    { "python/grippers", ogn.python_target_path .. "/grippers" },
    { "python/impl", ogn.python_target_path .. "/impl" },
    { "python/tests", ogn.python_tests_target_path },
}
