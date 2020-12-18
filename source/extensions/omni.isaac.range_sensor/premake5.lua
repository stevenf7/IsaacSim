local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.range_sensor.plugin")

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/range_sensor/**")

    include_physx()

    includedirs {
        "%{root}/source/pch",
        "%{root}/source/extensions/omni.isaac.utils", 
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/client_library/include",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "rangeSensorSchema", "omni.usd", "usdPhysics",
    }

    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.6m"
        }
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

project "test.unit"
    kind "ConsoleApp"
    dependson { "prebuild" }
    includedirs {
            "include",
            ".",
            "%{root}/_build/target-deps/nv_usd/debug/include",
            "%{root}/_build/target-deps/rtx_plugins/include",
        }

    libdirs { "%{root}/_build/target-deps/nv_usd/debug/lib",
              "%{root}/_build/target-deps/carb_sdk_plugins/_build/linux-x86_64/debug"}
    links {"carb"}
    --"omni.ui"}

    runpathdirs { "%{root}/_build/target-deps/nv_usd/debug/lib",
	          "%{root}/_build/target-deps/carb_sdk_plugins/_build/linux-x86_64/debug" }
    filter { "system:linux" }
            buildoptions { "-pthread" }
            links { "pthread" }
            rtti "On"
            includedirs { "%{target_deps}/python/include/python3.6m" }

    filter { "system:linux", "platforms:x86_64" }
            exceptionhandling "On"
            includedirs { "%{target_deps}/nv_usd/%{config}/include/boost" }
            libdirs { "%{target_deps}/cuda/lib64" }
            links { "boost_python36", "python3.6m", "cudart_static", "sdf", "tf", "usd", "usdUtils" }
            removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
            disablewarnings { "error=switch", "error=unused-function", "error=sign-compare" }

    files {
     	   "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/TestUSS.cpp",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/USSEnvelope.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicEmitter.h"}
    filter { "configurations:debug" }
      defines { "_DEBUG" }

   filter { "configurations:release" }
      defines { "_NDEBUG" }


-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.range_sensor.python",
    module = "_range_sensor",
    src = "bindings",
    target_subdir = "omni/isaac/range_sensor"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/range_sensor/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/range_sensor/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/range_sensor" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/python/RangeSensorSchema/**", ext.target_dir.."/omni/isaac/RangeSensorSchema" },
    { "%{root}/_build/target-deps/usd_ext_isaac/$config/lib/${lib_prefix}rangeSensorSchema${lib_ext}", ext.target_dir.."/bin"},
}
