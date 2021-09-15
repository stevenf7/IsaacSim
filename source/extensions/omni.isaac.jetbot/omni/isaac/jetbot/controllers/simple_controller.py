from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.controllers import BaseController
from typing import Union
import numpy as np
from enum import Enum


class SimpleContollerCommand(Enum):
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3


class SimpleController(BaseController):
    def __init__(self, name: str) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        super().__init__(name)
        return

    def forward(self, direction: SimpleContollerCommand) -> Union[ArticulationAction, dict, np.ndarray]:
        """[summary]

        Args:
            observations (dict): [description]

        Raises:
            NotImplementedError: [description]

        Returns:
            ArticulationAction: [description]
        """
        if direction == SimpleContollerCommand.FORWARD:
            # TODO: change values when convert asset
            return ArticulationAction(joint_velocities=np.array([2.0, 2.0]))
        elif direction == SimpleContollerCommand.BACKWARD:
            return ArticulationAction(joint_velocities=np.array([-2.0, -2.0]))
        elif direction == SimpleContollerCommand.LEFT:
            return ArticulationAction(joint_velocities=np.array([-1.0, 1.0]))
        elif direction == SimpleContollerCommand.RIGHT:
            return ArticulationAction(joint_velocities=np.array([1.0, -1.0]))
        return

    def reset(self) -> None:
        """[summary]
        """
        return
