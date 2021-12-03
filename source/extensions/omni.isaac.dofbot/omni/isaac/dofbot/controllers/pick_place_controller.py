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
from typing import Optional, List


class PickPlaceController(mg.PickPlaceController):
    """[summary]

        Args:
            name (str): [description]
            gripper_dof_indices (List[int]): [description]
            robot_prim_path (str): [description]
            events_dt (Optional[List[float]], optional): [description]. Defaults to None.
        """

    def __init__(
        self, name: str, gripper_dof_indices: List[int], robot_prim_path: str, events_dt: Optional[List[float]] = None
    ) -> None:
        if events_dt is None:
            events_dt = [0.01, 0.01, 1, 0.01, 0.01, 0.01, 0.01, 0.05, 0.01, 0.08]
        mg.PickPlaceController.__init__(
            self,
            name=name,
            cspace_controller=RMPFlowController(
                name=name + "_cspace_controller", robot_prim_path=robot_prim_path, policy_map_path=["DofBot", "RMPflow"]
            ),
            gripper_controller=GripperController(
                name=name + "_gripper_controller", gripper_dof_indices=gripper_dof_indices, deltas=None
            ),
            events_dt=events_dt,
            start_picking_height=0.2 / get_stage_units(),
        )
        return
