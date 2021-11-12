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
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.prims import get_prim_at_path, is_prim_path_valid
from omni.isaac.dynamic_control import _dynamic_control
from typing import Optional, List
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.extensions import get_extension_path_from_name
from omni.isaac.core.utils.string import find_unique_string_name
import os
import json
import numpy as np
from pxr import Usd


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
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._stage = get_current_stage()
        self._mg = MotionGenerator(self._stage)
        mg_extension_path = get_extension_path_from_name("omni.isaac.motion_generation")
        polciy_config_dir = os.path.join(mg_extension_path, "policy_configs")
        with open(os.path.join(polciy_config_dir, "policy_map.json")) as policy_map:
            policy_map = json.load(policy_map)
        config_path = os.path.join(polciy_config_dir, policy_map[policy_map_path[0]][policy_map_path[1]])
        self._config = self._process_policy_config(config_path)
        self._robot_prim = get_prim_at_path(robot_prim_path)
        self._mg.initialize(self._config, self._robot_prim, int(1.0 / physics_dt))
        self._physics_dt = physics_dt
        virtual_target_name = find_unique_string_name(
            intitial_name="/World/RMPFlowTarget", is_unique_fn=lambda x: not is_prim_path_valid(x)
        )
        self._target_prim = XFormPrim(prim_path=virtual_target_name)
        self._mg.set_end_effector_target(self._target_prim.prim)
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
            self._target_prim.set_world_pose(
                position=target_end_effector_position, orientation=euler_angles_to_quat(np.array([0, np.pi, 0]))
            )
        else:
            self._target_prim.set_world_pose(
                position=target_end_effector_position, orientation=target_end_effector_orientation
            )
        self._mg._motion_policy.update()
        target_joint_positions = self._mg.get_joint_position_targets()
        return ArticulationAction(joint_positions=target_joint_positions)

    def add_cube_obstacle(self, cube_prim: Usd.Prim) -> None:
        """[summary]

        Args:
            cube_prim (Usd.Prim): [description]
        """
        self._mg.create_block(cube_prim)
        return

    def remove_cube_obstacle(self, cube_prim: Usd.Prim) -> None:
        """[summary]

        Args:
            cube_prim (Usd.Prim): [description]
        """
        self._mg.remove_obstacle(cube_prim)
        return

    def reset(self) -> None:
        """[summary]
        """
        self._mg = MotionGenerator(self._stage)
        self._mg.initialize(self._config, self._robot_prim, int(1.0 / self._physics_dt))
        self._mg.set_end_effector_target(self._target_prim.prim)
        return

    def get_motion_generation(self) -> MotionGenerator:
        """[summary]

        Returns:
            MotionGenerator: [description]
        """
        return self._mg
