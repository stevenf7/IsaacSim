# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.utils.types import ArticulationAction
import omni.isaac.motion_generation as mg
from omni.isaac.surface_gripper import SurfaceGripper
from omni.isaac.universal_robots.controllers import PickPlaceController
from typing import List, Optional
import numpy as np


class StackingController(mg.StackingController):
    """[summary]

    Args:
        name (str): [description]
        surface_gripper (SurfaceGripper): [description]
        robot_prim_path (str): [description]
        picking_order_cube_names (List[str]): [description]
        robot_observation_name (str): [description]
    """

    def __init__(
        self,
        name: str,
        surface_gripper: SurfaceGripper,
        robot_prim_path: str,
        picking_order_cube_names: List[str],
        robot_observation_name: str,
    ) -> None:
        mg.StackingController.__init__(
            self,
            name=name,
            pick_place_controller=PickPlaceController(
                name=name + "_pick_place_controller", surface_gripper=surface_gripper, robot_prim_path=robot_prim_path
            ),
            picking_order_cube_names=picking_order_cube_names,
            robot_observation_name=robot_observation_name,
        )
        return

    def forward(
        self,
        observations: dict,
        end_effector_orientation: Optional[np.ndarray] = None,
        end_effector_offset: Optional[np.ndarray] = None,
    ) -> ArticulationAction:
        """[summary]

        Args:
            observations (dict): [description]
            end_effector_orientation (Optional[np.ndarray], optional): [description]. Defaults to None.
            end_effector_offset (Optional[np.ndarray], optional): [description]. Defaults to None.

        Returns:
            ArticulationAction: [description]
        """
        return super().forward(
            observations, end_effector_orientation=end_effector_orientation, end_effector_offset=end_effector_offset
        )
