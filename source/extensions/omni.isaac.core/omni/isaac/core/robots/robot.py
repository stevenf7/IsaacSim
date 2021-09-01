# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
import numpy as np
from pxr import Usd
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.controllers.articulation_controllers import ArticulationController


class Robot(Articulation):
    def __init__(
        self,
        prim: Usd.Prim,
        name: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        articulation_controller: Optional[ArticulationController] = None,
    ) -> None:
        """[summary]

        Args:
            prim (Usd.Prim): [description]
            name (Optional, optional): [description]. Defaults to None.
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
            articulation_controller (Optional, optional): [description]. Defaults to None.
        """
        super().__init__(
            prim=prim,
            name=name,
            position=position,
            orientation=orientation,
            articulation_controller=articulation_controller,
        )
        self._sensors = list()
        # TODO: add sensor and controller buffers for messaging
        # TODO: potentially add some default agents for planning..etc

    def _initilize_sensors(self) -> None:
        """[summary]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def reset(self) -> None:
        """[summary]
        """
        super().reset()
        # TODO: reset sensors too
        return
