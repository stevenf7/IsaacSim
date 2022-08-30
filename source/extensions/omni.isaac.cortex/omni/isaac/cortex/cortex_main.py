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

    node_name = "cortex launch"
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument(
        "--assets_root",
        type=str,
        default=None,
        help="Assets root path. If None (default), defaults to using the built it get_assets_root_path() helper which typically reports 'omniverse://localhost/NVIDIA/Assets/Isaac/2022.2' on most installations.",
    )
    parser.add_argument(
        "--usd_env",
        type=str,
        default="Isaac/Samples/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd",
        help="Relative path to the USD environment to load. This path will be relative to the --assets_root. By default, it points to the example Franka blocks world environment.",
    )
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
from omni.isaac.core import World
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import add_reference_to_stage, print_stage_prim_paths

from omni.isaac.cortex.cortex_utils import (
    add_cortex_attributes_to_objects,
    add_cortex_attributes_to_robot,
    build_motion_commander,
    configure_robot,
    find_assets_root_path_with_error_checks,
    make_core_objects,
    set_home_config,
    wrap_cortex_robot_or_die,
)
from omni.isaac.cortex.cortex_object import CortexObject
from omni.isaac.cortex.df_behavior_watcher import DfBehaviorWatcher
from omni.isaac.cortex.tools import SteadyRate, CycleTimer, Profiler


class ContextTools:
    """ The tools passed in to a behavior when build_behavior(tools) is called.
    """

    def __init__(self, world, objects, obstacles, robot, commander):
        self.world = world  # The World singleton.
        self.objects = objects  # The objects under /cortex/belief/objects as core API objects.
        self.obstacles = obstacles  # Those objects marked as obstacles.
        self.robot = robot  # The belief robot.
        self.commander = commander  # The motion commander.

    def enable_obstacles(self):
        """ Ensures the obstacles are enabled. This can be called by a behavior on construction. To
        reset any previous obstacle suppression.
        """
        for _, obs in self.obstacles.items():
            self.commander.enable_obstacle(obs)


def main():
    do_gains_hack = True

    print("<entering main>")

    print("<creating default empty world>")
    world = World()  # Creates the singleton world accessed both locally and by extensions.
    world.reset()  # Start up the simulation environment.
    if args.enable_ros:
        print("<enabling cortex ROS-based extensions>")
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_manager.set_extension_enabled_immediate("omni.isaac.cortex", True)

    # Establish the physics step size and corresponding cycle rate.
    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt

    if args.assets_root is not None:
        assets_root_path = args.assets_root
    else:
        assets_root_path = find_assets_root_path_with_error_checks()

    env_asset_path = assets_root_path + "/" + args.usd_env

    print("loading world from USD:", env_asset_path)
    add_reference_to_stage(usd_path=env_asset_path, prim_path="/cortex")
    if args.print_stage_prims_on_startup:
        print_stage_prim_paths()

    robot = wrap_cortex_robot_or_die(domain="belief")
    world.scene.add(robot)

    world.step()  # Step physics to trigger cortex_sim extension robot to be created.
    world.reset()  # Reset to setup all robot handles.

    configure_robot(robot, verbose=True)
    set_home_config(robot)
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)
    world.step()  # Trigger extensions to configure their robots

    #  Create core objects and add them to the scene.
    objects, obstacles = make_core_objects("belief")
    add_cortex_attributes_to_objects(objects)
    for name, obj in objects.items():
        world.scene.add(obj)

    print("obstacles:")
    for i, name in enumerate(obstacles):
        print("%d) obs: %s" % (i, name))

    # Reset then step the world to set all initial configurations of the robot and corresponding
    # child USD elements (e.g. cortex's eff frame which aligns with the RMPflow policy's
    # end-effector).
    world.reset()
    world.step(render=False)

    if do_gains_hack:
        # TODO: gains hack -- needs to be here until gains are no longer reset by calling world.reset().
        configure_robot(robot, verbose=True)

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
