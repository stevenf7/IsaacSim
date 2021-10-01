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

from omni.isaac.ur10.tasks import TargetFollower
from omni.isaac.ur10.controllers import RMPFlowIKSolver
from omni.isaac.core import World
from omni.isaac.kit.utils import get_extension_id, get_extension_path

my_world = World(stage_units_in_meters=0.01)
extension_id = get_extension_id("omni.isaac.motion_generation")
mg_extension_path = get_extension_path(ext_id=extension_id)
my_task = TargetFollower()
my_world.load_task(my_task)
my_world.reset()
my_ur10 = my_world.scene.get_object("my_ur10")
my_controller = RMPFlowIKSolver(
    name="target_follower",
    dc_interface=my_world.dc_interface,
    stage=my_world.stage,
    robot_prim=my_ur10.prim,
    mg_extension_path=mg_extension_path,
)
articulation_controller = my_ur10.get_articulation_controller()

while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(
        target_end_effector_position=observations["target_cube"]["position"],
        current_joint_positions=observations["my_ur10"]["joint_positions"],
    )
    articulation_controller.apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
