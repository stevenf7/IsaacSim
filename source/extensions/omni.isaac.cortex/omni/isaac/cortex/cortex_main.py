# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import carb
import math
import numpy as np
import time
from typing import Optional

from omni.isaac.kit import SimulationApp


def setup_and_parse_known_args():
    import argparse

    node_name = "cortex"
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument("--usd_env", type=str, required=True, help="Path to the USD environment to load.")
    parser.add_argument(
        "--enable_ros",
        action="store_true",
        help="Enable cortex ROS-based extensions for communicating with physical robots.",
    )
    parser.add_argument("--position_only", action="store_true", help="Contol only the position, not the orientation.")
    parser.add_argument(
        "--loop_fast",
        action="store_true",
        help="Usually uses a steady step of 60 hz. Setting " "this flag tells the system to step as fast as it can.",
    )
    parser.add_argument(
        "--print_stage_prims_on_startup",
        action="store_true",
        help="Prints the stage prims when the environment is first loaded during startup.",
    )
    parser.add_argument(
        "--print_diagnostics", action="store_true", help="Print diagnostic information, including profiling info."
    )
    parser.add_argument(
        "--suppress_behaviors",
        action="store_true",
        help="If set, suppresses the behaviors. Useful for diagnosing issues.",
    )
    parser.add_argument(
        "--test", action="store_true", help="Run a simple bringup test to make sure the cortex system starts."
    )

    args, _ = parser.parse_known_args()
    return args


args = setup_and_parse_known_args()
simulation_app = SimulationApp({"headless": False})


import omni
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import add_reference_to_stage, print_stage_prim_paths

from omni.isaac.cortex.cortex_utils import (
    add_cortex_attributes_to_objects_if_needed,
    add_cortex_attributes_to_robot,
    build_motion_commander,
    configure_robot,
    make_core_objects,
    make_empty_world,
    set_home_config,
    wrap_cortex_robot_or_die,
)
from omni.isaac.cortex.cortex_object import CortexObject
from omni.isaac.cortex.df_behavior_watcher import DfBehaviorWatcher
from omni.isaac.cortex.tools import SteadyRate, CycleTimer, Profiler


class ContextTools:
    def __init__(self, world, objects, obstacles, robot, commander):
        self.world = world
        self.objects = objects
        self.obstacles = obstacles
        self.robot = robot
        self.commander = commander


def main():
    print("<entering main>")

    if args.enable_ros:
        print("<enabling cortex ROS-based extensions>")
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_manager.set_extension_enabled_immediate("omni.isaac.cortex", True)

    world = make_empty_world()

    # Establish the physics step size and corresponding cycle rate.
    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt

    print("loading world from USD:", args.usd_env)
    add_reference_to_stage(usd_path=args.usd_env, prim_path="/cortex")
    if args.print_stage_prims_on_startup:
        print_stage_prim_paths()

    robot = wrap_cortex_robot_or_die(domain="belief")
    world.scene.add(robot)
    world.reset()

    configure_robot(robot, verbose=True)
    set_home_config(robot)
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)

    #  Create core objects and add them to the scene.
    objects, obstacles = make_core_objects("belief")
    add_cortex_attributes_to_objects_if_needed(objects)
    for name, obj in objects.items():
        world.scene.add(obj)

    print("obstacles:")
    for i, name in enumerate(obstacles):
        print("%d) obs: %s" % (i, name))

    # Make sure reset before creating the motion commander to get the robots to the right
    # configuration so the measured end-effector pose is in the right place.
    world.reset()

    # TODO: figure out why we need to do an extra step to sync the ee_link USD. If we don't do this,
    # the transform we read for ee_link in UR10 is still the default zero config, so it adds the eff
    # prim in the wrong place. This has only been verified with UR10 -- Franka's underlying USD env
    # already has the robot in the correct retracted config. If this is just the way it works, we
    # should add the world.reset() and world.step() to set_home_config() to hide these details.
    world.step(render=False)

    commander = build_motion_commander(physics_dt, robot, obstacles)
    if args.position_only:
        commander.set_target_position_only()

    context_tools = ContextTools(world, objects, obstacles, robot, commander)
    df_behavior_watcher = DfBehaviorWatcher(verbose=True)

    print("<looping>")
    rate = SteadyRate(rate_hz)
    cycle_timer = CycleTimer()

    robot_prim = get_prim_at_path(robot.prim_path)
    needs_reset = False

    profiler = Profiler(name="cortex_loop_runner", alpha=0.99, skip_cycles=100)

    start_time = time.time()
    while simulation_app.is_running():
        cycle_timer.tick()
        profiler.start_cycle()

        if world.is_playing():
            if world.current_time_step_index == 0:
                world.reset()

            if not args.suppress_behaviors:
                is_suppressed = robot_prim.GetAttribute("cortex:is_suppressed").Get()
                if is_suppressed:
                    print("<cortex suppressed>")
                    needs_reset = True
                else:
                    # This signal of the attribute no longer being set is set by the ROS cortex extension in
                    # the world.step() method below. This section runs after that, so the robot's joints
                    # will already be set to the right things.
                    if needs_reset:
                        print("<cortex resetting>")
                        context_tools.commander.reset()
                        needs_reset = False

                    df_behavior_watcher.check_reload(context_tools)
                    try:
                        profiler.start_capture("behavior")
                        df_behavior_watcher.tick_behavior()
                        profiler.end_capture("behavior")
                    except Exception as e:
                        print("\nProblem ticking behavior.")
                        import traceback

                        traceback.print_exc()

                    # Retrieve the latest action specified by the target prim.
                    action = context_tools.commander.get_action()
                    robot.get_articulation_controller().apply_action(action)

        profiler.start_capture("world_and_task_step")
        world.step(step_sim=False)
        profiler.end_capture("world_and_task_step")

        profiler.start_capture("sim_step")
        SimulationContext.step(world, render=False)
        profiler.end_capture("sim_step")

        profiler.start_capture("render")
        world.render()
        profiler.end_capture("render")

        profiler.end_cycle()
        if args.print_diagnostics:
            profiler.print_report(max_rate_hz=rate_hz)

        if not args.loop_fast:
            rate.sleep()

        if args.test:
            if time.time() - start_time > 2.0:
                print("[Test successful. Shutting down.]")
                break


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nException caught.")
        import traceback

        traceback.print_exc()
    finally:
        simulation_app.close()
        print("<done>")
