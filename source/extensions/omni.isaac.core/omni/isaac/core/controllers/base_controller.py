# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from abc import abstractmethod
from omni.isaac.core.utils.types import ArticulationAction
from typing import Union
import numpy as np


class BaseController(object):
    def __init__(self, name: str) -> None:
        """[summary]

        Args:
            name (str): [description]
        """
        self._name = name

    @abstractmethod
    def forward(self, *args, **kwargs) -> Union[ArticulationAction, dict, np.ndarray]:
        """[summary]

        Args:
            observations (dict): [description]

        Raises:
            NotImplementedError: [description]

        Returns:
            ArticulationAction: [description]
        """
        raise NotImplementedError

    def reset(self) -> None:
        """[summary]
        """
        return
