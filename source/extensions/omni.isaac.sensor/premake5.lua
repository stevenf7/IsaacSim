local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/sensor")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.sensor.plugin")
    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin", "omni.isaac.debug_draw.primitive_drawing"}
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/sensor/**")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"nodes"})


    include_physx()

    includedirs {
        "%{root}/include/pch",
        targetDepsDir.."/physx/include",
        targetDepsDir.."/pxshared/include",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/include",
        targetDepsDir.."/omni_physics/include",
        targetDepsDir.."/rtx_plugins/include",
        targetDepsDir.."/client_library/include",
        targetDepsDir.."/nvlidar/include",
        "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/include",
        "%{root}/_build/target-deps/omni_client_library/include",
     }
    libdirs {
        "%{root}/_build/target-deps/python/libs",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/lib",
        "%{kit_sdk_bin_dir}/plugins",
        "%{kit_sdk_bin_dir}/extscore/omni.usd.core/bin"
    }

    links {"carb", "gf", "tf", "sdf", "usd", "usdGeom","usdUtils", "physxSchema","usdPhysics", "physicsSchemaTools", "omni.usd", "isaacSensorSchema",  "omni.isaac.debug_draw.primitive_drawing", "arch"}

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


project_ext_ogn( ext, ogn )

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.sensor.python",
    module = "_sensor",
    src = "bindings",
    target_subdir = "omni/isaac/sensor"
}
    add_ogn_dependencies(ogn)

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/sensor/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/sensor/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
    { "python/impl", ogn.python_target_path.."/impl" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/sensor" },
}
if os.target() == "linux" then
    repo_build.prebuild_copy {
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.materials/bin/libmaterial_profile_reader.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.materials/bin/libmaterials.default_material.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.materials/bin/libmaterials.core_material.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.materials/bin/libmaterials.retro_reflective_material.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.common/bin/libatmos_cfg_provider.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.lidar/bin/liblidar_profile_reader.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.lidar/bin/librtxmodel_lidar_core.plugin.so", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvlidar/%{platform}/omni.drivesim.sensors.nv.lidar/data/*.json", "%{root}/_build/%{platform}/%{config}/exts/omni.drivesim.sensors.nv.lidar/data/" },
    }
    repo_build.prebuild_copy {
        {"%{root}/_build/target-deps/nvlidar/material_files/","%{root}/_build/%{platform}/%{config}/data/material_files" },
    }
end