# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import os
import carb
import signal
import json
import argparse

import time
from omni.isaac.python_app import OmniKitHelper

_omni = None
_kit = None


"""
This script acts as an example for how one can run the benchmark extension from a script.
This affords multiple advantages:
    Benchmarks run much faster from this script because most of Sim is not loaded.
        (once the assets are is loaded and kit has started up)
    Environment and MotionPolicy parameters can be changed programmatically between tests.
    Running from a script enables logging of test data for quantitative analysis

To run this script with Isaac Sim's python environment:
    /path/to/sim/_build/linux-x86_64/release/python.sh benchmarking_script.py 
"""


def get_test_assets(benchmark_config_util, env_name, robot_name, policy_name):
    robot_assets = benchmark_config_util.get_robot_assets(robot_name)

    env_kwargs = benchmark_config_util.get_environment_params(env_name, robot_name)

    default_policy_config = benchmark_config_util.get_default_policy_config(robot_name, policy_name)
    final_policy_config = benchmark_config_util.overwrite_default_policy_config(
        env_name, robot_name, policy_name, default_policy_config
    )

    return robot_assets, env_kwargs, final_policy_config


def run_test(test, num_frames, fps=60):
    for i in range(600):
        _kit.update(1.0 / fps)
        test.step(1.0 / fps)
        if i == 0:
            test.toggle_testing()


def reload_stage():
    while _kit.is_loading():
        _kit.update()

    _omni.usd.get_context().new_stage()
    _kit.play()


def main(args):
    CUSTOM_CONFIG = {
        "renderer": "RayTracedLighting",
        "headless": args.headless,
        "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    }

    kit = OmniKitHelper(config=CUSTOM_CONFIG)
    import omni

    # make kit and omni globals to make calling functions cleaner
    global _kit, _omni
    _kit = kit
    _omni = omni

    from omni.isaac.robot_benchmark.robot_benchmarking import RobotBenchmark
    from omni.isaac.robot_benchmark.benchmark_logger import BenchmarkLogger
    from omni.isaac.robot_benchmark.benchmark_utils import BenchmarkConfigUtility
    from omni.isaac.benchmark_environments.environments import EnvironmentCreator

    viewport = omni.kit.viewport_legacy.get_default_viewport_window()

    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_manager.set_extension_enabled_immediate("omni.isaac.robot_benchmark", True)
    ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_benchmark")
    benchmark_extension_path = ext_manager.get_extension_path(ext_id)

    ext_manager.set_extension_enabled_immediate("omni.isaac.motion_generation", True)
    mg_ext_id = ext_manager.get_enabled_extension_id("omni.isaac.motion_generation")
    mg_extension_path = ext_manager.get_extension_path(mg_ext_id)

    benchmark_config_util = BenchmarkConfigUtility(mg_extension_path, benchmark_extension_path)

    env_creator = EnvironmentCreator()

    benchmark_logger = BenchmarkLogger(os.path.join(benchmark_extension_path, "python/scripts", args.output_file))

    kit.play()
    benchmark = RobotBenchmark()

    """
    The following functions may be helpful when modifying this script
        env_creator.get_environment_names() gets a list of all environments
        benchmark_config_util.get_robot_options() gets a list of all robots
        benchmark_config_util.get_motion_policy_options(robot_name) gets a list of motion policies that have configs for the specified robot

        env_creator.get_motion_policy_exclusion_list(env_name) gets a list of motion_policies that are not recommended for the specific environment
        env_creator.get_robot_exclusion_list(env_name) gets a list of robots that are not recommended for the specific environment  
    """

    # Load assets necessary to initialize a benchmark test for a specific robot/environment/policy combination.
    robot_assets, env_config, motion_policy_config = get_test_assets(
        benchmark_config_util, "Cubby", "Franka", "RMPflow"
    )

    # overwrite environment/policy parameters if needed
    env_config["timeout"] = 600  # 600 frames = 10 seconds real time
    env_config["name"] = "Cubby2"  # Environment name is logged by the logger to help identify the specific test.
    motion_policy_config["evaluations_per_frame"] = 10

    env = env_creator.create_environment("Cubby", random_seed=0, **env_config)
    viewport.set_camera_position("/OmniverseKit_Persp", *env.camera_position, True)
    viewport.set_camera_target("/OmniverseKit_Persp", *env.camera_target, True)

    if env is not None:
        benchmark.initialize_test(env, robot_assets, motion_policy_config, benchmark_logger)
        run_test(benchmark, 600)
        reload_stage()  # makes it possible to initialize a new test

    robot_assets, env_config, motion_policy_config = get_test_assets(benchmark_config_util, "Cubby", "UR10", "RMPflow")
    env = env_creator.create_environment("Cubby", random_seed=0, **env_config)
    viewport.set_camera_position("/OmniverseKit_Persp", *env.camera_position, True)
    viewport.set_camera_target("/OmniverseKit_Persp", *env.camera_target, True)

    if env is not None:
        benchmark.initialize_test(env, robot_assets, motion_policy_config, benchmark_logger)
        run_test(benchmark, 600)

    # benchmark_logger stores data internally until this function is called and the data is written to a json file
    benchmark_logger.write_to_json()

    kit.stop()
    kit.shutdown()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-H", "--headless", help="run in headless mode (no GUI)", action="store_true", default=False)
    # The output filepath is a relative path, and it will be appended to the path for the benchmark extension
    parser.add_argument(
        "--output_file", help="destination of output file describing tests", default="./saved_tests/test_out.json"
    )

    args = parser.parse_args()

    main(args)
