# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseController
from omni.isaac.core.utils.types import ArticulationAction


class StackingController(BaseController):
    def __init__(self, name, pick_place_controller, picking_order_cube_names, robot_observation_name):
        BaseController.__init__(self, name=name)
        self._pick_place_controller = pick_place_controller
        self._picking_order_cube_names = picking_order_cube_names
        self._current_cube = 0
        self._robot_observation_name = robot_observation_name
        self.reset()

    def forward(self, observations, end_effector_orientation=None, end_effector_offset=None):
        if self._current_cube >= len(self._picking_order_cube_names):
            target_joint_positions = [None] * observations[self._robot_observation_name]["joint_positions"].shape[0]
            return ArticulationAction(joint_positions=target_joint_positions)
        actions = self._pick_place_controller.forward(
            picking_position=observations[self._picking_order_cube_names[self._current_cube]]["position"],
            placing_position=observations[self._picking_order_cube_names[self._current_cube]]["target_position"],
            current_joint_positions=observations[self._robot_observation_name]["joint_positions"],
            end_effector_orientation=end_effector_orientation,
            end_effector_offset=end_effector_offset,
        )
        if self._pick_place_controller.is_done():
            self._current_cube += 1
            self._pick_place_controller.reset()
        return actions

    def reset(self, picking_order_cube_names=None):
        self._current_cube = 0
        self._pick_place_controller.reset()
        if picking_order_cube_names is not None:
            self._picking_order_cube_names = picking_order_cube_names
        return

    def is_done(self):
        if self._current_cube >= len(self._picking_order_cube_names):
            return True
        else:
            return False
