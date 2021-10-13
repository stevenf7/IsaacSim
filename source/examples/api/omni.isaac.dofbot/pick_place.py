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
from omni.isaac.dofbot.controllers import RMPFlowPickPlace
from omni.isaac.core import World
from omni.isaac.core.utils.extensions import get_extension_id, get_extension_path

my_world = World(stage_units_in_meters=0.01)
extension_id = get_extension_id("omni.isaac.motion_generation")
mg_extension_path = get_extension_path(ext_id=extension_id)
my_task = PickPlace()
my_world.load_task(my_task)
my_world.reset()
my_dofbot = my_world.scene.get_object("my_dofbot")
my_controller = RMPFlowPickPlace(
    name="pick_place_controller",
    dc_interface=my_world.dc_interface,
    stage=my_world.stage,
    robot_prim=my_dofbot.prim,
    mg_extension_path=mg_extension_path,
    gripper_dof_indices=my_dofbot.grippers_dof_indices,
)
articulation_controller = my_dofbot.get_articulation_controller()

while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(
        cube_position=observations["cube_1"]["position"],
        cube_orientation=observations["cube_1"]["orientation"],
        cube_target_position=observations["cube_1"]["target_position"],
        current_joint_positions=observations["my_dofbot"]["joint_positions"],
    )
    if my_controller.is_done():
        print("done picking and placing the cube")
    articulation_controller.apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
