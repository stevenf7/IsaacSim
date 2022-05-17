# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.kit import SimulationApp
import numpy as np
import copy
import os
import sys
import time

from omni.isaac.core.utils.nucleus import get_assets_root_path


def parse_args():
    import argparse

    node_name = "test_franka"
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument(
        "--set_slow_gains",
        action="store_true",
        help="Configure the robot to have a strong damping gain to move slowly.",
    )
    parser.add_argument("--use_second_reset", action="store_true", help="Exercise the issue.")
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


import omni
from omni.isaac.core import World
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.types import ArticulationAction


def write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


class SteadyRate:
    """ Maintains the steady cycle rate provided on initialization by adaptively sleeping an amount
    of time to make up the remaining cycle time after work is done.

    Usage:

    rate = SteadyRate(rate_hz=30.)
    while True:
      do.work()  # Do any work.
      rate.sleep()  # Sleep for the remaining cycle time.

    """

    def __init__(self, rate_hz):
        self.rate_hz = rate_hz
        self.dt = 1.0 / rate_hz
        self.last_sleep_end = time.time()

    def sleep(self):
        work_elapse = time.time() - self.last_sleep_end
        sleep_time = self.dt - work_elapse
        if sleep_time > 0.0:
            time.sleep(sleep_time)
        self.last_sleep_end = time.time()


def configure_robot(robot):
    robot.disable_gravity()

    controller = robot.get_articulation_controller()
    kps, kds = controller.get_gains()
    kds *= 1000.0
    controller.set_gains(kps, kds)


def main(args):
    input("cortex_main getting world <press>")
    print("cortex_main create world")
    world = World(stage_units_in_meters=1.0)
    print("cortex_main done create world")

    print("<enabling cortex ROS-based extensions (but should be stripped down ROS-free version>")
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_manager.set_extension_enabled_immediate("omni.isaac.cortex", True)

    use_usd = True
    if use_usd:
        usd_env = (
            "omniverse://ov-isaac-dev/Users/nratliff/CortexMeters/Franka/BlocksWorld/cortex_franka_blocks_belief.usd"
        )
        add_reference_to_stage(usd_path=usd_env, prim_path="/cortex")
        robot = world.scene.add(Robot(prim_path="/cortex/belief/robot", name="franka_belief"))
    else:
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            print("Could not find Isaac Sim assets folder")
        asset_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/cortex/belief/robot")
        robot = world.scene.add(Robot(prim_path="/cortex/belief/robot", name="franka_belief"))

    # Establish the physics step size and corresponding cycle rate.
    physics_dt = world.get_physics_dt()
    rate_hz = 1.0 / physics_dt

    print("<first reset>")
    world.reset()

    if args.set_slow_gains:
        configure_robot(robot)
    if args.use_second_reset:
        print("<second reset>")
        world.reset()
        world.reset()

    q_init = copy.deepcopy(robot.get_joint_positions())
    q_goal = 0.5 * (q_init + np.zeros(len(q_init)))
    q_init = q_goal

    print("<looping>")
    rate = SteadyRate(rate_hz)

    i = 0.0
    N = 100.0
    while simulation_app.is_running():
        a = i / N
        if a > 1.0:
            a = 1.0
        q = a * q_goal + (1.0 - a) * q_init
        robot.apply_action(ArticulationAction(joint_positions=q))
        write(".")

        write("<")
        action = robot.get_applied_action()
        write(">")

        world.step(render=True)
        i += 1

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
