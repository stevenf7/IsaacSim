local ext = get_current_extension_info()
project_ext (ext)

-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
                        ext = ext,
                        project_name = "isaacsim.core.utils.python",
                        module = "_isaac_utils",
                        src = "bindings",
                        target_subdir = "isaacsim/core/utils"
                    })
    staticruntime "Off"
    add_files("impl", "plugins")
    add_files("iface", "include")
    defines { "OMPRIMUTILSEXPORT" }

    include_physx()
    includedirs {
        "%{root}/source/extensions/isaacsim.core.includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        extsbuild_dir.."/usdrt.scenegraph/include",
        "%{root}/source/deprecated/omni.isaac.dynamic_control/include",
        "%{root}/source/extensions/isaacsim.core.utils/include",
        "%{root}/source/extensions/isaacsim.core.utils/plugins",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils", "usdPhysics"}

    filter { "system:linux", "platforms:x86_64" }
    links {"tbb", "boost_python310" }
    filter {}

    filter { "system:windows", "platforms:x86_64" }
        link_boost_for_windows({"boost_python310"})
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}


repo_build.prebuild_link {
    { "python/scripts/numpy", ext.target_dir.."/isaacsim/core/utils/numpy" },
    { "python/scripts/torch", ext.target_dir.."/isaacsim/core/utils/torch" },
    { "python/scripts/warp", ext.target_dir.."/isaacsim/core/utils/warp" },
    { "python/tests", ext.target_dir.."/isaacsim/core/utils/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/isaacsim/core/utils" },
    { "python/scripts/*.py", ext.target_dir.."/isaacsim/core/utils" },
}
