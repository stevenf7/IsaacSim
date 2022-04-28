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
    parser.add_argument(
        "--test_loading_franka_from_basic_env",
        action="store_true",
        help="Load the franka into the stage, then creates the wrapping object referencing that one.",
    )
    parser.add_argument(
        "--test_loading_franka_from_cortex_env",
        action="store_true",
        help="Load the franka and initializes it for cortex in the stage, then does it againt to wrap that one.",
    )

    args = parser.parse_args()
    return args


args = parse_args()
simulation_app = SimulationApp(
    {"experience": f'{os.environ["EXP_PATH"]}/omni.isaac.cortex.python.kit', "headless": False}
)

from cortex_utils import (
    make_target_prim,
    add_end_effector_prim_to_franka,
    build_motion_commander,
    configure_franka,
    add_cortex_attributes_to_robot,
    load_cortex_default_world,
    make_franka,
    add_cortex_franka_to_world,
)
from tools import write, SteadyRate, CycleTimer

import lula
import omni


def main(args):
    # Load the default world and cortex franka.
    world = load_cortex_default_world()
    if args.test_loading_franka_from_basic_env:
        make_franka(load_if_not_found=True)  # Adds just a basic franka to the env a first time.
        robot = add_cortex_franka_to_world(world)  # References that one and sets up for cortex.
    else:
        robot = add_cortex_franka_to_world(world, load_if_not_found=True)

    # Establish the physics step size and corresponding cycle rate.
    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt

    # Build the motion commander.
    obstacles = {}
    commander = build_motion_commander(physics_dt, robot, obstacles)

    if args.test_loading_franka_from_cortex_env:
        # Test whether it works to load the franka from cortex initialized USD by cortex
        # initializing a wrapped version and build the commander again (the motion command build is
        # where the end-effector prim is added).
        input("loading a second time <press>")
        robot = add_cortex_franka_to_world(world, robot_name="franka_reloaded")
        commander = build_motion_commander(physics_dt, robot, obstacles)

    if args.position_only:
        commander.set_target_position_only()

    print("<looping>")
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
                world.reset()

            action = commander.get_action()
            robot.get_articulation_controller().apply_action(action)

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
