# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers.controller import BaseController
from omni.isaac.core.utils.types import ArticulationAction
import numpy as np
from typing import Tuple


class GripperController(BaseController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, gripper_dof_indices):
        super().__init__(name)
        self._grippers_dof_indices = gripper_dof_indices
        return

    def forward(self, current_joint_positions: np.ndarray, deltas: Tuple[float, float]):
        current_gripper_position_1 = current_joint_positions[self._grippers_dof_indices[0]]
        current_gripper_position_2 = current_joint_positions[self._grippers_dof_indices[1]]
        target_joint_positions = [None] * current_joint_positions.shape[0]
        target_joint_positions[self._grippers_dof_indices[0]] = current_gripper_position_1 + deltas[0]
        target_joint_positions[self._grippers_dof_indices[1]] = current_gripper_position_2 + deltas[1]
        return ArticulationAction(joint_positions=target_joint_positions)

    def reset(self):
        return
