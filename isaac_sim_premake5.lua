
function include_physx()
    -- Which physx library type to use in release mode
    physx_libs = "profile"
    
    if configuration == "debug" then
        physx_libs = "debug"
    end

    filter { "configurations:debug" }
        defines {  "PX_PHYSX_STATIC_LIB", "_DEBUG" }
    filter { "configurations:release" }
        defines {  "PX_PHYSX_STATIC_LIB", "NDEBUG" }

    filter { "system:windows", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/win.x86_64.vc141.md/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/win.x86_64.vc141.md/%{config}" 
        }
        links { "nvToolsExt64_1"}
    filter {}

    filter { "system:linux", "platforms:x86_64" }
        libdirs { "%{root}/_build/target-deps/nvtx/lib/x64" }
        links { "nvToolsExt"}
        libdirs { 
            "%{root}/_build/target-deps/physx/bin/linux.clang/"..physx_libs, 
            "%{root}/_build/target-deps/vhacd/bin/linux.clang/%{config}" 
        }

    links { "PhysXExtensions_static_64", "PhysX_static_64", "PhysXPvdSDK_static_64","PhysXCooking_static_64","PhysXCommon_static_64", "PhysXFoundation_static_64"}

end
