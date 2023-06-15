local ext = get_current_extension_info()

local ogn = get_ogn_project_information(ext, "omni/isaac/wheeled_robots")

project_ext_ogn (ext, ogn)
project_ext( ext, { generate_ext_project=true })

    add_files("omni/isaac/wheeled_robots", "*.py")
    add_files("omni/isaac/wheeled_robots/nodes", "python/nodes/**.py")
    add_files("omni/isaac/wheeled_robots/robots", "python/robots/**.py")
    add_files("omni/isaac/wheeled_robots/controllers", "python/controllers/**.py")
    add_files("omni/isaac/wheeled_robots/tests", "python/tests/**.py")
    
    add_ogn_dependencies(ogn, {"omni/isaac/wheeled_robots/nodes"})

    repo_build.prebuild_copy {
        { "omni/isaac/wheeled_robots/__init__.py", ogn.python_target_path },
    }

    repo_build.prebuild_link {
        { "omni/isaac/wheeled_robots/controllers", ogn.python_target_path.."/controllers" },
        { "omni/isaac/wheeled_robots/robots", ogn.python_target_path.."/robots" },
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "omni/isaac/wheeled_robots/tests", ogn.python_tests_target_path },
    }


