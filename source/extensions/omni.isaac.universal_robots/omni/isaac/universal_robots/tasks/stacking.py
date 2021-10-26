# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.tasks import Stacking as BaseStacking
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.universal_robots import UR10
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.string import find_unique_string_name
import numpy as np


class Stacking(BaseStacking):
    def __init__(self, name="ur10_stacking", target_position=None, cube_size=None, task_frame_translation=None) -> None:
        if target_position is None:
            target_position = np.array([0.7, 0.7, 0]) / get_stage_units()
        BaseStacking.__init__(
            self,
            name=name,
            cube_initial_positions=np.array([[0.3, 0.3, 0.3], [0.3, -0.3, 0.3]]) / get_stage_units(),
            cube_initial_orientations=None,
            stack_target_position=target_position,
            cube_size=cube_size,
            task_frame_translation=task_frame_translation,
        )
        return

    def set_robot(self):
        ur10_prim_path = find_unique_string_name(
            intitial_name="/World/ur10", is_unique_fn=lambda x: not is_prim_path_valid(x)
        )
        ur10_robot_name = find_unique_string_name(
            intitial_name="my_ur10", is_unique_fn=lambda x: not self.scene.object_exists(x)
        )
        self._ur10_robot = UR10(prim_path=ur10_prim_path, name=ur10_robot_name, attach_gripper=True)
        return self._ur10_robot
