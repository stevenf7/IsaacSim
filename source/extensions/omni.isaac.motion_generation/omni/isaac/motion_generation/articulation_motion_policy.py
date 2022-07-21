# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import torch
import carb

from .motion_policy_interface import MotionPolicy
from .articulation_subset import ArticulationSubset
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.utils.types import ArticulationAction


class ArticulationMotionPolicy:
    """Wrapper class for running MotionPolicy on simulated robots.

    Args:
        robot_articulation (Articulation): an initialized robot Articulation object
        motion_policy (MotionPolicy): an instance of a class that implements the MotionPolicy interface
        physics_dt (float): Duration of a physics step in Isaac Sim (typically 1/60 s).

    Returns:
        None

    """

    def __init__(self, robot_articulation: Articulation, motion_policy: MotionPolicy, physics_dt: float) -> None:

        self.physics_dt = physics_dt
        self._robot_articulation = robot_articulation

        self.motion_policy = motion_policy

        self._articulation_controller = self._robot_articulation.get_articulation_controller()

        self._active_joints_view = ArticulationSubset(robot_articulation, motion_policy.get_active_joints())
        self._watched_joints_view = ArticulationSubset(robot_articulation, motion_policy.get_watched_joints())

    def move(self) -> None:
        """Use underlying MotionPolicy to compute and apply joint targets to the robot over the next frame.

        Return:
            None
        """
        action = self.get_next_articulation_action()
        self._articulation_controller.apply_action(action)

    def get_next_articulation_action(self) -> ArticulationAction:
        """Use underlying MotionPolicy to compute joint targets for the robot over the next frame.

        Returns: 
            ArticulationAction: Desired position/velocity target for the robot in the next frame
        """

        joint_positions, joint_velocities = (
            self._active_joints_view.get_joint_positions(),
            self._active_joints_view.get_joint_velocities(),
        )
        watched_joint_positions, watched_joint_velocities = (
            self._watched_joints_view.get_joint_positions(),
            self._watched_joints_view.get_joint_velocities(),
        )

        if joint_positions is None:
            carb.log_error(
                "Attempted to compute an action, but the robot Articulation has not been initialized.  Cannot get joint positions or velocities."
            )

        # convert to numpy if torch tensor
        if isinstance(joint_positions, torch.Tensor):
            joint_positions = joint_positions.cpu().numpy()
        if isinstance(joint_velocities, torch.Tensor):
            joint_velocities = joint_velocities.cpu().numpy()
        if isinstance(watched_joint_positions, torch.Tensor):
            watched_joint_positions = watched_joint_positions.cpu().numpy()
        if isinstance(watched_joint_velocities, torch.Tensor):
            watched_joint_velocities = watched_joint_velocities.cpu().numpy()

        position_targets, velocity_targets = self.motion_policy.compute_joint_targets(
            joint_positions, joint_velocities, watched_joint_positions, watched_joint_velocities, self.physics_dt
        )

        if position_targets is not None:
            position_action = self._active_joints_view.map_to_articulation_order(position_targets)
        else:
            position_action = None

        if velocity_targets is not None:
            velocity_action = self._active_joints_view.map_to_articulation_order(velocity_targets)
        else:
            velocity_action = None

        return ArticulationAction(joint_positions=position_action, joint_velocities=velocity_action)

    def get_active_joints_subset(self) -> ArticulationSubset:
        """Get view into active joints

        Returns:
            ArticulationSubset: returns robot states for active joints in an order compatible with the MotionPolicy
        """
        return self._active_joints_view

    def get_watched_joints_subset(self) -> ArticulationSubset:
        """Get view into watched joints

        Returns:
            ArticulationSubset: returns robot states for watched joints in an order compatible with the MotionPolicy
        """
        return self._watched_joints_view

    def get_robot_articulation(self) -> Articulation:
        """ Get the underlying Articulation object representing the robot.

        Returns:
            Articulation: Articulation object representing the robot.
        """
        return self._robot_articulation

    def get_motion_policy(self) -> MotionPolicy:
        """Get MotionPolicy that is being used to compute ArticulationActions
        
        Returns:
            MotionPolicy: MotionPolicy being used to compute ArticulationActions
        """
        return self.motion_policy
