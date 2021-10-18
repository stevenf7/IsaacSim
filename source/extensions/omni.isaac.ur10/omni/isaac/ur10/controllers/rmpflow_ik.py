# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseController
from omni.isaac.motion_generation import MotionGenerator
from omni.isaac.core.utils.types import ArticulationAction
from typing import Optional
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
import os
import json
import numpy as np
import lula


class RMPFlowIKSolver(BaseController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(
        self, name, mg_extension_path, dc_interface, stage, robot_prim, dt: float = 1.0 / 60.0, with_short_gripper=False
    ):
        super().__init__(name)
        self._dc_interface = dc_interface
        self._stage = stage
        self.mg = MotionGenerator(dc_interface, stage)
        polciy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(polciy_config_dir, "policy_map.json")) as policy_map:
            policy_map = json.load(policy_map)
        if with_short_gripper:
            config_path = os.path.join(polciy_config_dir, policy_map["UR10"]["RMPflowSuction"])
        else:
            config_path = os.path.join(polciy_config_dir, policy_map["UR10"]["RMPflow"])
        self._config = self.process_policy_config(config_path)
        self._robot_prim = robot_prim
        self.mg.initialize(self._config, robot_prim, int(1.0 / dt))
        self._dt = dt
        return

    def process_policy_config(self, mp_config_file):
        mp_config_dir = os.path.dirname(mp_config_file)  # path to directory containing mp_config_file

        with open(mp_config_file) as config_file:
            config = json.load(config_file)

        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_config_dir, v)

        return config

    def forward(
        self,
        current_joint_positions: np.ndarray,
        target_end_effector_position: np.ndarray,
        target_end_effector_orientation: Optional[np.ndarray] = None,
    ):
        if target_end_effector_orientation is not None:
            # TODO: change values with USD
            self.mg._motion_policy._policy.set_end_effector_target(
                position=np.array(target_end_effector_position, dtype=np.float64).reshape(3, 1) / 100.0,
                orientation=lula.Rotation3(
                    np.array(quat_to_rot_matrix(target_end_effector_orientation), dtype=np.float64).reshape(3, 3)
                ),
            )
        else:
            # TODO: change values with USD
            self.mg._motion_policy._policy.set_end_effector_target(
                position=np.array(target_end_effector_position, dtype=np.float64).reshape(3, 1) / 100.0
            )
        integration_dt = self.mg.sim_timestep
        aji = self.mg._active_joint_inds

        current_joint_velocities = np.zeros_like(current_joint_positions).astype(np.float64)
        current_joint_positions = current_joint_positions.astype(np.float64)
        target_joint_positions = np.array([None] * current_joint_positions.shape[0])
        if self.mg._motion_policy._robot_joint_positions is not None:
            self.mg._motion_policy._robot_joint_positions = current_joint_positions[aji]
        if self.mg._motion_policy._robot_joint_velocities is not None:
            self.mg._motion_policy._robot_joint_velocities = current_joint_velocities[aji]
        for i in range(10):
            target_joint_positions[aji] = self.mg._motion_policy.get_joint_position_targets(
                current_joint_positions[aji], current_joint_velocities[aji], integration_dt
            )
        target_joint_positions = list(target_joint_positions)
        for i in range(current_joint_positions.shape[0]):
            if i not in aji:
                target_joint_positions[i] = None
        return ArticulationAction(joint_positions=target_joint_positions)

    def add_cube_obstacle(self, cube_prim):
        self.mg.create_cube(cube_prim)
        return

    def remove_cube_obstacle(self, cube_prim):
        self.mg.remove_obstacle(cube_prim)
        return

    def reset(self):
        self.mg = MotionGenerator(self._dc_interface, self._stage)
        self.mg.initialize(self._config, self._robot_prim, int(1.0 / self._dt))
        return
