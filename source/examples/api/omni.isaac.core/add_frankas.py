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
from omni.isaac.franka import get_franka_usd_path

my_world = World()

asset_path = get_franka_usd_path()
articulated_system_1 = my_world.scene.add(
    Robot(prim=my_world.add_usd_reference(usd_path=asset_path, prim_path="/World/Franka_1"), name="my_franka_1")
)
articulated_system_2 = my_world.scene.add(
    Robot(prim=my_world.add_usd_reference(usd_path=asset_path, prim_path="/World/Franka_2"), name="my_franka_2")
)
# NOTE: here you can only set the pose through set_usd_pose()

for i in range(5):
    print("resetting...")
    my_world.reset()
    articulated_system_1.set_pose(position=[0.0, 2.0, 0.0])
    articulated_system_2.set_pose(position=[0.0, -2.0, 0.0])
    articulated_system_1.set_joint_positions([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
    for j in range(500):
        my_world.step(render=True)
        if j == 100:
            articulated_system_2.get_articulation_controller().apply_action(
                ArticulationAction(joint_positions=[1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
            )
        if j == 400:
            print("Franka 1's joint positions are: ", articulated_system_1.get_joint_positions())
            print("Franka 2's joint positions are: ", articulated_system_2.get_joint_positions())
simulation_app.close()
