local ext = get_current_extension_info()
local ogn = get_ogn_project_information(ext, "omni/isaac/sensor")
local targetDepsDir = "%{root}/_build/target-deps"
local hostDepsDir = "%{root}/_build/host-deps"

project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.sensor.plugin")
    cppdialect "C++17"
    
    dependson { "prebuild", "carb.physics-usd.plugin", "omni.physx.plugin", "omni.isaac.debug_draw.primitive_drawing"}
    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/sensor/**")
    add_files("ogn", ogn.nodes_path)

    add_ogn_dependencies(ogn, {"python/nodes"})

    include_physx()
    add_cuda_dependencies()

    includedirs {
        "%{root}/include/pch",
        targetDepsDir.."/physx/include",
        targetDepsDir.."/pxshared/include",
        targetDepsDir.."/nv_usd/%{cfg.buildcfg}/include",
        targetDepsDir.."/usd_ext_physics/%{cfg.buildcfg}/include",
        targetDepsDir.."/omni_physics/include",
        targetDepsDir.."/rtx_plugins/include",
        targetDepsDir.."/client_library/include",
        targetDepsDir.."/nvsensor/include/sensors",
        targetDepsDir.."/nvsensor/include",
        "%{kit_sdk_bin_dir}/extscore/usdrt.scenegraph/include",
        "%{root}/schemas/_install/isaacSensorSchema/%{platform}_%{config}/include",
        "%{root}/_build/target-deps/omni_client_library/include",
        "%{root}/_build/target-deps/python/include",
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

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/sensor/scripts" },
    { "python/tests", ext.target_dir.."/omni/isaac/sensor/tests" },
    { "data", ext.target_dir.."/data" },
    { "docs", ext.target_dir.."/docs" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/sensor" },
}
if os.target() == "linux" then
    repo_build.prebuild_copy {
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.beams/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.common/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.ids/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.lidar/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.lidar_tools/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.materials/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.material_tools/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.radar/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.samples/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.ultrasonic/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.wpm/bin/*", ext.target_dir.."/bin" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.lidar/data/*.json", "%{root}/_build/%{platform}/%{config}/exts/omni.sensors.nv.lidar/data/" },
        {"%{root}/_build/target-deps/nvsensor/%{platform}/omni.sensors.nv.radar/data/dmat_approx/*.json", "%{root}/_build/%{platform}/%{config}/exts/omni.sensors.nv.radar/data/dmat_approx/" },
    }
    repo_build.prebuild_copy {
        {"%{root}/_build/target-deps/nvsensor/data/material_files/","%{root}/_build/%{platform}/%{config}/data/material_files" },
    }
end