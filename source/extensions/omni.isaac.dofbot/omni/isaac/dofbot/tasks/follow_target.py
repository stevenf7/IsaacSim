# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.core.tasks as tasks
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.dofbot import DofBot
from omni.isaac.core.utils.prims import is_prim_path_valid
from omni.isaac.core.utils.string import find_unique_string_name
import numpy as np


class FollowTarget(tasks.FollowTarget):
    def __init__(
        self,
        name="dofbot_follow_target",
        target_prim_path=None,
        target_name=None,
        target_position=None,
        target_orientation=None,
        offset=None,
        dofbot_prim_path=None,
        dofbot_robot_name=None,
    ) -> None:
        """[summary]
        """
        if target_position is None:
            target_position = np.array([0, 0.1, 0.1]) / get_stage_units()
        tasks.FollowTarget.__init__(
            self,
            name=name,
            target_prim_path=target_prim_path,
            target_name=target_name,
            target_position=target_position,
            target_orientation=target_orientation,
            offset=offset,
        )
        self._dofbot_prim_path = dofbot_prim_path
        self._dofbot_robot_name = dofbot_robot_name
        return

    def set_robot(self):
        if self._dofbot_prim_path is None:
            self._dofbot_prim_path = find_unique_string_name(
                intitial_name="/World/DofBot", is_unique_fn=lambda x: not is_prim_path_valid(x)
            )
        if self._dofbot_robot_name is None:
            self._dofbot_robot_name = find_unique_string_name(
                intitial_name="my_dofbot", is_unique_fn=lambda x: not self.scene.object_exists(x)
            )
        return DofBot(prim_path=self._dofbot_prim_path, name=self._dofbot_robot_name)
