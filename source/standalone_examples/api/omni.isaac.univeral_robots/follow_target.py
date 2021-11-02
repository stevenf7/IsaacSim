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

from omni.isaac.universal_robots.tasks import FollowTarget
from omni.isaac.universal_robots.controllers import RMPFlowController
from omni.isaac.universal_robots import InverseKinematicsSolver
from omni.isaac.core import World

# from omni.isaac.universal_robots.controllers import InverseKinematicsSolver
from omni.isaac.core.utils.rotations import euler_angles_to_quat

my_world = World(stage_units_in_meters=0.01)
my_task = FollowTarget(name="follow_target_task", attach_gripper=True)
my_world.add_task(my_task)
my_world.reset()
task_params = my_world.get_task("follow_target_task").get_params()
ur10_name = task_params["robot_name"]["value"]
target_name = task_params["target_name"]["value"]
my_ur10 = my_world.scene.get_object(ur10_name)
# my_controller = InverseKinematicsSolver(
#     name="target_follower_controller",
#     robot_prim_path=my_ur10.prim_path,
#     attach_gripper=True)
my_controller = RMPFlowController(
    name="target_follower_controller", robot_prim_path=my_ur10.prim_path, attach_gripper=True
)
articulation_controller = my_ur10.get_articulation_controller()
i = 0
while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(
        target_end_effector_position=observations[target_name]["position"],
        target_end_effector_orientation=observations[target_name]["orientation"],
    )
    articulation_controller.apply_action(actions)
    my_world.step(render=True)
    if i % 2000 == 0:
        my_task.add_obstacle()
    if i % 3000 == 0:
        my_task.remove_obstacle()
    i += 1

simulation_app.close()
