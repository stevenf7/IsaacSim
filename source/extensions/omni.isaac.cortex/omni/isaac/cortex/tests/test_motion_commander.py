# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.kit import SimulationApp
import numpy as np
import os
import sys
import time


def parse_args():
    import argparse

    node_name = "test_motion_commander"
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument(
        "--loop_fast",
        action="store_true",
        help="Usually uses a steady step of 60 hz. Setting " "this flag tells the system to step as fast as it can.",
    )
    parser.add_argument("--position_only", action="store_true", help="Contol only the position, not the orientation.")

    args = parser.parse_args()
    return args


args = parse_args()
simulation_app = SimulationApp({"headless": False})


from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage

from omni.isaac.cortex.cortex_utils import (
    add_cortex_attributes_to_robot,
    build_motion_commander,
    configure_robot,
    load_franka_to_stage,
    make_cortex_default_world,
    set_home_config,
    wrap_robot,
)
from omni.isaac.cortex.tools import write, SteadyRate, CycleTimer

import lula
import omni


def add_robot_to_world_and_configure(world):
    # Find the robot asset and add it to the stage.
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        print("Could not find Isaac Sim assets folder")
    asset_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
    robot_prim_path = "/cortex/belief/robot"
    add_reference_to_stage(usd_path=asset_path, prim_path=robot_prim_path)

    # Wrap the robot and add it to the scene.
    robot = world.scene.add(wrap_robot(domain="belief", robot_type="franka", prim_path=robot_prim_path))
    world.reset()  # Initialize the robot and dynamic control.

    # Configure the robot and add the appropriate cortex attributes.
    configure_robot(robot, verbose=True)
    set_home_config(robot)
    physics_dt = world.get_physics_dt()
    add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)
    world.reset()  # Set the robot to the initial config before building the motion commander.

    return robot


def main(args):
    world = make_cortex_default_world()

    robot = add_robot_to_world_and_configure(world)

    # Build the motion commander.
    obstacles = {}
    physics_dt = world.get_physics_dt()
    commander = build_motion_commander(physics_dt, robot, obstacles)

    if args.position_only:
        commander.set_target_position_only()

    print("<looping>")
    rate_hz = 1.0 / physics_dt
    rate = SteadyRate(rate_hz)
    cycle_timer = CycleTimer()

    # Main loop. Simply steps the world, resets when necessary (e.g. if the timeline was stopped then
    # restarted), and sends the latest commander action to the robot.
    while simulation_app.is_running():
        write(".")
        cycle_timer.tick()
        world.step(render=True)
        if world.is_playing():
            if world.current_time_step_index == 0:
                # Note if world.reset() has already been called (such as the first time through,
                # this section isn't entered (time step indices is greater than zero).
                write("\n<reset>")
                world.reset()

            action = commander.get_action()
            robot.get_articulation_controller().apply_action(action)
        else:
            is_first = True

        if not args.loop_fast:
            rate.sleep()
    print("|<complete>")


if __name__ == "__main__":
    try:
        main(args)
        print("<exiting successfully>")
    except Exception as e:
        print("Exception encountered:", e)
        import traceback

        traceback.print_exc()
        print("<shutdown initiated>")
    finally:
        simulation_app.close()
