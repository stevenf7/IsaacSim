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

from omni.isaac.franka.tasks import PickPlace
from omni.isaac.franka.controllers import PickPlaceController
from omni.isaac.core import World
import numpy as np

my_world = World()
my_task = PickPlace()
my_world.load_task(my_task)
my_world.reset()
my_franka = my_world.scene.get_object("my_franka")
my_controller = PickPlaceController(
    name="pick_place_controller", gripper_dof_indices=my_franka.gripper.dof_indices, robot_prim_path=my_franka.prim_path
)
articulation_controller = my_franka.get_articulation_controller()

i = 0
while True:
    if my_world.is_playing():
        observations = my_world.get_observations()
        actions = my_controller.forward(
            cube_position=observations["cube_1"]["position"],
            cube_orientation=observations["cube_1"]["orientation"],
            cube_target_position=observations["cube_1"]["target_position"],
            current_joint_positions=observations["my_franka"]["joint_positions"],
            end_effector_translation_offset=np.array([0, 0, -0.015]),
        )
        if my_controller.is_done():
            print("done picking and placing")
        articulation_controller.apply_action(actions)
    my_world.step(render=True)
simulation_app.close()
