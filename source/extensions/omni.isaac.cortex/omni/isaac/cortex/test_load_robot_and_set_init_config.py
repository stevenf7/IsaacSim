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


def parse_args():
    import argparse

    node_name = "test_load_robot_and_set_init_config"
    parser = argparse.ArgumentParser(node_name)
    parser.add_argument("--usd_env", type=str, required=True, help="Path to the USD environment to load.")
    args = parser.parse_args()
    return args


args = parse_args()
simulation_app = SimulationApp({"experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit', "headless": False})


import omni
from omni.isaac.core import World
from omni.isaac.franka import Franka
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.core.utils.stage import add_reference_to_stage, print_stage_prim_paths


def main():
    add_sim_robot_to_world = False
    perform_post_reset_on_sim = True

    world = World(stage_units_in_meters=0.01)

    print("loading world from USD:", args.usd_env)
    add_reference_to_stage(usd_path=args.usd_env, prim_path="/cortex")

    robot = Franka(prim_path="/cortex/world/franka", name="franka")
    world.scene.add(robot)

    sim_robot = Franka(prim_path="/cortex/sim/franka", name="sim_franka", position=np.array([-120.0, 0.0, 0.0]))
    if add_sim_robot_to_world:
        world.scene.add(sim_robot)

    world.reset()
    sim_robot.initialize()

    retracted_config = np.array([np.pi / 4, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
    robot.set_joints_default_state(positions=retracted_config)
    sim_robot.set_joints_default_state(positions=retracted_config)
    world.reset()
    sim_robot.post_reset()

    world.step(render=True)
    reset_happened = False
    while simulation_app.is_running():

        if reset_happened:
            print("q before step render:", robot.get_joints_state().positions)
            input("before step after reset <press>")
        world.step(render=True)
        if reset_happened:
            print("q after step render:", robot.get_joints_state().positions)
            input("after step after reset <press>")

        if world.is_playing():
            if world.current_time_step_index == 0:
                input("before reset <press>")
                world.reset()

                if not add_sim_robot_to_world and perform_post_reset_on_sim:
                    sim_robot.post_reset()

                reset_happened = True

                print("q before step render:", robot.get_joints_state().positions)
                world.step(render=True)
                print("q after step render:", robot.get_joints_state().positions)
                input("after reset <press>")
            else:
                reset_happened = False


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
