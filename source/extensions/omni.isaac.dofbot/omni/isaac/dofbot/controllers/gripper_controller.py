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
from typing import List, Optional
import numpy as np


class GripperController(BaseGripperController):
    """[summary]

        Args:
            name (str): [description]
            gripper_dof_indices (List[int]): [description]
            deltas (Optional[np.ndarray], optional): [description]. Defaults to None.
        """

    def __init__(self, name: str, gripper_dof_indices: List[int], deltas: Optional[np.ndarray] = None) -> None:
        self._grippers_dof_indices = gripper_dof_indices
        super().__init__(name)
        if deltas is None:
            deltas = np.array([-0.1, 0.1])
        self._deltas = deltas
        return

    @property
    def grippers_dof_indices(self) -> List[int]:
        """[summary]

        Returns:
            List[int]: [description]
        """
        return self._grippers_dof_indices

    def open(self, current_joint_positions: np.ndarray) -> ArticulationAction:
        """[summary]

        Args:
            current_joint_positions (np.ndarray): [description]

        Returns:
            ArticulationAction: [description]
        """
        current_gripper_position_1 = current_joint_positions[self.grippers_dof_indices[0]]
        current_gripper_position_2 = current_joint_positions[self.grippers_dof_indices[1]]
        target_joint_positions = [None] * current_joint_positions.shape[0]
        target_joint_positions[self._grippers_dof_indices[0]] = current_gripper_position_1 + self._deltas[0]
        target_joint_positions[self._grippers_dof_indices[1]] = current_gripper_position_2 + self._deltas[1]
        return ArticulationAction(joint_positions=target_joint_positions)

    def close(self, current_joint_positions: np.ndarray) -> ArticulationAction:
        """[summary]

        Args:
            current_joint_positions (np.ndarray): [description]

        Returns:
            ArticulationAction: [description]
        """
        current_gripper_position_1 = current_joint_positions[self.grippers_dof_indices[0]]
        current_gripper_position_2 = current_joint_positions[self.grippers_dof_indices[1]]
        target_joint_positions = [None] * current_joint_positions.shape[0]
        target_joint_positions[self._grippers_dof_indices[0]] = current_gripper_position_1 - self._deltas[0]
        target_joint_positions[self._grippers_dof_indices[1]] = current_gripper_position_2 - self._deltas[1]
        return ArticulationAction(joint_positions=target_joint_positions)

    def set_deltas(self, deltas: np.ndarray) -> None:
        """[summary]

        Args:
            deltas (np.ndarray): [description]
        """
        self._deltas = deltas
        return

    def get_deltas(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._deltas
