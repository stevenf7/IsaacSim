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

from omni.isaac.franka.tasks import FollowTarget
from omni.isaac.franka.controllers import RMPFlowController
from omni.isaac.core import World
from omni.isaac.franka.controllers import InverseKinematicsSolver
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import numpy as np

my_world = World()
my_task = FollowTarget()
my_world.load_task(my_task)
my_world.reset()
my_franka = my_world.scene.get_object("my_franka")
# my_controller = InverseKinematicsSolver(
#     name="target_follower_controller",
#     robot_prim_path=my_franka.prim_path)
my_controller = RMPFlowController(name="target_follower_controller", robot_prim_path=my_franka.prim_path)
articulation_controller = my_franka.get_articulation_controller()

i = 0
while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(target_end_effector_position=observations["target"]["position"])
    articulation_controller.apply_action(actions)
    my_world.step(render=True)
    if i % 2000 == 0:
        my_task.add_obstacle()
    if i % 3000 == 0:
        my_task.remove_obstacle()
    i += 1

simulation_app.close()
