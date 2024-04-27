local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/range_sensor")
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.range_sensor.plugin")
    dependson {"omni.isaac.debug_draw.primitive_drawing"}
    add_files("impl", "plugins")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn)

    include_physx()
    includedirs {
        "%{root}/source/extensions/omni.isaac.common_includes/include",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/gsl/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/omni_physics/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/include",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/include",
        "%{root}/_build/target-deps/usd_schema_semantics/%{cfg.buildcfg}/include",
        "%{kit_sdk_bin_dir}/exts/omni.syntheticdata/include",
        "%{kit_sdk_bin_dir}/exts/usdrt.scenegraph/include",
        "%{kit_sdk_bin_dir}/dev/fabric/include/",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/python/include",
        "%{root}/source/extensions/omni.isaac.range_sensor/include",
        "%{root}/source/extensions/omni.isaac.dynamic_control/include",
        "%{root}/source/extensions/omni.isaac.debug_draw/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/IsaacSensorSchema/lib",
        "%{root}/_build/target-deps/omni-isaacsim-schema/%{platform}/%{config}/RangeSensorSchema/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/exts/omni.usd.core/bin",
    }

    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "rangeSensorSchema", "omni.usd", "usdPhysics",  "omni.isaac.debug_draw.primitive_drawing"
    }

    filter { "system:linux" }
        includedirs {
            "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
            "%{root}/_build/target-deps/python/include/python3.10"
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

project_ext_ogn( ext, ogn )

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.range_sensor.python",
    module = "_range_sensor",
    src = "bindings",
    target_subdir = "omni/isaac/range_sensor"
}

includedirs {
    "%{root}/source/extensions/omni.isaac.range_sensor/include",
}

repo_build.prebuild_link {
    { "python/impl", ext.target_dir.."/omni/isaac/range_sensor/impl" },
    { "python/tests", ext.target_dir.."/omni/isaac/range_sensor/tests" },
    { "python/commands", ext.target_dir.."/omni/isaac/range_sensor/commands" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "include", ext.target_dir.."/include" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/range_sensor" },
}
