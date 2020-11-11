local ext = get_current_extension_info()
project_ext (ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.occupancy_map.plugin")
    staticruntime "Off"
    rtti "On"
    exceptionhandling "On"
    disablewarnings {"error=pragmas"}

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/occupancy_map/**")
    filter { "system:windows", "platforms:x86_64", "configurations:debug" }
    libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/debug", 
            "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/debug" 
        }
        defines {  "PX_PHYSX_STATIC_LIB", "_DEBUG" }
    filter { "system:windows", "platforms:x86_64", "configurations:release" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/release" 
        }
        defines {  "PX_PHYSX_STATIC_LIB", "NDEBUG" }
    filter { "system:windows", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        links { "nvToolsExt64_1","PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"}
    filter {}

    filter { "system:windows", "platforms:x86_64", "configurations:debug" }
    libdirs { 
        "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/debug", 
        "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/debug" 
    }
    filter { "system:windows", "platforms:x86_64", "configurations:release" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/release" 
        }
    filter { "system:windows", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        links { "nvToolsExt64_1"}
    filter { "system:linux", "platforms:x86_64", "configurations:debug" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/debug", 
            "%{root}/_build/target-deps/vhacd/bin/linux.clang/debug" 
        }
    filter { "system:linux", "platforms:x86_64", "configurations:release" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/linux.clang/release" 
        }
    filter { "system:linux", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        links { "nvToolsExt"}
    filter {}
    defines {  "PX_PHYSX_STATIC_LIB"}

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
        "%{root}/_build/target-deps/octomap/include",
     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_physics/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/usd_ext_isaac/%{cfg.buildcfg}/lib",
        "%{kit_sdk_bin_dir}/plugins",             
        "%{root}/_build/target-deps/octomap/lib",
        "%{root}/_build/target-deps/omni_physics/lib",
    }

    links {"ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdShade", "vt", "work", "pxOsd",
    "hdx", "hd", "usdImaging", "hdSt", "usdLux", "usdUtils", "octomap", "omni.usd", "usdPhysics",
    "PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"}

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
    
-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "omni.isaac.occupancy_map.python",
    module = "_occupancy_map",
    src = "bindings",
    target_subdir = "omni/isaac/occupancy_map"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/occupancy_map/scripts" },
}

repo_build.prebuild_copy {
    { "%{root}/_build/target-deps/octomap/lib/**", ext.target_dir.."/bin" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/occupancy_map" },
}
