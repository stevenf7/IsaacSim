# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import omni.isaac.motion_generation as mg
from omni.isaac.universal_robots.controllers import GripperController
from omni.isaac.universal_robots.controllers import RMPFlowController
import numpy as np


class PickPlaceController(mg.PickPlaceController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, surface_gripper, robot_prim_path):
        mg.PickPlaceController.__init__(
            self,
            name=name,
            ik_solver=RMPFlowController(name=name + "_ik_solver", robot_prim_path=robot_prim_path, attach_gripper=True),
            gripper_controller=GripperController(name=name + "_gripper_controller", surface_gripper=surface_gripper),
        )
        return

    def forward(
        self,
        cube_position,
        cube_orientation,
        cube_target_position,
        current_joint_positions,
        end_effector_translation_offset=None,
        approach_angle=None,
    ):
        if approach_angle is None:
            approach_angle = euler_angles_to_quat(np.array([0, np.pi / 2.0, 0]))
        return super().forward(
            cube_position,
            cube_orientation,
            cube_target_position,
            current_joint_positions,
            end_effector_translation_offset=end_effector_translation_offset,
            approach_angle=approach_angle,
        )
