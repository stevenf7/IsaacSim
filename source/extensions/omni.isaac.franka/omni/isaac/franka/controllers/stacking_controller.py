# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.motion_generation as mg
from omni.isaac.franka.controllers import PickPlaceController
from typing import List


class StackingController(mg.StackingController):
    """[summary]

        Args:
            name (str): [description]
            gripper_dof_indices (List[int]): [description]
            robot_prim_path (str): [description]
            picking_order_cube_names (List[str]): [description]
            robot_observation_name (str): [description]
        """

    def __init__(
        self,
        name: str,
        gripper_dof_indices: List[int],
        robot_prim_path: str,
        picking_order_cube_names: List[str],
        robot_observation_name: str,
    ) -> None:
        mg.StackingController.__init__(
            self,
            name=name,
            pick_place_controller=PickPlaceController(
                name=name + "_pick_place_controller",
                gripper_dof_indices=gripper_dof_indices,
                robot_prim_path=robot_prim_path,
            ),
            picking_order_cube_names=picking_order_cube_names,
            robot_observation_name=robot_observation_name,
        )
        return
