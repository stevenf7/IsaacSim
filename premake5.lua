-- Shared build scripts from repo_build package
repo_build = require("omni/repo/build")

-- Repo root
root = repo_build.get_abs_path(".")

-- Shared build scripts from repo_build package
no_compile_commands_file = false

-- -- Include Kit SDK public premake, it defines few global variables and helper functions. Look inside to get more info.
-- local build_path = root.."/_build/"..os.target().."-x86_64/"

-- if os.isfile(build_path.."release/kit/dev/premake5-public.lua") then
--     kit_sdk = build_path.."release/kit"
--     dofile(build_path.."release/kit/dev/premake5-public.lua")
-- else
--     kit_sdk = build_path.."debug/kit"
--     dofile(build_path.."debug/kit/dev/premake5-public.lua")
-- end

-- -- Setup where to write generate prebuild.toml file
-- repo_build.set_prebuild_file('_build/generated/prebuild.toml')

function workspace_build_settings()
    -- Default compilation settings
    symbols "On"
    exceptionhandling "On"
    rtti "On"
    staticruntime "On"
    flags { "FatalCompileWarnings", "MultiProcessorCompile", "NoPCH", "NoIncrementalLink" }
    cppdialect "C++17"

    -- Debug configuration settings
    filter { "configurations:debug" }
        defines { "_DEBUG" }
        optimize "Off"

    -- Release configuration settings
    filter  { "configurations:release" }
        defines { "NDEBUG" }
        optimize "Speed"

    filter {}

    -- Windows platform settings
    filter { "system:windows" }
        platforms { "x86_64" }
        toolset "v142"

        -- Add .editorconfig to all projects so that VS 2017 automatically picks it up
        files {".editorconfig"}
        editandcontinue "Off"

        -- Enable usage of brought up toolchain
        setup_msvc_toolchain()

        -- All of our source strings and executable strings are utf8
        buildoptions {"/utf-8", "/bigobj"}
        buildoptions {"/permissive-", "/Zc:externC-"}
        -- The /Zc:inline option strips out the "arch_ctor_<name>" symbols, so disable it.
        -- See https://groups.google.com/g/usd-interest/c/nWm7u3B6CQk/m/OvIkOIyAAwAJ
        -- NOTE: This will give warnings for this project. According to premake docs, the removeunreferencedcodedata
        -- command should be used instead, but it doesn't appear until premake5.0.0-alpha16 and even then it doesn't
        -- work correctly. https://premake.github.io/docs/removeunreferencedcodedata/
        buildoptions { "/Zc:inline-" }

        -- define this everywhere to prevent 'pyerrors.h' from defining silly things like 'vsnprintf'
        -- and 'snprintf'.
        defines { "HAVE_SNPRINTF", "HAVE_COPYSIGN", "_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS" }
        undefines { "_copysign" }


    -- Linux platform settings
    filter { "system:linux" }
        platforms { "x86_64" }
        defaultplatform "x86_64"
        disablewarnings {"error=unused-function"}
        buildoptions { "-fvisibility=hidden -D_FILE_OFFSET_BITS=64" }

        -- Add library origin directory to dlopen() search path
        linkoptions { "-Wl,-rpath,'$$ORIGIN' -Wl,--export-dynamic" }

        enablewarnings { "all" }

    filter {}

    -- repo_build.enable_sanitizers()
end

function workspace_kit_settings()
    -- Setup include paths. Add kit SDK include paths too.
    includedirs {
        "include",
        targetDepsDir,
        targetDepsDir.."/pybind11/include",
        carbSDKInclude,
        kit_sdk.."/include",
        kit_sdk.."/_build/target-deps/",
        kit_dev_dir.."/include",
    }

    -- Carbonite carb lib
    libdirs {
        carbSDKLibs,
        carbSDKLibs.."/scripting-python-3.10",
        "%{kit_sdk}/plugins"
    }
end

function setup_common_folder_links()
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

        repo_build.prebuild_link {
            { "source/python_packages", "_build/%{platform}/%{config}/python_packages" },
            { "source/standalone_examples", "_build/%{platform}/%{config}/standalone_examples" },
            { "source/tools", "_build/%{platform}/%{config}/tools"},
            { "_build/target-deps/omni_physics/_build/%{platform}/%{config}/extsPhysics", "_build/%{platform}/%{config}/extsPhysics"},
        }

        if os.target() == "linux" then
            repo_build.prebuild_link {
                { "source/scripts/python/linux-x86_64/icon", "_build/%{platform}/%{config}/data/icon" },
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
            {"source/scripts/omni.isaac.sim.post.install.run${shell_ext}",  "_build/%{platform}/%{config}"},
            {"source/scripts/omni.isaac.sim.warmup${shell_ext}",  "_build/%{platform}/%{config}"},
            {"source/scripts/isaac-sim.docker*${shell_ext}",  "_build/%{platform}/%{config}"},
            {"source/apps/omni.isaac.sim.python.kit",  "_build/%{platform}/%{config}/apps"},
            {"source/scripts/vscode/%{platform}",  "_build/%{platform}/%{config}/.vscode"},
            {"source/scripts/telemetry/*",  "_build/%{platform}/%{config}/config"},
        }
end

function include_extensions()
        -- Isaac Extensions
    group "exts"

    -- Windows and Linux
    include ("source/extensions/omni.isaac.app.setup")
    include ("source/extensions/omni.isaac.app.selector")
    include ("source/extensions/omni.isaac.articulation_inspector")
    include ("source/extensions/omni.isaac.camera_inspector")
    include ("source/extensions/omni.isaac.assets_check")
    include ("source/extensions/omni.isaac.benchmark_environments")
    include ("source/extensions/omni.isaac.benchmark.services")
    include ("source/extensions/omni.isaac.benchmarks")
    include ("source/extensions/omni.isaac.block_world")
    include ("source/extensions/omni.isaac.gym.benchmark")
    include ("source/extensions/omni.isaac.cloner")
    include ("source/extensions/omni.isaac.robot_description_editor")
    include ("source/extensions/omni.isaac.core")
    include ("source/extensions/omni.isaac.core_archive")
    include ("source/extensions/omni.isaac.core_nodes")
    include ("source/extensions/omni.isaac.cortex")
    include ("source/extensions/omni.isaac.cortex.sample_behaviors")
    include ("source/extensions/omni.isaac.conveyor")
    include ("source/extensions/omni.isaac.conveyor.ui")
    include ("source/extensions/omni.isaac.diff_usd")
    include ("source/extensions/omni.isaac.debug_draw")
    include ("source/extensions/omni.isaac.doctest")
    include ("source/extensions/omni.isaac.dofbot")
    include ("source/extensions/omni.isaac.dynamic_control")
    include ("source/extensions/omni.isaac.examples")
    include ("source/extensions/omni.isaac.examples_nodes")
    include ("source/extensions/omni.isaac.extension_templates")
    include ("source/extensions/omni.isaac.franka")
    include ("source/extensions/omni.isaac.manipulators")
    include ("source/extensions/omni.isaac.manipulators.ui")
    include ("source/extensions/omni.isaac.gain_tuner")
    include ("source/extensions/omni.isaac.gym")
    include ("source/extensions/omni.isaac.import_wizard")
    include ("source/extensions/omni.isaac.internal_tools")
    include ("source/extensions/omni.isaac.sensor")
    include ("source/extensions/omni.isaac.kit")
    include ("source/extensions/omni.isaac.lula")
    include ("source/extensions/omni.isaac.lula_test_widget")
    include ("source/extensions/omni.isaac.merge_mesh")
    include ("source/extensions/omni.isaac.ml_archive")
    include ("source/extensions/omni.isaac.motion_generation")
    include ("source/extensions/omni.isaac.nucleus")
    include ("source/extensions/omni.isaac.occupancy_map")
    include ("source/extensions/omni.isaac.occupancy_map.ui")
    include ("source/extensions/omni.isaac.partition")
    include ("source/extensions/omni.isaac.proximity_sensor")
    include ("source/extensions/omni.isaac.physics_inspector")
    include ("source/extensions/omni.isaac.physics_utilities")
    include ("source/extensions/omni.isaac.quadruped")
    include ("source/extensions/omni.isaac.range_sensor")
    include ("source/extensions/omni.isaac.range_sensor.ui")
    include ("source/extensions/omni.isaac.range_sensor.examples")
    include ("source/extensions/omni.isaac.robot_benchmark")
    include ("source/extensions/omni.isaac.robot_assembler")
    include ("source/extensions/omni.isaac.surface_gripper")
    include ("source/extensions/omni.isaac.surface_gripper.ui")
    include ("source/extensions/omni.isaac.synthetic_recorder")
    include ("source/extensions/omni.isaac.tests")
    include ("source/extensions/omni.isaac.throttling")
    include ("source/extensions/omni.isaac.universal_robots")
    include ("source/extensions/omni.isaac.utils")
    include ("source/extensions/omni.isaac.ui")
    include ("source/extensions/omni.isaac.ui_template")
    include ("source/extensions/omni.isaac.unit_converter")
    include ("source/extensions/omni.isaac.vscode")

    include ("source/extensions/omni.isaac.wheeled_robots")
    include ("source/extensions/omni.isaac.wheeled_robots.ui")

    include ("source/extensions/omni.isaac.window.about")
    include ("source/extensions/omni.kit.property.isaac")
    include ("source/extensions/omni.kit.loop-isaac")
    include ("source/extensions/omni.usd.schema.isaac")
    include ("source/extensions/omni.isaac.asset_browser")
    include ("source/extensions/omni.isaac.version")
    include ("source/extensions/omni.replicator.isaac")
    include ("source/extensions/omni.isaac.ros2_bridge")
    include ("source/extensions/omni.isaac.scene_blox")
    include ("source/extensions/omni.pip.compute")
    include ("source/extensions/omni.pip.cloud")
    include ("source/extensions/omni.exporter.urdf")
    include ("source/extensions/omni.isaac.menu")

    -- Linux Only
    if os.target() == "linux" then
        include ("source/extensions/omni.isaac.benchmarks")
        include ("source/extensions/omni.isaac.gym.benchmark")
        include ("source/extensions/omni.isaac.repl")
        include ("source/extensions/omni.isaac.cortex_sync")
        include ("source/extensions/omni.isaac.ocs2")
        include ("source/extensions/omni.isaac.ros_bridge")
    end
end

function write_version_file(config)
    if os.target() == "windows" then
        local dir = root.."/_build/windows-x86_64/"..config
        if os.isdir(dir) then
            local file = io.open(root.."/VERSION", "r")
            local ver_str = file:read("*a")
            file:close()

            file = io.open(dir.."/SHORT_VERSION", "w")
            file:write(ver_str)
            file:close()

            local cmd = "repo.bat build_number -o "..dir.."/VERSION"
            os.execute(get_current_lua_file_dir().."/"..cmd)
        end
    else
        local dir = root.."/_build/linux-x86_64/"..config
        if os.isdir(dir) then
            local cmd = "./repo.sh build_number -o "..dir.."/VERSION"
            os.execute(get_current_lua_file_dir().."/"..cmd)
        end
    end

end

function get_git_info(params, env_var)
    local val = os.getenv(env_var)
    if val ~= nil then
        return val
    end

    local str = nil
    local cmd = "git "..params

    local proc = io.popen(cmd)
    if proc then
        str = proc:read("*a")
        local success, what, code = proc:close()
        if success then
            str = string.explode(str, "\n")[1]
        else
            str = nil
        end
    end

    if str == nil then
        str = "MISSING "..env_var
    else
        print (env_var.." "..str)
    end
    return str
end

function generate_version_header()
    shortSha = get_git_info("rev-parse --short HEAD", "ISAACSIM_BUILD_SHA")
    commitDate = get_git_info("show -s --format=\"%ad\"", "ISAACSIM_BUILD_DATE")
    branch = get_git_info("rev-parse --abbrev-ref HEAD", "ISAACSIM_BUILD_BRANCH")
    version = get_git_info("show HEAD:VERSION", "ISAACSIM_BUILD_VERSION")
    print("Generating version header file: "..branch.." "..shortSha.." "..version.." "..commitDate)

    os.mkdir("_build/generated/include/isaacSim")
    local new_text = "#pragma once\n#define ISAACSIM_BUILD_SHA \""..shortSha.."\"\n#define ISAACSIM_BUILD_DATE \""..commitDate.."\"\n#define ISAACSIM_BUILD_BRANCH \""..branch.."\"\n#define ISAACSIM_BUILD_VERSION \""..version.."\"\n"

    local file = io.open("_build/generated/include/isaacSim/Version.h", "r")
    local old_text = ""
    if file then
        old_text = file:read "*all"
        file:close()
    end

    -- if we overwrite Version.h with identical content, anything including that header will always get rebuilt
    -- let's try to avoid that
    if old_text and new_text == old_text then
        return
    end

    file = io.open("_build/generated/include/isaacSim/Version.h", "w")
    file:write(new_text)
    file:close(file)
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

function create_tests()
    group "startup_tests"
        -- use "--/app/settings/persistent=0 --/app/settings/loadUserConfig=0" to ignore config user config file
        -- use "--reset-user" to reset user config file
        define_startup_experience("tests-startup.main", "omni.isaac.sim", "--/app/quitAfter=500 --/app/file/ignoreUnsavedOnExit=1")
        define_startup_experience("tests-startup.webrtc", "omni.isaac.sim.headless.webrtc", "--no-window --/app/quitAfter=500 --/app/file/ignoreUnsavedOnExit=1")
        define_startup_experience("tests-startup.native", "omni.isaac.sim.headless.native", "--no-window --/app/quitAfter=500 --/app/file/ignoreUnsavedOnExit=1")
        define_startup_experience("tests-startup.extscache", "omni.isaac.sim", "--no-window --/app/quitAfter=500 --/app/extensions/registryEnabled=0 --/app/file/ignoreUnsavedOnExit=1")
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

    group "python_samples"
        -- smoke tests for python.sh itself
        python_script_test("tests-nativepython-pip_list", "-m pip list --")
        python_script_test("tests-nativepython-pycocotools", "-m pip install --force pycocotools --no-cache-dir --no-dependencies --") -- this test makes sure that pip packages that need Python.h can be installed.
        -- omni.kit.app
        python_sample_test("tests-nativepython-omni.kit.app.app_framework", "standalone_examples/api/omni.kit.app/app_framework.py")
        -- omni.isaac.kit
        python_sample_test("tests-nativepython-omni.isaac.kit.hello_world", "standalone_examples/api/omni.isaac.kit/hello_world.py")
        python_sample_test("tests-nativepython-omni.isaac.kit.change_resolution", "standalone_examples/api/omni.isaac.kit/change_resolution.py")
        python_sample_test("tests-nativepython-omni.isaac.kit.load_stage", "standalone_examples/api/omni.isaac.kit/load_stage.py", "--usd_path /Isaac/Environments/Simple_Room/simple_room.usd --test --headless")
        -- omni.isaac.cloner
        python_sample_test("tests-nativepython-omni.isaac.cloner.clone_ants", "standalone_examples/api/omni.isaac.cloner/clone_ants.py")
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
        -- omni.isaac.sensor
        python_sample_test("tests-nativepython-omni.isaac.sensor.rotating_lidar_rtx", "standalone_examples/api/omni.isaac.sensor/rotating_lidar_rtx.py", "--test")
        python_sample_test("tests-nativepython-omni.isaac.sensor.rotating_lidar_physX", "standalone_examples/api/omni.isaac.sensor/rotating_lidar_physX.py", "--test")
        -- omni.isaac.manipulators
        python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.follow_target_example", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/follow_target_example.py", "--test")
        python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.pick_up_example", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/pick_up_example.py", "--test")
        python_sample_test("tests-nativepython-omni.isaac.manipulators.cobotta_900.gripper_control", "standalone_examples/api/omni.isaac.manipulators/cobotta_900/gripper_control.py", "--test")
        python_sample_test("tests-nativepython-omni.isaac.manipulators.franka_pick_up", "standalone_examples/api/omni.isaac.manipulators/franka_pick_up.py", "--test")
        python_sample_test("tests-nativepython-omni.isaac.manipulators.ur10_pick_up", "standalone_examples/api/omni.isaac.manipulators/ur10_pick_up.py", "--test")
        -- omni.isaac.jetbot
        python_sample_test("tests-nativepython-omni.isaac.jetbot.jetbot_move", "standalone_examples/api/omni.isaac.jetbot/jetbot_move.py", "--test")
        -- omni.isaac.dynamic_control
        python_sample_test("tests-nativepython-omni.isaac.dynamic_control.franka_articulation", "standalone_examples/api/omni.isaac.dynamic_control/franka_articulation.py")
        -- omni.isaac.urdf
        python_sample_test("tests-nativepython-omni.isaac.urdf.urdf_import", "standalone_examples/api/omni.importer.urdf/urdf_import.py")
        -- omni.isaac.ros_bridge
        python_sample_test("tests-nativepython-omni.isaac.ros_bridge.clock", "standalone_examples/api/omni.isaac.ros_bridge/clock.py", "--test")
        -- python_sample_test("tests-nativepython-omni.isaac.ros_bridge.contact", "standalone_examples/api/omni.isaac.ros_bridge/contact.py") # disabling as this requires isaac sim custom message to be sourced, which doesn't work on TC
        python_sample_test("tests-nativepython-omni.isaac.ros_bridge.carter_stereo", "standalone_examples/api/omni.isaac.ros_bridge/carter_stereo.py", "--test")
        -- Replicator data samples:
        python_sample_test("tests-nativepython-replicator.offline_generation", "standalone_examples/replicator/offline_generation/offline_generation.py")
        python_sample_test("tests-nativepython-replicator.offline_generation_basic_writer", "standalone_examples/replicator/offline_generation/offline_generation.py", "--config standalone_examples/replicator/offline_generation/config/config_basic_writer.yaml")
        python_sample_test("tests-nativepython-replicator.offline_generation_default_writer", "standalone_examples/replicator/offline_generation/offline_generation.py", "--config standalone_examples/replicator/offline_generation/config/config_default_writer.json")
        python_sample_test("tests-nativepython-replicator.offline_generation_kitti_writer", "standalone_examples/replicator/offline_generation/offline_generation.py", "--config standalone_examples/replicator/offline_generation/config/config_kitti_writer.yaml")
        python_sample_test("tests-nativepython-replicator.offline_pose_generation", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py")
        python_sample_test("tests-nativepython-replicator.offline_pose_generation_ycbvideo", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--num_mesh 3 --num_dome 3 --writer YCBVideo --output_folder _out_ycb")
        python_sample_test("tests-nativepython-replicator.offline_pose_generation_ycbvideo_output_check", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--test --writer YCBVideo --output_folder _out_ycb_test")
        python_sample_test("tests-nativepython-replicator.offline_pose_generation_dope", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--num_mesh 3 --num_dome 3 --writer DOPE --output_folder _out_dope")
        python_sample_test("tests-nativepython-replicator.offline_pose_generation_dope_output_check", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py", "--test --writer DOPE --output_folder _out_dope_test")
        python_sample_test("tests-nativepython-replicator.writer_augmentation_numpy", "standalone_examples/replicator/augmentation/writer_augmentation.py", "--num_frames 1")
        python_sample_test("tests-nativepython-replicator.writer_augmentation_warp", "standalone_examples/replicator/augmentation/writer_augmentation.py", "--num_frames 1 --use_warp")
        python_sample_test("tests-nativepython-replicator.annotator_augmentation_numpy", "standalone_examples/replicator/augmentation/annotator_augmentation.py", "--num_frames 1")
        python_sample_test("tests-nativepython-replicator.annotator_augmentation_warp", "standalone_examples/replicator/augmentation/annotator_augmentation.py", "--num_frames 1 --use_warp")
        python_sample_test("tests-nativepython-replicator.amr_navigation", "standalone_examples/replicator/amr_navigation.py", "--num_frames 3 --env_interval 1")
        python_sample_test("tests-nativepython-replicator.amr_navigation_use_temp_rp", "standalone_examples/replicator/amr_navigation.py", "--num_frames 3 --env_interval 1 --use_temp_rp")
        -- tests that are not shipped
        python_sample_test("tests-internalnativepython-omni.isaac.core.hello_world", "standalone_examples/testing/omni.isaac.core/hello_world.py", "--test")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_time_stepping", "standalone_examples/testing/omni.isaac.core/test_time_stepping.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_articulation_root", "standalone_examples/testing/omni.isaac.core/test_articulation_root.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_rendering", "standalone_examples/testing/omni.isaac.core/test_rendering.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_save_stage", "standalone_examples/testing/omni.isaac.core/test_save_stage.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_delete_in_contact", "standalone_examples/testing/omni.isaac.core/test_delete_in_contact.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.test_articulation_determinism", "standalone_examples/testing/omni.isaac.core/test_articulation_determinism.py")
        python_sample_test("tests-internalnativepython-omni.isaac.dynamic_control.test_zero_step", "standalone_examples/testing/omni.isaac.dynamic_control/test_zero_step.py")
        python_sample_test("tests-internalnativepython-omni.isaac.ros2_bridge.enable_extension", "standalone_examples/testing/omni.isaac.ros2_bridge/enable_extension.py")
        python_sample_test("tests-internalnativepython-omni.isaac.ros2_bridge.test_carter_camera_multi_robot_nav", "standalone_examples/testing/omni.isaac.ros2_bridge/test_carter_camera_multi_robot_nav.py")
        python_sample_test("tests-internalnativepython-omni.isaac.ros2_bridge.test_people_sim", "standalone_examples/testing/omni.isaac.ros2_bridge/test_people_sim.py")
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_extra_args", "standalone_examples/testing/omni.isaac.kit/test_extra_args.py", '--/persistent/isaac/asset_root/default="omniverse://ov-test-this-is-working"')
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_ogn", "standalone_examples/testing/omni.isaac.kit/test_ogn.py")
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_syntheticdata", "standalone_examples/testing/omni.isaac.kit/test_syntheticdata.py")
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_fetch_results", "standalone_examples/testing/omni.isaac.kit/test_fetch_results.py")
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_unsaved_on_exit", "standalone_examples/testing/omni.isaac.kit/test_unsaved_on_exit.py")
        python_sample_test("tests-internalnativepython-omni.isaac.kit.test_external", "standalone_examples/testing/omni.isaac.kit/test_external.py", '--enable omni.kit.scripting')
        python_sample_test("tests-internalnativepython-omni.isaac.ros_bridge.test_carter_lidar", "standalone_examples/testing/omni.isaac.ros_bridge/test_carter_lidar.py", "--test")
        python_sample_test("tests-internalnativepython-omni.isaac.cortex.bringup", "standalone_examples/testing/omni.isaac.cortex/cortex_bringup_test.py")
        python_sample_test("tests-internalnativepython-omni.isaac.core.tensor_api_handles", "standalone_examples/testing/omni.isaac.core/tensor_api_handles.py")
        python_sample_test("tests-internalnativepython-omni.isaac.gym.test_gym_headless_app", "standalone_examples/testing/omni.isaac.gym/test_gym_headless_app.py")
        python_sample_test("tests-internalnativepython-omni.isaac.sensor.contact_sensor", "standalone_examples/testing/omni.isaac.sensor/contact_sensor_test.py")
        python_sample_test("tests-internalnativepython-omni.isaac.sensor.camera_opencv_fisheye", "standalone_examples/api/omni.isaac.sensor/camera_opencv_fisheye.py")
        python_sample_test("tests-internalnativepython-omni.isaac.sensor.camera_opencv", "standalone_examples/api/omni.isaac.sensor/camera_opencv.py")
        python_sample_test("tests-internalnativepython-python_sh.import_torch", "standalone_examples/testing/python_sh/import_torch.py")
        python_sample_test("tests-internalnativepython-python_sh.import_scipy", "standalone_examples/testing/python_sh/import_scipy.py")
        python_sample_test("tests-internalnativepython-python_sh.path_length", "standalone_examples/testing/python_sh/path_length.py")
        python_sample_test("tests-internalnativepython-python_sh.import_sys", "standalone_examples/testing/python_sh/import_sys.py")
        python_sample_test("tests-internalnativepython-omni.syntheticdata.test_basic", "standalone_examples/testing/omni.syntheticdata/test_basic.py")
        python_sample_test("tests-internalnativepython-omni.isaac.snippets.multi-camera", "standalone_examples/testing/omni.isaac.snippets/multi-camera.py")
        python_sample_test("tests-internalnativepython-omni.isaac.snippets.simulation_get_data", "standalone_examples/testing/omni.isaac.snippets/simulation_get_data.py")

    group "jupyter_samples"

        jupyter_sample_test("tests-jupyter-startup", "standalone_examples/testing/notebooks/basic_notebook.ipynb")
        jupyter_sample_test("tests-jupyter-ogn", "standalone_examples/testing/notebooks/test_ogn_notebook.ipynb")
        jupyter_sample_test("tests-jupyter-syntheticdata", "standalone_examples/testing/notebooks/test_syntheticdata_notebook.ipynb")

    if os.target() == "linux" then
    group "docker_tests"

        docker_test("tests-internaldocker-simple", "./dockertests/simple.sh")
        docker_test("tests-internaldocker-headless-native", "./isaac-sim.headless.native.sh", "--allow-root --/app/quitAfter=10")
        -- docker_test("tests-internaldocker-headless-webrtc", "./isaac-sim.headless.webrtc.sh", "--allow-root --/app/quitAfter=10")
        -- docker_test("tests-internaldocker-python-livestream", "./python.sh", "standalone_examples/api/omni.isaac.kit/livestream.py --/app/quitAfter=500")
        -- docker_test("tests-internaldocker-jupyter", "./dockertests/jupyter.sh")
        docker_test("tests-internaldocker-python-asset_usd_converter", "./python.sh", "standalone_examples/api/omni.kit.asset_converter/asset_usd_converter.py --folders standalone_examples/data/cube standalone_examples/data/torus")
        -- docker_test("tests-internaldocker-python-offline_pose_generation", "./python.sh", "standalone_examples/replicator/offline_pose_generation/offline_pose_generation.py --writer dope --num_dome 5 --num_mesh 5 --no-window")
    end
end

function group_apps()
    group "apps"
    for _, config in ipairs(ALL_CONFIGS) do
        -- Direct shortcur to kit executable for convenience:
        -- create_experience_runner("kit", nil, config, "")

        -- Put build version file into build directories
        write_version_file(config)
    end

    define_local_experience("isaac-sim", "omni.isaac.sim")
    define_local_experience("isaac-sim.gym", "omni.isaac.sim.gym")
    define_local_experience("isaac-sim.fabric", "omni.isaac.sim.fabric")
    define_local_experience("isaac-sim.selector", "omni.isaac.sim.selector")
    define_local_experience("isaac-sim.headless.native", "omni.isaac.sim.headless.native", "--no-window ")
    define_local_experience("isaac-sim.headless.webrtc", "omni.isaac.sim.headless.webrtc", "--no-window ")
    -- Windows Only
    if os.target() == "windows" then
        define_local_experience("isaac-sim.xr.steamvr", "omni.isaac.sim.xr.steamvr")
    end
end

nvccPath = path.getabsolute("_build/target-deps/cuda/bin/nvcc");
filter { "system:windows" }
    nvccHostCompilerVS =  path.getabsolute("_build/host-deps/msvc/VC");
filter {}
-- -- Insert kit template premake configuration, it creates solution, finds extensions.. Look inside for more details.
-- dofile("_repo/deps/repo_kit_tools/kit-template/premake5.lua")
-- mostly so outside code knows we are building isaac-sim
building_for_isaac_sim = true
defines { "BUILDING_FOR_ISAAC_SIM" }

kit = require(root.."/_repo/deps/repo_kit_tools/kit-template/premake5-kit")
-- kit.setup_all()
kit.include_kit()
-- kit.random_hacks()
kit.define_workspace() -- creates workspace

targetDepsDir = "%{root}/_build/target-deps"
hostDepsDir = "%{root}/_build/host-deps"
carbSDKPath = targetDepsDir.."/carb_sdk_plugins"
carbSDKInclude = carbSDKPath.."/include"
carbSDKLibs = carbSDKPath.."/_build/"..platform.."/%{config}"
    -- Workspace setup
    kit.workspace_basics()
        -- objdir ("_build/obj/%{prj.name}")

    -- kit.workspace_build_settings()
    workspace_build_settings()
    -- kit.workspace_kit_settings()
    workspace_kit_settings()
    -- kit.setup_toolchain()
    generate_version_header()

    -- Common settings for kit-based apps and extensions
    -- kit.setup_common_folder_links()
    setup_common_folder_links()
    kit.setup_kit_autopull()
    
    include("isaac_sim_premake5.lua") -- Shared build scripts from isaac sim
    -- kit.autoinclude_extensions()
    include_extensions()
    -- kit.group_apps()
    group_apps()
    create_tests()

    -- Use the tool to create extra tests if needed.
    -- Currently, it only supports creating the launcher startup test.
    -- execute_repo_tool("create_extra_test")


--
