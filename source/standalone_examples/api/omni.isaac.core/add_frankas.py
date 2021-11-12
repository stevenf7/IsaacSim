# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units
from omni.isaac.core.utils.nucleus import find_nucleus_server
import numpy as np
import carb
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode")
args, unknown = parser.parse_known_args()

my_world = World(stage_units_in_meters=0.01)

my_world.scene.add_default_ground_plane()
result, nucleus_server = find_nucleus_server()
if result is False:
    carb.log_error("Could not find nucleus server with /Isaac folder")
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_1")
add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_2")
articulated_system_1 = my_world.scene.add(Robot(prim_path="/World/Franka_1", name="my_franka_1"))
articulated_system_2 = my_world.scene.add(Robot(prim_path="/World/Franka_2", name="my_franka_2"))

for i in range(5):
    print("resetting...")
    my_world.reset()
    articulated_system_1.set_world_pose(position=np.array([0.0, 2.0, 0.0]) / get_stage_units())
    articulated_system_2.set_world_pose(position=np.array([0.0, -2.0, 0.0]) / get_stage_units())
    articulated_system_1.set_joint_positions(np.array([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]))
    for j in range(500):
        my_world.step(render=True)
        if j == 100:
            articulated_system_2.get_articulation_controller().apply_action(
                ArticulationAction(joint_positions=np.array([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]))
            )
        if j == 400:
            print("Franka 1's joint positions are: ", articulated_system_1.get_joint_positions())
            print("Franka 2's joint positions are: ", articulated_system_2.get_joint_positions())
    if args.test is True:
        break
simulation_app.close()
