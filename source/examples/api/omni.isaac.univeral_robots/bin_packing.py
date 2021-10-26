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

from omni.isaac.ur10.tasks import BinPacking
from omni.isaac.ur10.controllers import RMPFlowPickPlace
from omni.isaac.core import World
from omni.isaac.core.utils.extensions import get_extension_id, get_extension_path

my_world = World(stage_units_in_meters=0.01)
extension_id = get_extension_id("omni.isaac.motion_generation")
mg_extension_path = get_extension_path(ext_id=extension_id)
my_task = BinPacking()
my_world.add_task(my_task)
my_world.reset()
my_ur10 = my_world.scene.get_object("my_ur10")
my_controller = RMPFlowPickPlace(
    name="pick_place_controller",
    dc_interface=my_world.dc_interface,
    stage=my_world.stage,
    robot_prim=my_ur10.prim,
    mg_extension_path=mg_extension_path,
    gripper_controller=my_ur10,
    gripper_length=my_ur10.gripper_length,
    approach="side",
)
articulation_controller = my_ur10.get_articulation_controller()
added_screws = False
while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(
        cube_position=observations["packing_bin"]["position"],
        cube_orientation=observations["packing_bin"]["orientation"],
        cube_target_position=observations["packing_bin"]["target_position"],
        cube_size=observations["packing_bin"]["size"],
        current_joint_positions=observations["my_ur10"]["joint_positions"],
    )
    if not added_screws and my_controller.get_current_event() == 5 and not my_controller.is_paused():
        my_controller.pause()
        my_task.add_screws()
        added_screws = True
    if my_controller.is_paused() and my_task.get_current_num_of_screws_to_add() == 0:
        my_controller.resume()
    articulation_controller.apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
