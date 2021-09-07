# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from numpy.core.fromnumeric import reshape
from omni.isaac.core.controllers.controller import BaseController
from omni.isaac.motion_generation import MotionGenerator
from omni.isaac.core.utils.types import ArticulationAction
from typing import Optional
from omni.isaac.core.utils.rotations import rot_matrix_from_quat
import os
import json
import numpy as np
import lula


class RMPFlowIKSolver(BaseController):
    # TODO: this will need further discussion with buck and SRL before cleaning it up
    def __init__(self, name, mg_extension_path, dc_interface, stage, robot_prim):
        super().__init__(name)
        self.mg = MotionGenerator(dc_interface, stage)
        polciy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(polciy_config_dir, "policy_map.json")) as policy_map:
            policy_map = json.load(policy_map)
        config_path = os.path.join(polciy_config_dir, policy_map["Franka"]["RMPflow"])
        self.config = self.process_policy_config(config_path)
        self.mg.initialize(self.config, robot_prim, 60)
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
            self.mg._motion_policy._policy.set_end_effector_target(
                position=np.array(target_end_effector_position, dtype=np.float64).reshape(3, 1),
                orientation=lula.Rotation3(
                    np.array(rot_matrix_from_quat(target_end_effector_orientation), dtype=np.float64).reshape(3, 3)
                ),
            )
        else:
            self.mg._motion_policy._policy.set_end_effector_target(
                position=np.array(target_end_effector_position, dtype=np.float64).reshape(3, 1)
            )
        self.mg._motion_policy.update()
        integration_dt = self.mg.sim_timestep
        joint_positions, joint_velocities, joint_accel = self.mg.get_joint_states()
        aji = self.mg._active_joint_inds

        target_joint_positions = np.array([None] * current_joint_positions.shape[0])
        target_joint_positions[aji] = self.mg._motion_policy.get_joint_position_targets(
            joint_positions[aji], joint_velocities[aji], integration_dt
        )
        target_joint_positions = list(target_joint_positions)
        for i in range(current_joint_positions.shape[0]):
            if i not in aji:
                target_joint_positions[i] = None
        return ArticulationAction(joint_positions=target_joint_positions)

    def update_obstacles(self, obstacles):
        raise NotImplementedError
