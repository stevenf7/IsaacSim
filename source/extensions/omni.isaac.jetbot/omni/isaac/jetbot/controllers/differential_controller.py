# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.controllers import BaseController
import numpy as np


class DifferentialController(BaseController):
    """Controller uses unicycle model for a diffrential drive

        Args:
            name (str): [description]
            wheel_radius (float): Radius of left and right wheels in cms
            wheel_base (float): Distance between left and right wheels in cms
        """

    def __init__(self, name: str, wheel_radius=3, wheel_base=11.25) -> None:
        super().__init__(name)
        self._wheel_radius = wheel_radius
        self._wheel_base = wheel_base
        return

    def forward(self, command: np.ndarray) -> ArticulationAction:
        """[summary]

        Args:
            command (np.ndarray): [description]

        Returns:
            ArticulationAction: [description]
        """
        joint_velocities = [0.0, 0.0]
        joint_velocities[0] = ((2 * command[0]) - (command[1] * self._wheel_base)) / (2 * self._wheel_radius)
        joint_velocities[1] = ((2 * command[0]) + (command[1] * self._wheel_base)) / (2 * self._wheel_radius)
        return ArticulationAction(joint_velocities=joint_velocities)

    def reset(self) -> None:
        """[summary]
        """
        return
