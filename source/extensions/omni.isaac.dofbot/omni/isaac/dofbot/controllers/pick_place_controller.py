# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.utils.stage import get_stage_units
import omni.isaac.motion_generation as mg
from omni.isaac.dofbot.controllers import GripperController
from omni.isaac.motion_generation import RMPFlowController


class PickPlaceController(mg.PickPlaceController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, gripper_dof_indices, robot_prim_path, event_velocities=None):
        if event_velocities is None:
            event_velocities = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.05, 0.01, 0.08]
        mg.PickPlaceController.__init__(
            self,
            name=name,
            cspace_controller=RMPFlowController(
                name=name + "_cspace_controller", robot_prim_path=robot_prim_path, policy_map_path=["DofBot", "RMPflow"]
            ),
            gripper_controller=GripperController(
                name=name + "_gripper_controller", gripper_dof_indices=gripper_dof_indices, deltas=None
            ),
            event_velocities=event_velocities,
            start_picking_height=0.2 / get_stage_units(),
        )
        return
