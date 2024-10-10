-- Setup the basic extension variables
local ext = get_current_extension_info()
-- Set up the basic shared project information
project_ext (ext)

-- -------------------------------------
-- Build the C++ plugin that will be loaded by the extension
project_ext_plugin(ext, "isaacsim.xr.openxr.plugin")
    add_files("include", "include/isaacsim/xr/openxr")
    add_files("source", "plugins/isaacsim.xr.openxr")
    includedirs {
        "include",
        "plugins/isaacsim.xr.openxr",
    }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- -------------------------------------
-- Build Python bindings that will be loaded by the extension
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.xr.openxr.python",
    module = "_openxr",
    src = "bindings/isaacsim.xr.openxr",
    target_subdir = "isaacsim/xr/openxr"
}
    dependson { "isaacsim.xr.openxr.plugin" }
    links { "isaacsim.xr.openxr.plugin" }
    includedirs { 
        "include",
    }

-- -------------------------------------
-- Link/copy folders and files to be packaged with the extension
repo_build.prebuild_link {
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "python/impl", ext.target_dir.."/isaacsim/xr/openxr/impl" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/isaacsim/xr/openxr" },
}
