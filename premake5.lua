-- Add new option to enable passing host platform for cross-compilation
newoption {
    trigger     = "platform-host",
    description = "(Optional) Specify host platform for cross-compilation"
}

-- Shared build scripts from repo_build package
repo_build = require("omni/repo/build")

-- Repo root
root = repo_build.get_abs_path(".")

-- Resolved path to kit SDK (without %{} tokens), for creating experiences
KIT_SDK_RESOLVED = {
    ["debug"] = root.."/_build/kit_debug",
    ["release"] = root.."/_build/kit_release",
}

-- Path to kit sdk
kit_sdk = "%{root}/_build/kit_%{config}"
kit_sdk_bin_dir = kit_sdk.."/_build/%{platform}/%{config}"

-- Include Kit SDK public premake, it defines few global variables and helper functions. Look inside to get more info.
include("_build/kit_release/premake5-public.lua")


-- Shared build scripts from isaac sim
include("isaac_sim_premake5.lua")

-- Setup where to write generate prebuild.toml file
repo_build.set_prebuild_file('_build/generated/prebuild.toml')

--
function write_version_file(config)
    local cmd
    if os.target() == "windows" then
        local dir = root.."/_build/windows-x86_64/"..config
        cmd = "repo.bat build_number -o "..dir.."/VERSION"
    else
        local dir = root.."/_build/linux-x86_64/"..config
        cmd = "./repo.sh build_number -o "..dir.."/VERSION"
    end
    os.execute(get_current_lua_file_dir().."/"..cmd)
end

-- Starting from here we define a structure of actual solution to be generated. Starting with solution name.
workspace "isaac-sim"
    configurations { "debug", "release" }

    -- Project selected by default to run
    startproject ""

    -- Set location for solution file
    location (workspace_dir)

    -- Set default target dir, later projects overwrite it
    targetdir (bin_dir)

    -- Setup include paths. Add kit SDK include paths too.
    includedirs {
        "include",
        "_build/target-deps",
        "_build/target-deps/carb_sdk_plugins/include",
        "%{kit_sdk}/include",
        "%{kit_sdk}/_build/target-deps/",
    }

    -- Carbonite carb lib
    libdirs { "%{root}/_build/target-deps/carb_sdk_plugins/_build/%{platform}/%{config}" }

    -- Location for intermediate  files
    objdir ("_build/intermediate/%{platform}/%{prj.name}")

    -- Default compilation settings
    symbols "On"
    exceptionhandling "On"
    rtti "On"
    staticruntime "On"
    flags { "FatalCompileWarnings", "MultiProcessorCompile", "NoPCH", "NoIncrementalLink" }
    cppdialect "C++14"

    -- Generic folder linking and file copy setup:
    repo_build.prebuild_link {
        -- Link app configs in target dir for easier edit
        { "source/apps", bin_dir.."/apps" },
    }

    -- Windows platform settings
    filter { "system:windows" }
        platforms { "x86_64" }

        -- Add .editorconfig to all projects so that VS 2017 automatically picks it up
        files {".editorconfig"}
        editandcontinue "Off"

        -- Enable usage of brought up toolchain
        setup_msvc_toolchain()

        -- All of our source strings and executable strings are utf8
        buildoptions {"/utf-8", "/bigobj"}
        buildoptions {"/permissive-"}


    -- Linux platform settings
    filter { "system:linux" }
        platforms { "x86_64", "aarch64" }
        defaultplatform "x86_64"

        buildoptions { "-fvisibility=hidden -D_FILE_OFFSET_BITS=64" }

        -- Add library origin directory to dlopen() search path
        linkoptions { "-Wl,-rpath,'$$ORIGIN' -Wl,--export-dynamic" }

        enablewarnings { "all" }

    filter { "platforms:x86_64" }
        architecture "x86_64"

    -- Debug configuration settings
    filter { "configurations:debug" }
        defines { "_DEBUG" }
        optimize "Off"

    -- Release configuration settings
    filter  { "configurations:release" }
        defines { "NDEBUG" }
        optimize "Speed"

    filter {}

function create_app_shortcut(app_name, config)
    if os.target() == "windows" then
        local bat_file_path = root.."/_build/windows-x86_64/"..config.."/appshortcuts/"..app_name..".bat"
        local app_path = "_build/windows-x86_64/"..config.."/"..app_name..".bat"
        f = io.open(bat_file_path, 'w')
        f:write(string.format([[
@echo off
setlocal
call "%%~dp0/%s" %%*
        ]], app_path))
    else
        local sh_file_path = root.."/_build/linux-x86_64/"..config.."/appshortcuts/"..app_name..".sh"
        local app_path = "_build/linux-x86_64/"..config.."/"..app_name..".sh"
        f = io.open(sh_file_path, 'w')
        f:write(string.format([[
#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
exec "$SCRIPT_DIR/%s" $@
        ]], app_path))
        f:close()
        os.chmod(sh_file_path, 755)
    end
end

-- Helper to create bat/sh files to run local kit files
function define_local_experience(app_name, kit_file, extra_args)
    local script_dir_token = (os.target() == "windows") and "%~dp0" or "$SCRIPT_DIR"
    local extra_args = extra_args or ""
    local kit_file = kit_file or app_name
    define_experience(app_name, { config_path = "apps/"..kit_file..".kit",
                     extra_args = "--ext-folder \""..script_dir_token.."/exts\" "
                        .."--ext-folder \""..script_dir_token.."/apps\" "
                        ..extra_args
    })

    for _, config in ipairs(ALL_CONFIGS) do
        create_app_shortcut(app_name, config)
    end
end


group "apps"
    for _, config in ipairs(ALL_CONFIGS) do
        -- Direct shortcur to kit executable for convenience:
        -- create_experience_runner("kit", nil, config, "")

        -- Put build version file into build directories
        write_version_file(config)
    end

    define_local_experience("isaac-sim")
    define_local_experience("isaac-sim.launcher")
    -- We reuse the isaac sim config and add additional args to it
    local headless_args = "--no-window --enable omni.kit.livestream.core "
        .."--/app/window/width=1280 --/app/window/height=800 --/app/window/drawMouse=true "
        .."--/ngx/enabled=false --/app/livestream/proto=tcp --/app/livestream/logLevel=info "
    define_local_experience("isaac-sim.headless", "isaac-sim", 
                            "--enable  omni.kit.livestream.native "..headless_args)
    define_local_experience("isaac-sim.headless.webrtc", "isaac-sim", 
                            "--enable  omni.kit.livestream.webrtc "..headless_args)


    -- -- Test runner experience:
    -- args = {
    --     "--/exts/omni.kit.test/runTestsAndQuit=true", -- Run tests and quit
    --     "--/exts/omni.kit.test/includeTests/0='omni.create.app.*'", -- Only include tests from the python module
    -- }
    -- define_local_experience("tests-create-mini", "omni.create.mini", table.concat(args, " "))

-- Isaac Extensions
group "exts"
    -- Windows and Linux
    -- include ("source/extensions/omni.isaac.decals")
    include ("source/extensions/omni.isaac.dr")
    include ("source/extensions/omni.isaac.dynamic_control")
    include ("source/extensions/omni.isaac.contact_sensor")
    include ("source/extensions/omni.isaac.range_sensor")
    include ("source/extensions/omni.isaac.manip")
    include ("source/extensions/omni.isaac.shapenet")
    include ("source/extensions/omni.isaac.utils")
    include ("source/extensions/omni.isaac.urdf")
    include ("source/extensions/omni.isaac.samples")
    -- include ("source/extensions/omni.isaac.samples_internal")
    include ("source/extensions/omni.isaac.synthetic_utils")
    include ("source/extensions/omni.isaac.tests")
    include ("source/extensions/omni.isaac.step_importer")
    -- include ("source/extensions/omni.isaac.exploded_view")
    include ("source/extensions/omni.isaac.internal_tools")
    include ("source/extensions/omni.isaac.app.setup")
    include ("source/extensions/omni.isaac.app.launcher")
    include ("source/extensions/omni.isaac.splash")

    include ("source/extensions/omni.kit.property.isaac")
    include ("source/extensions/omni.kit.loop-isaac")

    -- Linux Only
    if os.target() == "linux" then
        include ("source/extensions/omni.isaac.motion_planning")
        include ("source/extensions/omni.isaac.robot_engine_bridge")
        include ("source/extensions/omni.isaac.ros_bridge")
        include ("source/extensions/omni.isaac.occupancy_map")
    end

repo_build.prebuild_link {
    { "source/python_samples", "_build/python_samples" },
    { "source/ros_samples", "_build/ros_samples" },
}

group "python_samples"
    python_sample_test("tests-python.core.app_framework", "core/app_framework.py")
    python_sample_test("tests-python.simple.time_stepping", "simple/time_stepping.py")
    python_sample_test("tests-python.simple.urdf_import", "simple/urdf_import.py")
    python_sample_test("tests-python.simple.franka_articulation", "simple/franka_articulation.py")
    python_sample_test("tests-python.simple.change_resolution", "simple/change_resolution.py")
    python_sample_test("tests-python.isaac_sdk.pose_estimation", "isaac_sdk/pose_estimation.py", "--test")
