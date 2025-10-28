local ext = get_current_extension_info()
ext.target_dir = isaac_sim_extra_extsbuild_dir .. "/" .. ext.id
ext.bin_dir = ext.target_dir .. "/bin"
project_ext(ext)

-- build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "isaacsim.app.compatibility_check.plugin")
    targetdir(ext.bin_dir)
    rtti "On"

    add_files("include", "include")
    add_files("source", "plugins")
    includedirs {
        "include",
        "plugins",
        "%{root}/_build/target-deps/rtx_plugins/include",
    }

-- build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.app.compatibility_check.python",
    module = "_compatibility_check",
    src = "bindings",
    target_subdir = "isaacsim/app/compatibility_check"
}
    includedirs {
        "include",
        "%{root}/_build/target-deps/rtx_plugins/include",
    }

-- link/copy folders and files that should be packaged with the extension
repo_build.prebuild_link {
    { "python/impl", ext.target_dir .. "/isaacsim/app/compatibility_check/impl" },
    { "python/tests", ext.target_dir .. "/isaacsim/app/compatibility_check/tests" },
    { "data", ext.target_dir .. "/data" },
    { "docs", ext.target_dir .. "/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir .. "/isaacsim/app/compatibility_check" },
}
