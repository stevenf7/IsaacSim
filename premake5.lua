-- Add new option to enable passing host platform for cross-compilation
newoption {
    trigger     = "platform-host",
    description = "(Optional) Specify host platform for cross-compilation"
}

-- Shared build scripts from repo_build package
repo_build = require("omni/repo/build")

-- Repo root
root = repo_build.get_abs_path(".")

-- Include Kit SDK public premake, it defines few global variables and helper functions. Look inside to get more info.
local build_path = "_build/"..os.target().."-x86_64/"
local _ = dofileopt(build_path.."release/kit/dev/premake5-public.lua") or dofileopt(build_path.."debug/kit/dev/premake5-public.lua")

-- Shared build scripts from isaac sim
include("isaac_sim_premake5.lua")

-- Setup where to write generate prebuild.toml file
repo_build.set_prebuild_file('_build/generated/prebuild.toml')

--
function write_version_file(config)
    local cmd
    if os.target() == "windows" then
        local dir = root.."/_build/windows-x86_64/"..config

        local file = io.open(root.."/VERSION", "r")
        local ver_str = file:read("*a")
        file:close()

        file = io.open(dir.."/SHORT_VERSION", "w")
        file:write(ver_str)
        file:close()

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
        "%{kit_dev_dir}/include",
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

        -- Link all licenses
        { "_build/PACKAGE-LICENSES", bin_dir.."/PACKAGE-LICENSES" },
        
        -- TODO:
        -- Link python app sources in target dir for easier edit
        -- { "source/pythonapps/target", bin_dir.."/pythonapps" },
    }

    repo_build.prebuild_copy {
        -- Copy launcher file
        { "launcher.toml", bin_dir },

    --     -- Copy python app running scripts in target dir
    --     {"source/pythonapps/runscripts/$config/*$shell_ext", bin_dir}
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
        disablewarnings {"error=unused-function"}
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

-- same as above but writes to tests folder
function define_startup_experience(app_name, kit_file, extra_args)
    local script_dir_token = (os.target() == "windows") and "%~dp0" or "$SCRIPT_DIR"
    local extra_args = extra_args or ""
    local kit_file = kit_file or app_name
    define_test_experience(app_name, { config_path = "../apps/"..kit_file..".kit",
                     extra_args = "--ext-folder \""..script_dir_token.."/../exts\" "
                        .."--ext-folder \""..script_dir_token.."/../apps\" "
                        ..extra_args
    })
end

group "apps"
    for _, config in ipairs(ALL_CONFIGS) do
        -- Direct shortcur to kit executable for convenience:
        -- create_experience_runner("kit", nil, config, "")

        -- Put build version file into build directories
        write_version_file(config)
    end

    define_local_experience("isaac-sim", "omni.isaac.sim")
    define_local_experience("isaac-sim.launcher", "omni.isaac.sim.launcher")
    define_local_experience("isaac-sim.headless.kitremote", "omni.isaac.sim.headless.kitremote", "--no-window ")
    define_local_experience("isaac-sim.headless.webrtc", "omni.isaac.sim.headless.webrtc", "--no-window ")
    define_local_experience("isaac-sim.headless.websocket", "omni.isaac.sim.headless.websocket", "--no-window ")

group "startup_tests"
    define_startup_experience("tests-startup.main", "omni.isaac.sim.startup.main", "--/app/quitAfter=500")
    define_startup_experience("tests-startup.websocket", "omni.isaac.sim.startup.websocket", "--no-window --/app/quitAfter=500")
    define_startup_experience("tests-startup.kitremote", "omni.isaac.sim.startup.kitremote", "--no-window --/app/quitAfter=500")
    define_startup_experience("tests-startup.webrtc", "omni.isaac.sim.startup.webrtc", "--no-window --/app/quitAfter=500")
    define_startup_experience("tests-startup.warmup", "omni.isaac.sim.warmup")

    define_startup_experience(
        "tests-launcher.main", 
        "omni.isaac.sim.launcher", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.launcher/auto_launch=false --/persistent/ext/omni.isaac.launcher/show_console=true --/persistent/ext/omni.isaac.launcher/persistent_launcher=false" 
    )
    define_startup_experience(
        "tests-launcher.autolaunch", 
        "omni.isaac.sim.launcher", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.launcher/auto_launch=true --/persistent/ext/omni.isaac.launcher/show_console=true --/persistent/ext/omni.isaac.launcher/persistent_launcher=false --/persistent/ext/omni.isaac.launcher/extra_args='--/app/quitAfter=10'"
    )
    define_startup_experience(
        "tests-launcher.no_show_console", 
        "omni.isaac.sim.launcher", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.launcher/auto_launch=true --/persistent/ext/omni.isaac.launcher/show_console=false --/persistent/ext/omni.isaac.launcher/persistent_launcher=false --/persistent/ext/omni.isaac.launcher/extra_args='--/app/quitAfter=10'"
    )
    define_startup_experience(
        "tests-launcher.persist", 
        "omni.isaac.sim.launcher", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.launcher/auto_launch=true --/persistent/ext/omni.isaac.launcher/show_console=true --/persistent/ext/omni.isaac.launcher/persistent_launcher=true --/persistent/ext/omni.isaac.launcher/extra_args='--/app/quitAfter=10'"
    )

-- Isaac Extensions
group "exts"
    -- Windows and Linux
    include ("source/extensions/omni.isaac.app.setup")
    include ("source/extensions/omni.isaac.app.launcher")
    include ("source/extensions/omni.isaac.contact_sensor")
    include ("source/extensions/omni.isaac.debug_draw")
    include ("source/extensions/omni.isaac.dr")
    include ("source/extensions/omni.isaac.dynamic_control")
    include ("source/extensions/omni.isaac.dynamic_control.samples")
    include ("source/extensions/omni.isaac.internal_tools")
    include ("source/extensions/omni.isaac.imu_sensor")
    include ("source/extensions/omni.isaac.manip")
    include ("source/extensions/omni.isaac.merge_mesh")
    include ("source/extensions/omni.isaac.onshape")
    include ("source/extensions/omni.isaac.proximity_sensor")
    include ("source/extensions/omni.isaac.python_app")
    include ("source/extensions/omni.isaac.physics_inspector")
    include ("source/extensions/omni.isaac.physics_utilities")
    include ("source/extensions/omni.isaac.range_sensor")
    include ("source/extensions/omni.isaac.samples")
    include ("source/extensions/omni.isaac.shapenet")
    include ("source/extensions/omni.isaac.splash")
    include ("source/extensions/omni.isaac.surface_gripper")
    include ("source/extensions/omni.isaac.synthetic_recorder")
    include ("source/extensions/omni.isaac.synthetic_utils")
    include ("source/extensions/omni.isaac.synthetic_workflow")
    include ("source/extensions/omni.isaac.tests")
    include ("source/extensions/omni.isaac.utils")
    include ("source/extensions/omni.isaac.urdf")
    include ("source/extensions/omni.isaac.ui")
    include ("source/extensions/omni.isaac.ui_template")
    include ("source/extensions/omni.isaac.layout_manager")
    include ("source/extensions/omni.isaac.window.about")
    include ("source/extensions/omni.kit.property.isaac")
    include ("source/extensions/omni.kit.loop-isaac")
    include ("source/extensions/omni.usd.schema.isaac")
    include ("source/extensions/omni.isaac.kit")
    include ("source/extensions/omni.isaac.pip_archive")
    include ("source/extensions/omni.isaac.core")
    include ("source/extensions/omni.isaac.franka")

    -- include ("source/extensions/omni.isaac.samples_internal")
    -- include ("source/extensions/omni.isaac.exploded_view")

    -- Linux Only
    if os.target() == "linux" then
        include ("source/extensions/omni.isaac.motion_planning")
	include ("source/extensions/omni.isaac.motion_generation")
        include ("source/extensions/omni.isaac.robot_benchmark")
        include ("source/extensions/omni.isaac.benchmark_environments")
        include ("source/extensions/omni.isaac.occupancy_map")
        include ("source/extensions/omni.isaac.robot_engine_bridge_ui")
        include ("source/extensions/omni.isaac.robot_engine_bridge")
        include ("source/extensions/omni.isaac.robot_engine_bridge_gxf")
        include ("source/extensions/omni.isaac.ros_bridge_ui")
        include ("source/extensions/omni.isaac.ros_bridge")
        include ("source/extensions/omni.isaac.ros2_bridge")
        include ("source/extensions/omni.isaac.utils_manager")

    end




repo_build.prebuild_link {
    { "source/python_samples", "_build/%{platform}/%{config}/python_samples" },
    { "source/examples", "_build/%{platform}/%{config}/examples" },
    { "source/ros_samples", "_build/%{platform}/%{config}/ros_samples" },
    { "source/ros2_samples", "_build/%{platform}/%{config}/ros2_samples" },
}

repo_build.prebuild_copy {
    {"source/scripts/python.sh",  "_build/%{platform}/%{config}"},
    {"source/scripts/jupyter_kernel",  "_build/%{platform}/%{config}/jupyter_kernel"},
    {"source/scripts/jupyter_notebook.sh",  "_build/%{platform}/%{config}"},
    {"source/scripts/run_all_tests.sh",  "_build/%{platform}/%{config}"},
    {"source/scripts/omni.isaac.sim.post.install.sh",  "_build/%{platform}/%{config}"},
    {"source/scripts/omni.isaac.sim.warmup.sh",  "_build/%{platform}/%{config}"},
    {"source/apps/omni.isaac.sim.python.kit",  "_build/%{platform}/%{config}/apps"},
    {"source/scripts/vscode",  "_build/%{platform}/%{config}/.vscode"},

}

group "python_samples"
    -- Core samples
    python_sample_test("tests-nativepython-core.app_framework", "python_samples/core/app_framework.py")
    python_sample_test("tests-nativepython-omni.isaac.kit.example_zero", "examples/api/omni.isaac.kit/example_zero.py")
    -- Simple samples
    python_sample_test("tests-nativepython-simple.time_stepping", "python_samples/simple/time_stepping.py")
    python_sample_test("tests-nativepython-simple.urdf_import", "python_samples/simple/urdf_import.py")
    python_sample_test("tests-nativepython-simple.franka_articulation", "python_samples/simple/franka_articulation.py")
    python_sample_test("tests-nativepython-simple.change_resolution", "python_samples/simple/change_resolution.py")
    python_sample_test("tests-nativepython-simple.load_stage", "python_samples/simple/load_stage.py", "--usd_path /Environments/Simple_Room/simple_room.usd --test --headless")
    python_sample_test("tests-nativepython-simple.franka_rmp", "python_samples/simple/franka_rmp.py", "--headless")
    -- SDK samples 
    python_sample_test("tests-nativepython-isaac_sdk.pose_estimation", "python_samples/isaac_sdk/pose_estimation.py", "--test")
    python_sample_test("tests-nativepython-isaac_sdk.load_stage", "python_samples/isaac_sdk/load_stage.py", "--usd_path /Samples/Isaac_SDK/Scenario/franka_basic.usd --test --headless")
    -- ROS samples
    python_sample_test("tests-nativepython-ros.clock", "python_samples/ros/clock.py")

group "jupyter_samples"

    jupyter_sample_test("tests-jupyter-startup", "examples/notebooks/basic_notebook.ipynb")