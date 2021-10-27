# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.motion_generation as mg
from omni.isaac.universal_robots.controllers import PickPlaceController


class StackingController(mg.StackingController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, surface_gripper, robot_prim_path, picking_order_cube_names, robot_observation_name):
        mg.StackingController.__init__(
            self,
            name=name,
            pick_place_controller=PickPlaceController(
                name=name + "_pick_place_controller", surface_gripper=surface_gripper, robot_prim_path=robot_prim_path
            ),
            picking_order_cube_names=picking_order_cube_names,
            robot_observation_name=robot_observation_name,
        )
        return

    def forward(self, observations, end_effector_orientation=None, end_effector_offset=None):
        return super().forward(
            observations, end_effector_orientation=end_effector_orientation, end_effector_offset=end_effector_offset
        )
