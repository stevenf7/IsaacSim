# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from abc import abstractmethod
from omni.isaac.core.controllers import BaseController


class BaseGripperController(BaseController):
    def __init__(self, name: str) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        self._name = name
        return

    # TODO: pass other args down
    def forward(self, action, current_joint_positions):
        if action == "open":
            return self.open(current_joint_positions)
        elif action == "close":
            return self.close(current_joint_positions)
        else:
            raise Exception("The action is not recognized, it has to be either open or close")

    @abstractmethod
    def open(self, current_joint_positions):
        raise NotImplementedError

    @abstractmethod
    def close(self, current_joint_positions):
        raise NotImplementedError

    def reset(self) -> None:
        """[summary]
        """
        return
