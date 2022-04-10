local ext = get_current_extension_info()


local ogn = get_ogn_project_information(ext, "omni/isaac/conveyor")

project_ext_ogn( ext, ogn )


project_ext (ext, { generate_ext_project=true })

    add_files("python", "*.py")
    add_files("python/nodes", "python/nodes/**.py")
    add_files("python/scripts", "python/scripts/**.py")
    add_files("python/tests", "python/tests/**.py")

    add_ogn_dependencies(ogn, {"python/nodes"})

    repo_build.prebuild_link {
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "python/scripts", ogn.python_target_path.."/scripts" },    
        { "python/tests", ogn.python_target_path.."/tests" },    
    }

    repo_build.prebuild_copy {
        { "python/__init__.py", ogn.python_target_path },
    }