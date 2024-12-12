local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "isaacsim/replicator/writers")

project_ext_ogn( ext, ogn )
project_ext( ext, { generate_ext_project=true })

    -- All Python script and documentation files are part of this project
    add_files("python", "*.py")
    add_files("python/nodes", "python/nodes/**.py")
    add_files("python/impl", "python/impl/**.py")
    add_files("python/tests", "python/tests/**.py")
    add_files("python/scripts", "python/scripts/**.py")

    -- Add the standard dependencies all OGN projects have
    add_ogn_dependencies(ogn, {"python/nodes"})

    -- Copy the init script directly into the build tree to avoid reload conflicts.
    repo_build.prebuild_copy {
        { "python/__init__.py", ogn.python_target_path },
    }
    -- Linking directories allows them to hot reload when files are modified in the source tree
    -- Docs are linked to get the README into the extension window
    repo_build.prebuild_link {
        { "docs", ext.target_dir.."/docs" },
        { "data", ext.target_dir.."/data" },
        { "python/tests", ogn.python_tests_target_path },
        { "python/impl", ogn.python_target_path.."/impl" },
        { "python/scripts", ogn.python_target_path.."/scripts" },
    }

