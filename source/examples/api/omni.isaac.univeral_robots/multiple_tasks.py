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


from omni.isaac.universal_robots.tasks import Stacking as UR10Stacking
from omni.isaac.universal_robots.controllers import StackingController as UR10StackingController
from omni.isaac.franka.tasks import Stacking as FrankaStacking
from omni.isaac.franka.controllers import StackingController as FrankaStackingController
from omni.isaac.core import World
import numpy as np

my_world = World(stage_units_in_meters=0.01)
tasks = []
num_of_tasks = 2

tasks.append(FrankaStacking(name="task_0", task_frame_translation=np.array([0, -200, 0])))
my_world.add_task(tasks[-1])
tasks.append(UR10Stacking(name="task_1", task_frame_translation=np.array([0, 0, 0])))
my_world.add_task(tasks[-1])
my_world.reset()
robots = []
for i in range(num_of_tasks):
    task_params = tasks[i].get_params()
    robots.append(my_world.scene.get_object(task_params["robot_name"]["value"]))

controllers = []
controllers.append(
    FrankaStackingController(
        name="pick_place_controller",
        gripper_dof_indices=robots[0].gripper.dof_indices,
        robot_prim_path=robots[0].prim_path,
        picking_order_cube_names=tasks[0].get_cube_names(),
        robot_observation_name=robots[0].name,
    )
)
controllers[-1].reset()
controllers.append(
    UR10StackingController(
        name="pick_place_controller",
        surface_gripper=robots[1].gripper,
        robot_prim_path=robots[1].prim_path,
        picking_order_cube_names=tasks[1].get_cube_names(),
        robot_observation_name=robots[1].name,
    )
)


articulation_controllers = []
for i in range(num_of_tasks):
    articulation_controllers.append(robots[i].get_articulation_controller())

my_world.pause()
while True:
    if my_world.is_playing():
        observations = my_world.get_observations()
        actions = controllers[0].forward(
            observations=observations, end_effector_translation_offset=np.array([0, 0, -1.5])
        )
        articulation_controllers[0].apply_action(actions)
        actions = controllers[1].forward(observations=observations, end_effector_translation_offset=np.array([0, 0, 2]))
        articulation_controllers[1].apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
