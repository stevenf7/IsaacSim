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

from omni.isaac.dofbot.tasks import PickPlace
from omni.isaac.dofbot.controllers import PickPlaceController
from omni.isaac.core import World
import numpy as np

my_world = World(stage_units_in_meters=0.01)
my_task = PickPlace()
my_world.add_task(my_task)
my_world.reset()
task_params = my_task.get_params()
dofbot_name = task_params["robot_name"]["value"]
my_dofbot = my_world.scene.get_object(dofbot_name)
my_controller = PickPlaceController(
    name="pick_place_controller", gripper_dof_indices=my_dofbot.gripper.dof_indices, robot_prim_path=my_dofbot.prim_path
)
articulation_controller = my_dofbot.get_articulation_controller()

i = 0
while True:
    if my_world.is_playing():
        observations = my_world.get_observations()
        actions = my_controller.forward(
            picking_position=observations[task_params["cube_name"]["value"]]["position"],
            placing_position=observations[task_params["cube_name"]["value"]]["target_position"],
            current_joint_positions=observations[dofbot_name]["joint_positions"],
            end_effector_offset=np.array([0, -6, 0]),
        )
        if my_controller.is_done():
            print("done picking and placing")
        articulation_controller.apply_action(actions)
    my_world.step(render=True)
simulation_app.close()
