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
from omni.isaac.core.utils.stage import get_current_stage
from typing import Optional, List
import omni.isaac.core.objects
from omni.isaac.core.utils.rotations import euler_angles_to_quat, quat_to_rot_matrix
from omni.isaac.core.utils.extensions import get_extension_path_from_name
import os
import json
import numpy as np


class RMPFlowController(BaseController):
    """[summary]

        Args:
            name (str): [description]
            robot_prim_path (str): [description]
            policy_map_path (List[str]): [description]
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """

    def __init__(
        self, name: str, robot_prim_path: str, policy_map_path: List[str], physics_dt: float = 1.0 / 60.0
    ) -> None:
        BaseController.__init__(self, name)
        self._mg = MotionGenerator()
        mg_extension_path = get_extension_path_from_name("omni.isaac.motion_generation")
        polciy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(polciy_config_dir, "policy_map.json")) as policy_map:
            policy_map = json.load(policy_map)
        config_path = os.path.join(polciy_config_dir, policy_map[policy_map_path[0]][policy_map_path[1]])
        self._config = self._process_policy_config(config_path)
        self._robot_prim_path = robot_prim_path

        self._mg.initialize(self._config, self._robot_prim_path, int(1.0 / physics_dt))
        self._physics_dt = physics_dt
        return

    def _process_policy_config(self, mg_config_file):
        mp_config_dir = os.path.dirname(mg_config_file)
        with open(mg_config_file) as config_file:
            config = json.load(config_file)
        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_config_dir, v)
        return config

    def forward(
        self, target_end_effector_position: np.ndarray, target_end_effector_orientation: Optional[np.ndarray] = None
    ) -> ArticulationAction:
        """[summary]

        Args:
            target_end_effector_position (np.ndarray): [description]
            target_end_effector_orientation (Optional[np.ndarray], optional): [description]. Defaults to None.

        Returns:
            ArticulationAction: [description]
        """

        if target_end_effector_orientation is None:
            target_end_effector_orientation = euler_angles_to_quat(np.array([0, np.pi, 0]))

        self._mg.set_end_effector_target(target_end_effector_position, target_end_effector_orientation)

        self._mg._motion_policy.update()
        action = self._mg.get_next_articulation_action()

        return action

    def add_obstacle(self, obstacle: omni.isaac.core.objects) -> None:
        """Add an object from omni.isaac.core.objects as an obstacle to the motion_policy

        Args:
            obstacle (omni.isaac.core.objects): Dynamic or Fixed object from omni.isaac.core.objects
        """
        self._mg.add_obstacle(obstacle)
        return

    def remove_obstacle(self, obstacle: omni.isaac.core.objects) -> None:
        """Remove and added obstacle from the motion_policy

        Args:
            obstacle (omni.isaac.core.objects): Object from omni.isaac.core.objects that has been added to the motion_policy
        """
        self._mg.remove_obstacle(obstacle)
        return

    def reset(self) -> None:
        """[summary]
        """
        self._mg = MotionGenerator()
        self._mg.initialize(self._config, self._robot_prim_path, int(1.0 / self._physics_dt))
        return

    def get_motion_generation(self) -> MotionGenerator:
        """[summary]

        Returns:
            MotionGenerator: [description]
        """
        return self._mg
