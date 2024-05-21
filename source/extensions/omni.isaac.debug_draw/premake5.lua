local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/debug_draw")
project_ext (ext)


project_with_location("omni.isaac.debug_draw.primitive_drawing")
    targetdir (ext.bin_dir)
    kind "StaticLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "library")
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/%{config}/include",
        "%{root}/source/extensions/omni.isaac.debug_draw/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }
    links{"sdf", "omni.usd"}

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.10"
        }
        buildoptions("-fvisibility=default")
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.debug_draw.plugin")
    cppdialect "C++17"
    dependson {"omni.isaac.debug_draw.primitive_drawing", "omni.physx.plugin"}
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }

    add_files("impl", "plugins")
    add_files("ogn", ogn.nodes_path)

    include_physx()
    -- Add the standard dependencies all OGN projects have
    add_ogn_dependencies(ogn)
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{root}/_build/target-deps/python/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
        "%{root}/source/extensions/omni.isaac.debug_draw/include",
    }
    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin"
    }

    if os.target() == "linux" then
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.10",
        }
    else
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
        }
    end

    links { 
        "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", "omni.usd", "omni.isaac.debug_draw.primitive_drawing"
    }

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}

-- ----------------------------------------------------------------------
-- Breaking this out as a separate project ensures the .ogn files are processed before their results are needed
project_ext_ogn( ext, ogn )

-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.debug_draw.python",
    module = "_debug_draw",
    src = "bindings",
    target_subdir = "omni/isaac/debug_draw"})
    
    -- Add the standard dependencies all OGN projects have, and link directories with Python nodes
    dependson {"omni.isaac.debug_draw.primitive_drawing"}
    --add_files("bindings", "bindings")
    --add_files("python", "python/*.py")
    --add_files("python/tests", "python/tests/*.py")
    include_physx()
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/source/extensions/omni.isaac.debug_draw/include",
    }

    libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils", "omni.isaac.debug_draw.primitive_drawing"}

    filter { "system:linux", "platforms:x86_64" }        
        links {"tbb", "boost_python310" }
    filter {}

    filter { "system:windows", "platforms:x86_64" }
        link_boost_for_windows({"boost_python310"})

    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}



repo_build.prebuild_link {
    { "python/scripts", ogn.python_target_path.."/scripts" },
    { "python/tests", ogn.python_tests_target_path },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/__init__.py", ogn.python_target_path },
}
