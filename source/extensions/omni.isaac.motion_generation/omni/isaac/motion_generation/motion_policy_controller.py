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
from .motion_policy_interface import MotionPolicy
from omni.isaac.core.utils.types import ArticulationAction
from typing import Optional
import omni.isaac.core.objects
from omni.isaac.core.utils.rotations import euler_angles_to_quat
import numpy as np


class MotionPolicyController(BaseController):
    """A Controller that steps using an arbitrary MotionPolicy

        Args:
            name (str): name of this controller
            robot_prim_path (str): path to robot Prim
            motion_policy (MotionPolicy): An instance of a class that implements the MotionPolicy interface
            physics_dt (float, optional): duration of a physics step. Defaults to 1.0/60.0 s.
        """

    def __init__(
        self, name: str, robot_prim_path: str, motion_policy: MotionPolicy, physics_dt: float = 1.0 / 60.0
    ) -> None:
        BaseController.__init__(self, name)

        self._robot_prim_path = robot_prim_path
        self._physics_dt = physics_dt

        self._motion_policy = motion_policy
        self._mg = MotionGenerator()

        self._mg.initialize(self._motion_policy, self._robot_prim_path, physics_dt=physics_dt)
        return

    def forward(
        self, target_end_effector_position: np.ndarray, target_end_effector_orientation: Optional[np.ndarray] = None
    ) -> ArticulationAction:
        """Compute an ArticulationAction representing the desired robot state for the next simulation frame

        Args:
            target_translation (nd.array): Translation vector (3x1) for robot end effector.
                Target translation should be specified in the same units as the USD stage, relative to the stage origin.
            target_orientation (Optional[np.ndarray], optional): Quaternion of desired rotation for robot end effector relative to USD stage global frame.
                Target orientation defaults to None, which means that the robot may reach the target with any orientation.

        Returns:
            ArticulationAction: A wrapper object containing the desired next state for the robot
        """

        if target_end_effector_orientation is None:
            target_end_effector_orientation = euler_angles_to_quat(np.array([0, np.pi, 0]))

        self._motion_policy.set_end_effector_target(target_end_effector_position, target_end_effector_orientation)

        self._motion_policy.update_world()

        action = self._mg.get_next_articulation_action()

        return action

    def add_obstacle(self, obstacle: omni.isaac.core.objects, static: bool = False) -> None:
        """Add an object from omni.isaac.core.objects as an obstacle to the motion_policy

        Args:
            obstacle (omni.isaac.core.objects): Dynamic, Visual, or Fixed object from omni.isaac.core.objects
            static (bool): If True, the obstacle may be assumed by the MotionPolicy to remain stationary over time
        """
        self._motion_policy.add_obstacle(obstacle, static=static)
        return

    def remove_obstacle(self, obstacle: omni.isaac.core.objects) -> None:
        """Remove and added obstacle from the motion_policy

        Args:
            obstacle (omni.isaac.core.objects): Object from omni.isaac.core.objects that has been added to the motion_policy
        """
        self._motion_policy.remove_obstacle(obstacle)
        return

    def reset(self) -> None:
        """
        """
        self._motion_policy.reset()

        self._mg = MotionGenerator()
        self._mg.initialize(self._motion_policy, self._robot_prim_path, physics_dt=self._physics_dt)
        return

    def get_motion_generation(self) -> MotionGenerator:
        """Get MotionGenerator wrapper that is wrapping MotionPolicy

        Returns:
            MotionGenerator: Wraps MotionPolicy to interface policy with simulated robot
        """
        return self._mg

    def get_motion_policy(self) -> MotionPolicy:
        """Get MotionPolicy that was passed to this class on initialization

        Returns:
            MotionPolicy: an instance of the MotionPolicy interface
        """
        return self._motion_policy
