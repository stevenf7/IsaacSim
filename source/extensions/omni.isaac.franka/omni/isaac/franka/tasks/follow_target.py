# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.isaac.core.tasks as tasks
from omni.isaac.franka import Franka


class FollowTarget(tasks.FollowTarget):
    def __init__(
        self, target_prim_path="/World/TargetCube", target_name="target", target_position=None, target_orientation=None
    ) -> None:
        """[summary]
        """
        tasks.FollowTarget.__init__(
            self,
            robot=Franka(prim_path="/World/Franka", name="my_franka"),
            target_prim_path=target_prim_path,
            target_name=target_name,
            target_position=target_position,
            target_orientation=target_orientation,
        )
        return
