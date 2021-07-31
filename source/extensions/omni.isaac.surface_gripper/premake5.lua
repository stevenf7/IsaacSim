local ext = get_current_extension_info()
project_ext (ext)

-- -- C++ Carbonite plugin
-- project_ext_plugin(ext, "omni.isaac.surface_gripper.plugin")
--     removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }

--     add_files("impl", "plugins")
--     add_files("iface", "%{root}/include/omni/isaac/surface_gripper/**")

--     includedirs {
--         "%{root}/source/pch",
--         "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
--         "%{root}/_build/target-deps/rtx_plugins/include",
--     }
--     libdirs {   
--         "%{root}/_build/target-deps/python/libs", 
--         "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
--         "%{root}/_build/target-deps/nv_usd/release/lib",
--         "%{kit_sdk_bin_dir}/plugins",

--     }

--     if os.target() == "linux" then
--         includedirs {
--             "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
--             "%{root}/_build/target-deps/python/include/python3.7m",
--         }
--     else
--         libdirs {
--             "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
--         }
--     end

--     links { 
--         "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", "omni.usd"
--     }


-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.surface_gripper.python",
    module = "_surface_gripper",
    src = "bindings",
    target_subdir = "omni/isaac/surface_gripper"})
    
    includedirs {
        "%{root}/source/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/client_library/include",
    }

    libdirs {   
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils"}

    filter { "system:linux", "platforms:x86_64" }
        links {"tbb", "boost_python37" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}



repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/surface_gripper/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/surface_gripper/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/surface_gripper" },
}
