# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseGripperController
from omni.isaac.core.utils.types import ArticulationAction


class GripperController(BaseGripperController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, surface_gripper):
        super().__init__(name)
        self._surface_gripper = surface_gripper
        return

    def open(self, current_joint_positions):
        target_joint_positions = [None] * current_joint_positions.shape[0]
        self._surface_gripper.open()
        return ArticulationAction(joint_positions=target_joint_positions)

    def close(self, current_joint_positions):
        target_joint_positions = [None] * current_joint_positions.shape[0]
        self._surface_gripper.close()
        return ArticulationAction(joint_positions=target_joint_positions)
