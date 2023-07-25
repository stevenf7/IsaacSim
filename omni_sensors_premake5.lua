-- functions and defines used by omni.sensors that are in drivesim's premake5.lua 

bin2cPath = path.getabsolute("_build/target-deps/cuda/bin/bin2c");
nv_usd = "%{root}/_build/target-deps/nv_usd/%{cfg.buildcfg}/"
obj_dir = "_build/obj/%{prj.name}"

includedirs {"%{root}/_build/target-deps/gsl/include"}

----------------------------CUDA-------------------------------------------------------------


function link_boost_1_76_for_windows(libs)
    link_boost_for_windows(libs)
end

function includeUsd()
    staticruntime "Off"
    exceptionhandling "On"
    rtti "On"
    setRuntimeToBeKitCompatible()
    includedirs { "include",
                  "%{root}/_build/target-deps/usd_ext/"..kit_sdk_config.."/include",
                  "%{root}/_build/target-deps/usd_audio_schema/"..kit_sdk_config.."/include",
                  "%{root}/_build/target-deps/usd_schema_semantics/"..kit_sdk_config.."/include",
                  "%{nv_usd}/include",
                  "%{root}/_build/target-deps/rtx_plugins/include",
                  "%{root}/source/pch",-- drivesim, like kit, keeps pch in source/pch.  isaac-sim keeps it in include/pch
                  "%{root}/include/pch",-- drivesim, like kit, keeps pch in source/pch.  isaac-sim keeps it in include/pch
                  "%{root}/_build/target-deps/python/include",
                  "%{target_deps}/omni_client_library/include",-- isaac-sim location
                  "%{target_deps}/client-library/include" } -- drivesim location
    libdirs { "%{root}/_build/target-deps/usd_ext/"..kit_sdk_config.."/lib",
              "%{kit_sdk}/plugins",
              "%{root}/_build/target-deps/usd_audio_schema/"..kit_sdk_config.."/lib",
              "%{root}/_build/target-deps/usd_schema_semantics/"..kit_sdk_config.."/lib",
              "%{nv_usd}/lib",
              "%{kit_sdk}/exts/omni.usd.core/bin",
              "%{kit_sdk}/exts/omni.usd.libs/bin",
              "%{kit_sdk}/exts/omni.usd.schema.audio/bin",
              "%{kit_sdk}/exts/omni.usd.schema.semantics/bin"}

    links { "omni.usd" }
    links {
        "ar", "arch", "gf", "js", "kind", "pcp", "plug", "sdf", "tf", "trace", "usd", "usdGeom", "usdSkel", "usdShade", "vt", "work", "pxOsd",
        "hdx", "hd", "usdImaging",  "usdLux", "usdUtils", "usdVolImaging"
    }
    filter { "system:windows" }
        libdirs {   "%{root}/_build/target-deps/python/libs",
                    "%{root}/_build/target-deps/tbb/lib/intel64/vc14",
                    "%{nv_usd}/lib" }
        includedirs { "%{root}/_build/target-deps/opensubdiv/%{config}/include" }
        link_boost_1_76_for_windows({"boost_python310"})
    filter { "system:linux" }
        exceptionhandling "On"
        removeflags { "UndefinedIdentifiers" }
        includedirs { "%{nv_usd}/include/boost",
                      "%{root}/_build/target-deps/python/include/python3.10" }
        libdirs {   "%{root}/_build/target-deps/python/lib" }
        buildoptions { "-pthread" }
        links { "dl", "pthread", "tbb", "boost_python310", "python3.10" }
    filter {}
end