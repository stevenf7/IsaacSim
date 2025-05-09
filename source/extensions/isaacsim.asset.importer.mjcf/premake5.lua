local ext = get_current_extension_info()
project_ext(ext)

-- C++ Carbonite plugin
project_ext_plugin(ext, "isaacsim.asset.importer.mjcf.plugin")
    symbols "On"
    exceptionhandling "On"
    rtti "On"
    staticruntime "Off"

    cppdialect "C++17"

    flags { "FatalCompileWarnings", "MultiProcessorCompile", "NoPCH", "NoIncrementalLink" }
    removeflags { "FatalCompileWarnings", "UndefinedIdentifiers" }

    add_files("impl", "plugins")

    includedirs {
        target_deps.."/pybind11/include",
        target_deps.."/usd/%{cfg.buildcfg}/include",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/include",
        target_deps.."/python/include/python3.11",
        target_deps.."/tinyxml2/include",
        target_deps.."/omni_client_library/include",
        target_deps.."/omniverse_asset_converter/include",
        extsbuild_dir .. "%{root}/source/extensions/isaacsim.robot.schema/include",
    }

    libdirs {
        target_deps.."/usd/%{cfg.buildcfg}/lib",
        target_deps.."/usd_ext_physics/%{cfg.buildcfg}/lib",
        target_deps.."/tinyxml2/lib",
        target_deps.."/omni_client_library/%{cfg.buildcfg}",
        extsbuild_dir.."/omni.usd.core/bin",
        target_deps.."/omniverse_asset_converter/lib",
    }

    links {
        "physicsSchemaTools", "physxSchema", "omni.usd", "tinyxml2", "omniclient", "tbb", "omniverse_asset_converter"
    }

    extra_usd_libs = { "usdGeom", "usdUtils", "usdShade", "usdImaging", "usdPhysics"}

    -- Begin OpenUSD
    add_usd(extra_usd_libs)
    -- End OpenUSD

    if os.target() == "linux" then
        includedirs {
            target_deps.."/usd/%{cfg.buildcfg}/include/boost",
            target_deps.."/python/include/python3.11",
        }
        libdirs {

        }
        links {
            "stdc++fs"
        }
    else
        filter { "system:windows", "platforms:x86_64" }
        filter {}
        libdirs {
            target_deps.."/tbb/lib/intel64/vc14",
        }
    end

-- Python Bindings for Carobnite Plugin
project_ext_bindings {
    ext = ext,
    project_name = "isaacsim.asset.importer.mjcf.python",
    module = "_mjcf",
    src = "bindings",
    target_subdir = "isaacsim/asset/importer/mjcf"
}

repo_build.prebuild_link {
    { "python/scripts", ext.target_dir.."/isaacsim/asset/importer/mjcf/scripts" },
    { "python/tests", ext.target_dir.."/isaacsim/asset/importer/mjcf/tests" },
    { "docs", ext.target_dir.."/docs" },
    { "data", ext.target_dir.."/data" },
    { "icons", ext.target_dir.."/icons" },
}

repo_build.prebuild_copy {

    { "python/*.py", ext.target_dir.."/isaacsim/asset/importer/mjcf" },
}


if os.target() == "linux" then
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/tinyxml2/lib/**.so.*", ext.target_dir.."/bin" },
    }
else
    repo_build.prebuild_copy {
        { "%{root}/_build/target-deps/tinyxml2/bin/**.dll", ext.target_dir.."/bin" },
    }
end