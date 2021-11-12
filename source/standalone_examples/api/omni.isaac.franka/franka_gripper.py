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

from omni.isaac.franka import Franka
from omni.isaac.core import World
from omni.isaac.core.utils.types import ArticulationAction


my_world = World(stage_units_in_meters=0.01)
my_franka = my_world.scene.add(Franka(prim_path="/World/Franka", name="my_franka"))
my_world.scene.add_default_ground_plane()
my_world.reset()

i = 0
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_playing():
        if my_world.current_time_step_index == 0:
            my_world.reset()
        i += 1
        gripper_positions = my_franka.gripper.get_positions()
        if i < 500:
            my_franka.gripper.apply_action(
                ArticulationAction(
                    joint_positions=[gripper_positions[0] - (0.005 * 100), gripper_positions[1] - (0.005 * 100)]
                )
            )
        if i > 500:
            my_franka.gripper.apply_action(
                ArticulationAction(
                    joint_positions=[gripper_positions[0] + (0.005 * 100), gripper_positions[1] + (0.005 * 100)]
                )
            )
        if i == 1000:
            i = 0


simulation_app.close()
