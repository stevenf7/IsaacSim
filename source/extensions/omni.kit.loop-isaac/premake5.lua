local ext = get_current_extension_info()

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.kit.loop-isaac.plugin")
    add_files("impl", "plugins/omni.kit.loop")
    add_files("iface", "%{root}/include/omni/kit/**")

    includedirs {
        "%{root}/source/extensions/omni.kit.loop-isaac/include",
    }

    -- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.kit.loop-isaac.python",
    module = "_loop",
    src = "bindings",
    target_subdir = "omni/kit/loop"
}

includedirs {
    "%{root}/source/extensions/omni.kit.loop-isaac/include",
}

repo_build.prebuild_link {
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}
repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/kit/loop" },
}
