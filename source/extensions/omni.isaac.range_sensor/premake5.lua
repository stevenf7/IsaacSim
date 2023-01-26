local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/range_sensor")
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.range_sensor.plugin")
    dependson {"omni.isaac.debug_draw.primitive_drawing"}
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/range_sensor/**")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn)

    include_physx()

    includedirs {
        "%{root}/include/pch",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/gsl/include",
        "%{root}/_build/target-deps/physx/include",
        "%{root}/_build/target-deps/pxshared/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/include",
        "%{root}/_build/target-deps/usd_schema_semantics/%{cfg.buildcfg}/include",
        "%{kit_sdk_bin_dir}/extscore/omni.syntheticdata/include",
        "%{root}/_build/kit_%{config}/_exts/omni.syntheticdata/include",
        "%{root}/_build/target-deps/omni_client_library/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/schemas/_install/rangeSensorSchema/%{platform}_%{config}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin"
    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "rangeSensorSchema", "omni.usd", "usdPhysics",  "omni.isaac.debug_draw.primitive_drawing"
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

project "tests-unit-omni.isaac.range_sensor"
    kind "ConsoleApp"
    dependson { "prebuild" }
    targetdir ("%{root}/_build/%{platform}/%{config}/tests")
    includedirs {
            "%{root}/source/extensions/omni.isaac.range_sensor",
            "%{root}/_build/target-deps/physx/include",
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
            "%{root}/_build/target-deps/rtx_plugins/include",
            "%{root}/_build/target-deps/doctest",
        }

    libdirs { "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
              "%{root}/_build/target-deps/carb_sdk_plugins/_build/linux-x86_64/%{cfg.buildcfg}"}
    links {"carb"}

    runpathdirs {
                "%{root}/_build/%{platform}/%{config}/kit/plugins",
                "%{root}/_build/%{platform}/%{config}/kit/extscore/omni.usd.libs/bin/" 
            }
    filter { "system:linux" }
            buildoptions { "-pthread" }
            links { "pthread" }
            includedirs { "%{target_deps}/python/include/python3.7m",
                          "%{target_deps}/nv_usd/%{config}/include/boost" }
            links { "boost_python37", "python3.7m", "sdf", "tf", "usd", "usdUtils" }

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

project_ext_ogn( ext, ogn )

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
}
