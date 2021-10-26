# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.motion_generation as mg
from omni.isaac.franka.controllers import GripperController
from omni.isaac.motion_generation import RMPFlowController


class PickPlaceController(mg.PickPlaceController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, gripper_dof_indices, robot_prim_path):
        mg.PickPlaceController.__init__(
            self,
            name=name,
            ik_solver=RMPFlowController(
                name=name + "_ik_solver", robot_prim_path=robot_prim_path, policy_map_path=["Franka", "RMPflow"]
            ),
            gripper_controller=GripperController(
                name=name + "_gripper_controller", gripper_dof_indices=gripper_dof_indices, deltas=None
            ),
        )
        return
