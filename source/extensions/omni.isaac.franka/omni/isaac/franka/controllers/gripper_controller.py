# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseGripperController
from omni.isaac.core.utils.types import ArticulationAction
from typing import Tuple


class GripperController(BaseGripperController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, gripper_dof_indices, deltas=[0.005, 0.005]):
        super().__init__(name, gripper_dof_indices)
        self._deltas = deltas
        return

    def open(self, current_joint_positions):
        current_gripper_position_1 = current_joint_positions[self.grippers_dof_indices[0]]
        current_gripper_position_2 = current_joint_positions[self.grippers_dof_indices[1]]
        target_joint_positions = [None] * current_joint_positions.shape[0]
        target_joint_positions[self._grippers_dof_indices[0]] = current_gripper_position_1 + self._deltas[0]
        target_joint_positions[self._grippers_dof_indices[1]] = current_gripper_position_2 + self._deltas[1]
        return ArticulationAction(joint_positions=target_joint_positions)

    def close(self, current_joint_positions):
        current_gripper_position_1 = current_joint_positions[self.grippers_dof_indices[0]]
        current_gripper_position_2 = current_joint_positions[self.grippers_dof_indices[1]]
        target_joint_positions = [None] * current_joint_positions.shape[0]
        target_joint_positions[self._grippers_dof_indices[0]] = current_gripper_position_1 - self._deltas[0]
        target_joint_positions[self._grippers_dof_indices[1]] = current_gripper_position_2 - self._deltas[1]
        return ArticulationAction(joint_positions=target_joint_positions)

    def set_deltas(self, deltas: Tuple[float, float]):
        self._deltas = deltas

    def get_deltas(self):
        return self._deltas
