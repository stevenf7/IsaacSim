# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers.controller import BaseController
from omni.isaac.franka.controllers import RMPFlowPickPlace
from omni.isaac.core.utils.types import ArticulationAction


class RMPFlowTower(BaseController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, mg_extension_path, dc_interface, stage, robot_prim):
        self._pick_place = RMPFlowPickPlace(
            name=name + "pick_place",
            dc_interface=dc_interface,
            stage=stage,
            robot_prim=robot_prim,
            mg_extension_path=mg_extension_path,
        )
        self._order = None
        self._current_cube = 0
        self._robot_observation_name = None
        self._pick_place.reset()

    def configure(self, cubes_order, robot_observation_name):
        self._order = cubes_order
        self._robot_observation_name = robot_observation_name
        return

    def forward(self, observations):
        if self._current_cube >= len(self._order):
            target_joint_positions = [None] * observations[self._robot_observation_name]["joint_positions"].shape[0]
            return ArticulationAction(joint_positions=target_joint_positions)
        actions = self._pick_place.forward(
            cube_position=observations[self._order[self._current_cube]]["position"],
            cube_orientation=observations[self._order[self._current_cube]]["orientation"],
            cube_target_position=observations[self._order[self._current_cube]]["target_position"],
            current_joint_positions=observations[self._robot_observation_name]["joint_positions"],
        )
        if self._pick_place.is_done():
            self._current_cube += 1
            self._pick_place.reset()
        return actions

    def reset(self):
        self._current_cube = 0
        self._pick_place.reset()
        return

    def is_done(self):
        if self._current_cube >= len(self._order):
            return True
        else:
            return False
