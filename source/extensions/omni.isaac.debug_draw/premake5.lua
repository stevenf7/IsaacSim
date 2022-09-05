local ext = get_current_extension_info()
project_ext (ext)


project_with_location("omni.isaac.debug_draw.primitive_drawing")
    targetdir ("%{root}/_build/intermediate/%{platform}/%{prj.name}")
    kind "StaticLib"
    language "C++"

    pic "On"
    staticruntime "Off"
    add_files("impl", "library")
    add_files("iface", "%{root}/include/omni/isaac/debug_draw/**")
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
    }
    libdirs {
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
    }
    links{"sdf", "omni.usd"}

    filter { "system:linux" }
        disablewarnings {"error=pragmas"}
        includedirs {
            "%{root}/_build/target-deps/python/include/python3.7m"
        }
        buildoptions("-fvisibility=default")
    filter { "system:windows" }
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14"
        }
    filter {}

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.debug_draw.plugin")
    dependson {"omni.isaac.debug_draw.primitive_drawing"}
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/debug_draw/**")

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
    }
    libdirs {   
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",

    }

    if os.target() == "linux" then
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.7m",
        }
    else
        libdirs {
            "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
        }
    end

    links { 
        "gf", "tf", "sdf", "vt","usd", "usdGeom", "usdUtils", "usdShade", "usdImaging", "omni.usd", "omni.isaac.debug_draw.primitive_drawing"
    }


-- Python Bindings for Carobnite Plugin
project_ext_bindings ({
    ext = ext,
    project_name = "omni.isaac.debug_draw.python",
    module = "_debug_draw",
    src = "bindings",
    target_subdir = "omni/isaac/debug_draw"})
    
    dependson {"omni.isaac.debug_draw.primitive_drawing"}
    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/carb_gfx_plugins/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
    }

    libdirs {   
        "%{root}/_build/target-deps/python/libs", 
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/nv_usd/release/lib"
    }
    links {"arch", "gf", "sdf", "tf", "vt", "pcp", "usd", "usdGeom", "usdUtils", "omni.isaac.debug_draw.primitive_drawing"}

    filter { "system:linux", "platforms:x86_64" }
        links {"tbb", "boost_python37" }
    filter {}

    filter { "configurations:debug" }
        defines { "_DEBUG" }
    filter { "configurations:release" }
        defines { "NDEBUG" }
    filter {}



repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/debug_draw/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/debug_draw/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/debug_draw" },
}
