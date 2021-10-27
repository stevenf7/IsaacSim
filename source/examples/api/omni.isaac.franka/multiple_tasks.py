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

my_world = World(stage_units_in_meters=0.01)
tasks = []
num_of_tasks = 2
for i in range(num_of_tasks):
    tasks.append(PickPlace(name="task" + str(i), task_frame_translation=100 * np.array([0, (i * 2) - 3, 0])))
    my_world.add_task(tasks[-1])
my_world.reset()
frankas = []
cube_names = []
for i in range(num_of_tasks):
    task_params = tasks[i].get_params()
    frankas.append(my_world.scene.get_object(task_params["robot_name"]["value"]))
    cube_names.append(task_params["cube_name"]["value"])

controllers = []
for i in range(num_of_tasks):
    controllers.append(
        PickPlaceController(
            name="pick_place_controller",
            gripper_dof_indices=frankas[i].gripper.dof_indices,
            robot_prim_path=frankas[i].prim_path,
        )
    )
    controllers[-1].reset()

articulation_controllers = []
for i in range(num_of_tasks):
    articulation_controllers.append(frankas[i].get_articulation_controller())

my_world.pause()
while True:
    if my_world.is_playing():
        observations = my_world.get_observations()
        for i in range(num_of_tasks):
            articulation_controllers.append(frankas[i].get_articulation_controller())
            actions = controllers[i].forward(
                picking_position=observations[cube_names[i]]["position"],
                placing_position=observations[cube_names[i]]["target_position"],
                current_joint_positions=observations[frankas[i].name]["joint_positions"],
                end_effector_translation_offset=np.array([0, 0, -0.015 * 100]),
            )
            articulation_controllers[i].apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
