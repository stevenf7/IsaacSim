local ext = get_current_extension_info()

local ogn = get_ogn_project_information(ext, "omni/isaac/examples_nodes")

project_ext (ext, ogn)
project_ext( ext, { generate_ext_project=true })

    add_files("omni/isaac/examples_nodes", "*.py")
    add_files("omni/isaac/examples_nodes/nodes", "python/nodes/**.py")
    add_files("omni/isaac/examples_nodes/tests", "python/tests/**.py")
    
    add_ogn_dependencies(ogn, {"omni/isaac/examples_nodes/nodes"})

    repo_build.prebuild_copy {
        { "omni/isaac/examples_nodes/__init__.py", ogn.python_target_path },
    }

    repo_build.prebuild_link {
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "omni/isaac/examples_nodes/tests", ogn.python_tests_target_path },
    }


