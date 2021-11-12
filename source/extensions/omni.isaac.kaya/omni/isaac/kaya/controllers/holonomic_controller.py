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
import math
import numpy as np


class HolonomicController(BaseController):
    """[summary]

        Args:
            name (str): [description]
            wheel_radius (float, optional): Radius of left and right wheels in cms. Defaults to 4.0.
            wheel_base (float, optional):  Distance between left and right wheels in cms. Defaults to 12.5.
        """

    def __init__(self, name: str, wheel_radius: float = 4.0, wheel_base: float = 12.5) -> None:
        super().__init__(name)
        self._wheel_radius = wheel_radius
        self._wheel_base = wheel_base
        return

    def forward(self, longitudinal_velocity: float, lateral_velocity: float, yaw_velocity: float) -> ArticulationAction:
        """[summary]

        Args:
            longitudinal_velocity (float): [description]
            lateral_velocity (float): [description]
            yaw_velocity (float): [description]

        Returns:
            ArticulationAction: [description]
        """
        target_velocity = np.array([longitudinal_velocity, lateral_velocity, yaw_velocity])
        forward_matrix = np.array(
            [
                [0, -(1.0 / math.sqrt(3.0)), (1.0 / math.sqrt(3.0))],
                [(1.0 / 3.0) * 2, -(1.0 / 3.0), -(1.0 / 3.0)],
                [-(1.0 / 3.0) / self._wheel_base, -(1.0 / 3.0) / self._wheel_base, -(1.0 / 3.0) / self._wheel_base],
            ]
        )
        wheels_radius_matrix = np.array(
            [[self._wheel_radius, 0, 0], [0, self._wheel_radius, 0], [0, 0, self._wheel_radius]]
        )
        transform_matrix = np.matmul(forward_matrix, wheels_radius_matrix)
        inverse_matrix = np.linalg.inv(transform_matrix)
        wheel_speed = np.matmul(inverse_matrix, target_velocity)
        return ArticulationAction(joint_velocities=wheel_speed)

    def reset(self) -> None:
        """[summary]
        """
        return
