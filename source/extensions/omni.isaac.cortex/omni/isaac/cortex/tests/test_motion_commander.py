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


from omni.isaac.core.utils.stage import add_reference_to_stage

sys.path.append(os.path.dirname(__file__) + "/..")
from cortex_utils import (
    build_motion_commander,
    configure_robot,
    load_franka_to_stage,
    make_empty_world,
    set_home_config,
    wrap_cortex_robot_or_die,
)
from omni.isaac.cortex.tools import write, SteadyRate, CycleTimer

import lula
import omni


def main(args):
    world = make_empty_world()

    usd_env = "omniverse://ov-isaac-dev.nvidia.com/Users/nratliff/cortex/blocks_world/cortex_blocks_world_belief.usd"
    add_reference_to_stage(usd_path=usd_env, prim_path="/cortex")
    robot = world.scene.add(wrap_cortex_robot_or_die(domain="world"))
    world.reset()  # Initialize the robot and dynamic control.

    configure_robot(robot, verbose=True)
    set_home_config(robot)
    world.reset()  # Set the robot to the initial config before building the motion commander.

    # Establish the physics step size and corresponding cycle rate.
    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt

    # Build the motion commander.
    obstacles = {}
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
