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
            "%{root}/_build/target-deps/python/include/python3.7m"
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

project "test.unit.range_sensor"
    kind "ConsoleApp"
    dependson { "prebuild" }
    
    includedirs {
            "%{root}/source/extensions/omni.isaac.range_sensor",
            "%{root}/_build/target-deps/physx/include",
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/rtx_plugins/include",
        }

    libdirs { "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
              "%{root}/_build/target-deps/carb_sdk_plugins/_build/linux-x86_64/%{cfg.buildcfg}"}
    links {"carb"}

    runpathdirs { "%{root}/_build/kit_release/_build/linux-x86_64/release/plugins/" }
    filter { "system:linux" }
            buildoptions { "-pthread" }
            links { "pthread" }
            includedirs { "%{target_deps}/python/include/python3.7m",
                          "%{target_deps}/nv_usd/%{config}/include/boost" }
            libdirs { "%{target_deps}/cuda/lib64" }
            links { "boost_python37", "python3.7m", "cudart_static", "sdf", "tf", "usd", "usdUtils" }

    files {
     	   "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/TestUSS.cpp",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicReceiver.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicReceiver.cpp",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicReceiverArray.cpp",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicReceiverArray.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/USSEnvelope.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/FiringModeUtils.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/UltrasonicEmitter.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/BRDF.h",
           "%{root}/source/extensions/omni.isaac.range_sensor/plugins/ultrasonic/BRDF.cpp"}
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
