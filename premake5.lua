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
local build_path = root.."/_build/"..os.target().."-x86_64/"

if os.isfile(build_path.."release/kit/dev/premake5-public.lua") then
    kit_sdk = build_path.."release/kit"
    dofile(build_path.."release/kit/dev/premake5-public.lua")
else
    kit_sdk = build_path.."debug/kit"
    dofile(build_path.."debug/kit/dev/premake5-public.lua")
end

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

    carbSDKPath = "%{root}/_build/target-deps/carb_sdk_plugins"
    carbSDKInclude = carbSDKPath.."/include"
    carbSDKLibs = carbSDKPath.."/_build/"..platform.."/%{config}"
    
    nvccPath = path.getabsolute("_build/target-deps/cuda/bin/nvcc");
    nvccHostCompilerVS =  path.getabsolute("_build/host-deps/msvc/VC");

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
        -- Copy licenses
        { "tools/internal-licenses/*",  bin_dir.."/PACKAGE-LICENSES" },

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
                     extra_args = "--ext-folder \""..script_dir_token.."/apps\" "
                        ..extra_args
    })

    -- disable appshortcuts
    -- for _, config in ipairs(ALL_CONFIGS) do
    --     create_app_shortcut(app_name, config)
    -- end
end

-- same as above but writes to tests folder
function define_startup_experience(app_name, kit_file, extra_args)
    local script_dir_token = (os.target() == "windows") and "%~dp0" or "$SCRIPT_DIR"
    local extra_args = extra_args or ""
    local kit_file = kit_file or app_name
    define_test_experience(app_name, { config_path = "../apps/"..kit_file..".kit",
                     extra_args = "--ext-folder \""..script_dir_token.."/../apps\" "
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
    define_local_experience("isaac-sim.selector", "omni.isaac.sim.selector")
    define_local_experience("isaac-sim.headless.native", "omni.isaac.sim.headless.native", "--no-window ")
    define_local_experience("isaac-sim.headless.websocket", "omni.isaac.sim.headless.websocket", "--no-window ")
    define_local_experience("isaac-sim.headless.websocket.h264", "omni.isaac.sim.headless.websocket", "--no-window --/app/livestream/websocket/encoder_selection=OPENH264 ")
    define_local_experience("isaac-sim.headless.webrtc", "omni.isaac.sim.headless.webrtc", "--no-window ")
    define_local_experience("isaac-sim.xr.steamvr", "omni.isaac.sim.xr.steamvr")

group "startup_tests"
    -- use "--/app/settings/persistent=0 --/app/settings/loadUserConfig=0" to ignore config user config file
    -- use "--reset-user" to reset user config file
    define_startup_experience("tests-startup.main", "omni.isaac.sim", "--/app/quitAfter=500")
    define_startup_experience("tests-startup.websocket", "omni.isaac.sim.headless.websocket", "--no-window --/app/quitAfter=500")
    define_startup_experience("tests-startup.websocket.h264", "omni.isaac.sim.headless.websocket", "--no-window --/app/livestream/websocket/encoder_selection=OPENH264 --/app/quitAfter=500")
    define_startup_experience("tests-startup.webrtc", "omni.isaac.sim.headless.webrtc", "--no-window --/app/quitAfter=500")
    define_startup_experience("tests-startup.native", "omni.isaac.sim.headless.native", "--no-window --/app/quitAfter=500")
    -- Windows Only
    if os.target() == "windows" then
        define_startup_experience("tests-startup.xr.steamvr", "omni.isaac.sim.xr.steamvr", "--no-window --/app/quitAfter=500")
    end

group "selector_tests"
    define_startup_experience(
        "tests-selector.default", 
        "omni.isaac.sim.selector", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.selector/auto_start=false --/persistent/ext/omni.isaac.selector/show_console=true --/persistent/ext/omni.isaac.selector/persistent_selector=false" 
    )
    define_startup_experience(
        "tests-selector.autolaunch_and_persist", 
        "omni.isaac.sim.selector", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.selector/auto_start=true --/persistent/ext/omni.isaac.selector/show_console=true --/persistent/ext/omni.isaac.selector/persistent_selector=true --/persistent/ext/omni.isaac.selector/extra_args='--/app/quitAfter=10'"
    )
    define_startup_experience(
        "tests-selector.no_show_console", 
        "omni.isaac.sim.selector", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.selector/auto_start=true --/persistent/ext/omni.isaac.selector/show_console=false --/persistent/ext/omni.isaac.selector/persistent_selector=true --/persistent/ext/omni.isaac.selector/extra_args='--/app/quitAfter=10'"
    )
    define_startup_experience(
        "tests-selector.persist", 
        "omni.isaac.sim.selector", 
        "--/app/quitAfter=500 --/persistent/ext/omni.isaac.selector/auto_start=false --/persistent/ext/omni.isaac.selector/show_console=true --/persistent/ext/omni.isaac.selector/persistent_selector=true --/persistent/ext/omni.isaac.selector/extra_args='--/app/quitAfter=10'"
    )

-- Isaac Extensions
group "exts"
    -- Windows and Linux
    include ("source/extensions/omni.isaac.app.setup")
    include ("source/extensions/omni.isaac.app.selector")
    include ("source/extensions/omni.isaac.articulation_inspector")
    include ("source/extensions/omni.isaac.assets_check")
    include ("source/extensions/omni.isaac.benchmark_environments")
    include ("source/extensions/omni.isaac.benchmarks")
    include ("source/extensions/omni.isaac.cloner")
    include ("source/extensions/omni.isaac.collision_sphere_editor")
    include ("source/extensions/omni.isaac.core")
    include ("source/extensions/omni.isaac.core_archive")
    include ("source/extensions/omni.isaac.core_nodes")
    include ("source/extensions/omni.isaac.conveyor")   
    include ("source/extensions/omni.isaac.diff_usd")
    include ("source/extensions/omni.isaac.debug_draw")
    include ("source/extensions/omni.isaac.demos")
    include ("source/extensions/omni.isaac.dofbot")
    include ("source/extensions/omni.isaac.dynamic_control")
    include ("source/extensions/omni.isaac.examples")
    include ("source/extensions/omni.isaac.franka")
    include ("source/extensions/omni.isaac.manipulators")
    include ("source/extensions/omni.isaac.gain_tuner")
    include ("source/extensions/omni.isaac.gym")
    include ("source/extensions/omni.isaac.internal_tools")
    include ("source/extensions/omni.isaac.sensor")
    include ("source/extensions/omni.isaac.isaac_sensor")
    include ("source/extensions/omni.isaac.kit")
    include ("source/extensions/omni.isaac.lula")
    include ("source/extensions/omni.isaac.merge_mesh")
    include ("source/extensions/omni.isaac.ml_archive")
    include ("source/extensions/omni.isaac.motion_generation")
    include ("source/extensions/omni.isaac.motion_planning")
    include ("source/extensions/omni.isaac.occupancy_map")
    include ("source/extensions/omni.isaac.onshape")
    include ("source/extensions/omni.isaac.partition")
    include ("source/extensions/omni.isaac.proximity_sensor")
    include ("source/extensions/omni.isaac.physics_inspector")
    include ("source/extensions/omni.isaac.physics_utilities")
    include ("source/extensions/omni.isaac.quadruped")
    include ("source/extensions/omni.isaac.repl")
    include ("source/extensions/omni.isaac.range_sensor")
    include ("source/extensions/omni.isaac.robot_benchmark")
    include ("source/extensions/omni.isaac.shapenet")
    include ("source/extensions/omni.isaac.statistics_logging")
    include ("source/extensions/omni.isaac.splash")
    include ("source/extensions/omni.isaac.surface_gripper")
    include ("source/extensions/omni.isaac.synthetic_recorder")
    include ("source/extensions/omni.isaac.synthetic_utils")
    include ("source/extensions/omni.isaac.tests")
    include ("source/extensions/omni.isaac.universal_robots")
    include ("source/extensions/omni.isaac.utils")
    include ("source/extensions/omni.isaac.urdf")
    include ("source/extensions/omni.isaac.ui")
    include ("source/extensions/omni.isaac.ui_template")
    include ("source/extensions/omni.isaac.unit_converter")
    include ("source/extensions/omni.isaac.wheeled_robots")
    include ("source/extensions/omni.isaac.mjcf")
    include ("source/extensions/omni.isaac.window.about")
    include ("source/extensions/omni.kit.property.isaac")
    include ("source/extensions/omni.kit.loop-isaac")
    include ("source/extensions/omni.usd.schema.isaac")
    include ("source/extensions/omni.isaac.asset_browser")
    include ("source/extensions/omni.isaac.version")
    include ("source/extensions/omni.replicator.isaac")
   

    -- Linux Only
    if os.target() == "linux" then
        include ("source/extensions/omni.isaac.cortex")
        include ("source/extensions/omni.isaac.cortex_sync")
        -- include ("source/extensions/omni.isaac.robot_engine_bridge")
        include ("source/extensions/omni.isaac.gxf_bridge")
        include ("source/extensions/omni.isaac.ros_bridge")

        include ("source/extensions/omni.isaac.ros2_bridge")
        include ("source/extensions/omni.isaac.ros2_bridge-humble")
    end


repo_build.prebuild_link {
    { "source/standalone_examples", "_build/%{platform}/%{config}/standalone_examples" },
    { "source/tools", "_build/%{platform}/%{config}/tools"},
}

if os.target() == "linux" then
    repo_build.prebuild_link {
        { "source/ros_workspace", "_build/%{platform}/%{config}/ros_workspace" },
        { "source/ros2_workspace", "_build/%{platform}/%{config}/ros2_workspace" },
    }
    -- For docker tests
    repo_build.prebuild_copy {
        {"source/scripts/docker/tests/*",  "_build/%{platform}/%{config}/dockertests"},
        -- {"source/scripts/docker/vulkan_check.sh",  "_build/%{platform}/%{config}"},
    }
end

if os.target() == "windows" then
    repo_build.prebuild_copy {
        {"source/scripts/omni.isaac.sim.create_junction${shell_ext}",  "_build/%{platform}/%{config}"},
    }
end

repo_build.prebuild_copy {
    {"source/scripts/python/shared/*",  "_build/%{platform}/%{config}"},
    {"source/scripts/python/%{platform}/*",  "_build/%{platform}/%{config}"},
    {"source/scripts/jupyter_kernel",  "_build/%{platform}/%{config}/jupyter_kernel"},
    {"source/scripts/run_all_tests${shell_ext}",  "_build/%{platform}/%{config}"},
    {"source/scripts/omni.isaac.sim.post.install${shell_ext}",  "_build/%{platform}/%{config}"},
    {"source/scripts/omni.isaac.sim.warmup${shell_ext}",  "_build/%{platform}/%{config}"},
    {"source/apps/omni.isaac.sim.python.kit",  "_build/%{platform}/%{config}/apps"},
    {"source/scripts/vscode",  "_build/%{platform}/%{config}/.vscode"},
}

group "python_samples"

    -- smoke tests for python.sh itself
    python_script_test("tests-nativepython-import_sys", "-c \"import sys\" --")
    python_script_test("tests-nativepython-pip_list", "-m pip list --")

    -- omni.kit.app
    python_sample_test("tests-nativepython-omni.kit.app.app_framework", "standalone_examples/api/omni.kit.app/app_framework.py")
    -- omni.isaac.kit
    python_sample_test("tests-nativepython-omni.isaac.kit.hello_world", "standalone_examples/api/omni.isaac.kit/hello_world.py")
    python_sample_test("tests-nativepython-omni.isaac.kit.change_resolution", "standalone_examples/api/omni.isaac.kit/change_resolution.py")
    python_sample_test("tests-nativepython-omni.isaac.kit.load_stage", "standalone_examples/api/omni.isaac.kit/load_stage.py", "--usd_path /Isaac/Environments/Simple_Room/simple_room.usd --test --headless")
    -- omni.isaac.core
    python_sample_test("tests-nativepython-omni.isaac.core.add_cubes", "standalone_examples/api/omni.isaac.core/add_cubes.py")
    python_sample_test("tests-nativepython-omni.isaac.core.add_frankas", "standalone_examples/api/omni.isaac.core/add_frankas.py", "--test")
    python_sample_test("tests-nativepython-omni.isaac.core.data_logging", "standalone_examples/api/omni.isaac.core/data_logging.py")
    python_sample_test("tests-nativepython-omni.isaac.core.control_robot", "standalone_examples/api/omni.isaac.core/control_robot.py")
    python_sample_test("tests-nativepython-omni.isaac.core.simulate_robot", "standalone_examples/api/omni.isaac.core/simulate_robot.py")
    python_sample_test("tests-nativepython-omni.isaac.core.simulation_callbacks", "standalone_examples/api/omni.isaac.core/simulation_callbacks.py")
    python_sample_test("tests-nativepython-omni.isaac.core.time_stepping", "standalone_examples/api/omni.isaac.core/time_stepping.py")
    python_sample_test("tests-nativepython-omni.isaac.core.visual_materials", "standalone_examples/api/omni.isaac.core/visual_materials.py", "--test")
    -- omni.isaac.franka
    python_sample_test("tests-nativepython-omni.isaac.franka.franka_gripper", "standalone_examples/api/omni.isaac.franka/franka_gripper.py", "--test")
    -- omni.isaac.manipulators
    python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.follow_target_example", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/follow_target_example.py", "--test")
    python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.pick_up_example", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/pick_up_example.py", "--test")
    python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.gripper_control", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/gripper_control.py", "--test")
    python_sample_test("tests-nativepython-omni.isaac.manipulators.franka_pick_up", "standalone_examples/api/omni.isaac.manipulators/franka_pick_up.py", "--test")
    python_sample_test("tests-nativepython-omni.isaac.manipulators.ur10_pick_up", "standalone_examples/api/omni.isaac.manipulators/ur10_pick_up.py", "--test")
    -- omni.isaac.jetbot
    python_sample_test("tests-nativepython-omni.isaac.jetbot.stable_baselines_example", "standalone_examples/api/omni.isaac.jetbot/stable_baselines_example/train.py", "--test")
    -- omni.isaac.dynamic_control
    python_sample_test("tests-nativepython-omni.isaac.dynamic_control.franka_articulation", "standalone_examples/api/omni.isaac.dynamic_control/franka_articulation.py")
    -- omni.isaac.urdf
    python_sample_test("tests-nativepython-omni.isaac.urdf.urdf_import", "standalone_examples/api/omni.isaac.urdf/urdf_import.py")
    -- omni.isaac.robot_engine_bridge
    -- python_sample_test("tests-nativepython-omni.isaac.robot_engine_bridge.custom_message", "standalone_examples/api/omni.isaac.robot_engine_bridge/custom_message.py")
    -- python_sample_test("tests-nativepython-omni.isaac.robot_engine_bridge.pose_estimation", "standalone_examples/api/omni.isaac.robot_engine_bridge/pose_estimation.py", "--test")
    -- python_sample_test("tests-nativepython-omni.isaac.robot_engine_bridge.load_stage", "standalone_examples/api/omni.isaac.robot_engine_bridge/load_stage.py", "--usd_path /Isaac/Samples/Isaac_SDK/Scenario/carter_warehouse_with_forklifts.usd --test --headless --add_rebcamera /World/Carter_REB/chassis_link/camera_mount/carter_camera_first_person,1280,720 /World/Carter_REB/chassis_link/camera_mount/carter_camera_third_person,1280,720")
    -- python_sample_test("tests-nativepython-omni.isaac.robot_engine_bridge.freespace_dnn_data_generator", "standalone_examples/api/omni.isaac.robot_engine_bridge/freespace_dnn_data_generator.py", "--test --no-window")

    -- omni.isaac.ros_bridge
    python_sample_test("tests-nativepython-omni.isaac.ros_bridge.clock", "standalone_examples/api/omni.isaac.ros_bridge/clock.py")
    python_sample_test("tests-nativepython-omni.isaac.ros_bridge.contact", "standalone_examples/api/omni.isaac.ros_bridge/contact.py")
    python_sample_test("tests-nativepython-omni.isaac.ros_bridge.carter_stereo", "standalone_examples/api/omni.isaac.ros_bridge/carter_stereo.py", "--test")
    -- Replicator data samples:
    python_sample_test("tests-nativepython-replicator.offline_generation", "standalone_examples/replicator/offline_generation.py")
    python_sample_test("tests-nativepython-replicator.offline_pose_generation", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py")
    python_sample_test("tests-nativepython-replicator.offline_pose_generation_ycbvideo", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--num_mesh 3 --num_dome 3 --writer 'YCBVideo' --output_folder '_out_ycb'")
    python_sample_test("tests-nativepython-replicator.offline_pose_generation_dope", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--num_mesh 3 --num_dome 3 --writer 'DOPE' --output_folder '_out_dope'")
    -- Replicator Composer tests
    -- FOR DEVELOPMENT -- 
    local nucleus_server = "ov-isaac-dev.nvidia.com"
    -- -- FOR PRODUCTION -- 
    -- local nucleus_server = "localhost"
    python_sample_test("tests-nativepython-replicator.composer.warehouse_1", "tools/composer/src/main.py", "--input parameters/warehouse.yaml --num-scenes 5 --headless --overwrite --nucleus-server "..nucleus_server)
    python_sample_test("tests-nativepython-replicator.composer.warehouse_2", "tools/composer/src/main.py", "--input parameters/warehouse.yaml --visualize-models --headless --overwrite --nucleus-server "..nucleus_server)
    python_sample_test("tests-nativepython-replicator.composer.flying_things_3d", "tools/composer/src/main.py", "--input parameters/flying_things_3d.yaml --num-scenes 5 --headless --overwrite --nucleus-server "..nucleus_server)
    python_sample_test("tests-nativepython-replicator.composer.flying_things_4d", "tools/composer/src/main.py", "--input parameters/flying_things_4d.yaml --num-scenes 1 --headless --overwrite --nucleus-server "..nucleus_server)
    
    -- tests that are not shipped
    python_sample_test("tests-internalnativepython-omni.isaac.core.test_time_stepping", "standalone_examples/testing/omni.isaac.core/test_time_stepping.py")
    python_sample_test("tests-internalnativepython-omni.isaac.core.test_save_stage", "standalone_examples/testing/omni.isaac.core/test_save_stage.py")
    python_sample_test("tests-internalnativepython-omni.isaac.core.test_delete_in_contact", "standalone_examples/testing/omni.isaac.core/test_delete_in_contact.py")
    python_sample_test("tests-internalnativepython-omni.isaac.core.test_articulation_determinism", "standalone_examples/testing/omni.isaac.core/test_articulation_determinism.py")
    python_sample_test("tests-internalnativepython-omni.isaac.dynamic_control.test_zero_step", "standalone_examples/testing/omni.isaac.dynamic_control/test_zero_step.py")
    python_sample_test("tests-internalnativepython-omni.isaac.ros2_bridge.enable_extension", "standalone_examples/testing/omni.isaac.ros2_bridge/enable_extension.py")
    python_sample_test("tests-internalnativepython-omni.isaac.ros2_bridge.test_carter_camera_multi_robot_nav", "standalone_examples/testing/omni.isaac.ros2_bridge/test_carter_camera_multi_robot_nav.py")
    python_sample_test("tests-internalnativepython-omni.isaac.statistics_logging.test_memory_leak", "standalone_examples/testing/omni.isaac.statistics_logging/test_memory_leak.py")
    python_sample_test("tests-internalnativepython-omni.isaac.kit.test_extra_args", "standalone_examples/testing/omni.isaac.kit/test_extra_args.py", '--/persistent/isaac/asset_root/default="omniverse://ov-test-this-is-working"')
    python_sample_test("tests-internalnativepython-omni.isaac.kit.test_ogn", "standalone_examples/testing/omni.isaac.kit/test_ogn.py")
    python_sample_test("tests-internalnativepython-omni.isaac.kit.test_syntheticdata", "standalone_examples/testing/omni.isaac.kit/test_syntheticdata.py")
    python_sample_test("tests-internalnativepython-omni.isaac.kit.test_fetch_results", "standalone_examples/testing/omni.isaac.kit/test_fetch_results.py")
    python_sample_test("tests-internalnativepython-omni.isaac.ros_bridge.test_carter_lidar", "standalone_examples/testing/omni.isaac.ros_bridge/test_carter_lidar.py")
    python_sample_test("tests-internalnativepython-omni.isaac.cortex.bringup", "exts/omni.isaac.cortex/omni/isaac/cortex/cortex_main.py", "--test --usd_env=omniverse://ov-isaac-dev.nvidia.com/Users/nratliff/cortex/blocks_world/cortex_blocks_world_belief_sim.usd")
    python_sample_test("tests-internalnativepython-omni.isaac.core.tensor_api_handles", "standalone_examples/testing/omni.isaac.core/tensor_api_handles.py")
    python_sample_test("tests-internalnativepython-omni.isaac.gym.test_gym_headless_app", "standalone_examples/testing/omni.isaac.gym/test_gym_headless_app.py")
    python_sample_test("tests-internalnativepython-omni.isaac.synthetic_utils.visualize_groundtruth", "standalone_examples/testing/omni.isaac.synthetic_utils/visualize_groundtruth.py")
    python_sample_test("tests-internalnativepython-omni.isaac.sensor.contact_sensor", "standalone_examples/testing/omni.isaac.sensor/contact_sensor_test.py")
    python_sample_test("tests-internalnativepython-python_sh.import_torch", "standalone_examples/testing/python_sh/import_torch.py")
    python_sample_test("tests-internalnativepython-omni.syntheticdata.test_basic", "standalone_examples/testing/omni.syntheticdata/test_basic.py")
    python_sample_test("tests-internalnativepython-omni.synthetic_utils.test_basic", "standalone_examples/testing/omni.synthetic_utils/test_basic.py")

    -- docker tests
    docker_test("tests-docker-simple", "simple.sh")
    docker_test("tests-docker-jupyter", "jupyter.sh")

group "jupyter_samples"

    jupyter_sample_test("tests-jupyter-startup", "standalone_examples/testing/notebooks/basic_notebook.ipynb")
    jupyter_sample_test("tests-jupyter-ogn", "standalone_examples/testing/notebooks/test_ogn_notebook.ipynb")
    jupyter_sample_test("tests-jupyter-syntheticdata", "standalone_examples/testing/notebooks/test_syntheticdata_notebook.ipynb")
