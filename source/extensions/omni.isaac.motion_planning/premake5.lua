local ext = get_current_extension_info()
project_ext (ext)


-- C++ Carbonite plugin
project_ext_plugin(ext, "omni.isaac.motion_planning.plugin")
    staticruntime "Off"
    exceptionhandling "On"
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }
    cppdialect "C++17"

    add_files("impl", "plugins")
    add_files("iface", "%{root}/include/omni/isaac/motion_planning/**")

    -- physx libs
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

    includedirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include",
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/include/boost",
        "%{root}/_build/target-deps/lula/include",
        "%{root}/_build/target-deps/python/include/python3.6m",
        "%{root}/_build/target-deps/rtx_plugins/include",
        "%{root}/_build/target-deps/client_library/include",

     }
     libdirs {
        "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/lib",
        "%{root}/_build/target-deps/lula/lib"
    }

    links {"gf", "sdf", "usdGeom", "usdUtils", "lula_opt", "lula_kinematics", "lula_math" , "lula_rmpflow", "lula_util", "yaml-cpp", "urdfdom_model", "glog"}

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
project_ext_bindings (  {ext = ext,
                        project_name = "omni.isaac.motion_planning.python",
                        module = "_motion_planning",
                        src = "bindings",
                        target_subdir = "omni/isaac/motion_planning"})
    
    includedirs {"%{root}/_build/target-deps/lula/include"}
    cppdialect "C++17"


repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/omni/isaac/motion_planning/scripts" },
}
repo_build.prebuild_link {
    { "%{root}/_build/target-deps/lula/data", ext.target_dir.."/omni/isaac/motion_planning/resources/lula/" },
}

repo_build.prebuild_copy {
    { "python/*.py", ext.target_dir.."/omni/isaac/motion_planning" },
}
