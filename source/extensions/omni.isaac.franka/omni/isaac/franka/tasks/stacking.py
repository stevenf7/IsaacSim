# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks import Stacking as BaseStacking
from omni.isaac.franka import Franka
import numpy as np


class Stacking(BaseStacking):
    def __init__(self) -> None:
        BaseStacking.__init__(
            self,
            robot=Franka(prim_path="/World/Franka", name="my_franka"),
            cube_initial_positions=np.array([[0.3, 0.3, 0.3], [0.3, -0.3, 0.3]]),
            cube_initial_orientations=None,
            stack_target_position=None,
            cube_size=0.0515,
        )
        return
