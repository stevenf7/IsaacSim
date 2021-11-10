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

from omni.isaac.universal_robots.tasks import Stacking
from omni.isaac.universal_robots.controllers import StackingController
from omni.isaac.core import World
import numpy as np

my_world = World(stage_units_in_meters=0.01)
my_task = Stacking()
my_world.add_task(my_task)
my_world.reset()
robot_name = my_task.get_robot_name()
my_ur10 = my_world.scene.get_object(robot_name)
my_controller = StackingController(
    name="stacking_controller",
    surface_gripper=my_ur10.gripper,
    robot_prim_path=my_ur10.prim_path,
    picking_order_cube_names=my_task.get_cube_names(),
    robot_observation_name=robot_name,
)
articulation_controller = my_ur10.get_articulation_controller()

i = 0
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_simulating():
        observations = my_world.get_observations()
        actions = my_controller.forward(observations=observations, end_effector_offset=np.array([0.0, 0.0, 2.0]))
        articulation_controller.apply_action(actions)

simulation_app.close()
