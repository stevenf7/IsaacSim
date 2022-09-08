local ext = get_current_extension_info()
project_ext (ext)


-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.motion_planning.plugin")
    cppdialect "C++17"

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/motion_planning/**")

    include_physx()

    includedirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/lula/include",
        "%{root}/_build/target-deps/python/include/python3.7m",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_client_library/include",

    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/lula/lib64"
    }

    links {
        "gf", "sdf", "tf", "usd", "usdGeom", "usdUtils",
        "lula_fabrics", "lula_kinematics", "lula_math" , "lula_rmpflow", "lula_util", "lula_world",
        "console_bridge", "urdfdom_model", "yaml-cpp"
    }

    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
        defines {
            "_ENABLE_EXTENDED_ALIGNED_STORAGE", -- Silence warnings about a behavior change in recent versions of MSVC affecting alignment
                                                --     of structs containing certain Eigen types.
            "_SILENCE_CXX17_ADAPTOR_TYPEDEFS_DEPRECATION_WARNING" -- Silence warnings triggered by eigen/src/core/util/meta.h
        }
        disablewarnings {
            "4251", -- Suppress warnings from yaml-cpp headers ("needs to have dll-interface to be used by clients of class ...")
            "4275", -- Suppress warnings from yaml-cpp headers ("non dll-interface class 'std::runtime_error' used as base for
                    --     dll-interface class 'YAML::Exception' ...")
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- Python Bindings for Carobnite Plugin
project_ext_bindings (  {ext = ext,
                        project_name = "omni.isaac.motion_planning.python",
                        module = "_motion_planning",
                        src = "bindings",
                        target_subdir = "omni/isaac/motion_planning"})

    includedirs {"%{root}/_build/target-deps/lula/include"}
    cppdialect "C++17"


repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/motion_planning/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/motion_planning/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "resources", ext.target_dir.."/resources" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/motion_planning" },
    { "%{root}/_build/target-deps/lula/lib64/**", ext.target_dir.."/bin" },
}
