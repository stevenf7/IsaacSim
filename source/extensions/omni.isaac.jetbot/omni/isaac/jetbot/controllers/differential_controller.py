from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.controllers import BaseController
from typing import Union
import numpy as np


class DifferentialController(BaseController):
    def __init__(self, name: str, wheel_radius=0.030, wheel_base=0.1125) -> None:
        """[summary]

        Args:
            name (str): [description]
            wheel_radius (float): Radius of left and right wheels in meters
            wheel_base (float): Distance between left and right wheels in meterss
        """
        super().__init__(name)
        self._wheel_radius = wheel_radius
        self._wheel_base = wheel_base
        return

    def forward(self, command: np.ndarray) -> Union[ArticulationAction, dict, np.ndarray]:
        """[summary]

        Args:
            command (array): forward and rotational velocity of robot

        Raises:
            NotImplementedError: [description]

        Returns:
            ArticulationAction: [description]
        """
        joint_velocities = [0.0, 0.0]
        joint_velocities[0] = (command[0] - command[1] * self._wheel_base) / self._wheel_radius
        joint_velocities[1] = (command[0] + command[1] * self._wheel_base) / self._wheel_radius

        return ArticulationAction(joint_velocities=joint_velocities)

    def reset(self) -> None:
        """[summary]
        """
        return
