# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
from .motion_policy_interface import MotionPolicy
from typing import Tuple
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.utils.types import ArticulationAction


class MotionGenerator:
    """Interface for running MotionPolicy on simulated robots.
    """

    def __init__(self) -> None:
        self.initialized = False

    def initialize(self, motion_policy: MotionPolicy, robot_prim_path: str, physics_dt: float) -> None:
        """Initialize MotionGenerator.

        Args:
            motion_policy (MotionPolicy): an instance of a class that implements the MotionPolicy interface
            robot_prim (str): Path to USD prim for the robot
            physics_dt (float): Duration of a physics step in Isaac Sim (defaults to 1/60 s)

        Returns:
            None
        """

        self.physics_dt = physics_dt
        self._robot_articulation = Articulation(robot_prim_path)
        self._robot_articulation.initialize()

        self.motion_policy = motion_policy

        # initialize controller
        self._articulation_controller = self._robot_articulation.get_articulation_controller()

        self._active_joints = self.motion_policy.get_active_joints()
        self._watched_joints = self.motion_policy.get_watched_joints()

        self._active_joint_inds = [self._robot_articulation.get_dof_index(joint) for joint in self._active_joints]
        self._watched_joint_inds = [self._robot_articulation.get_dof_index(joint) for joint in self._watched_joints]

        self.initialized = True

    def is_initialized(self) -> bool:
        """Indicates whether MotionGenerator has been successfully initialized with the initialize() function

        Returns:
            bool: True if MotionGenerator initialize() function has completed without error
        """

        return self.initialized

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
        aji = self._active_joint_inds

        joint_positions, joint_velocities, _ = self.get_active_joint_states()
        watched_joint_positions, watched_joint_velocities, _ = self.get_watched_joint_states()

        position_targets, velocity_targets = self.motion_policy.compute_joint_targets(
            joint_positions, joint_velocities, watched_joint_positions, watched_joint_velocities, self.physics_dt
        )

        if position_targets is not None:
            position_action = [None] * self._robot_articulation.num_dof
            for i, j in enumerate(aji):
                position_action[j] = position_targets[i]
        else:
            position_action = None

        if velocity_targets is not None:
            velocity_action = [None] * self._robot_articulation.num_dof
            for i, j in enumerate(aji):
                velocity_action[j] = velocity_targets[i]
        else:
            velocity_action = None

        return ArticulationAction(joint_positions=position_action, joint_velocities=velocity_action)

    def get_joint_states(self) -> Tuple[np.array, np.array, np.array]:
        """Return the states (position, velocity and acceleration) of all robot joints.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for all robot joints.
        """
        joints_state = self._robot_articulation.get_joints_state()
        return joints_state.positions, joints_state.velocities, joints_state.efforts

    def get_active_joint_states(self) -> Tuple[np.array, np.array, np.array]:
        """Return the states (position, velocity and acceleration) of active robot joints.
        Active joints are joints controlled by the underlying MotionPolicy.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for active robot joints.
        """
        pos, vel, effort = self.get_joint_states()

        pos = pos[self._active_joint_inds]
        vel = vel[self._active_joint_inds]
        effort = effort[self._active_joint_inds]

        return pos, vel, effort

    def get_watched_joint_states(self) -> Tuple[np.array, np.array, np.array]:
        """Return the states (position, velocity and acceleration) of active robot joints.
        Watched joints are joints that are being observed but not directly controlled by the underlying MotionPolicy.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for watched robot joints.
        """
        pos, vel, effort = self.get_joint_states()

        pos = pos[self._watched_joint_inds]
        vel = vel[self._watched_joint_inds]
        effort = effort[self._watched_joint_inds]

        return pos, vel, effort

    def get_motion_policy(self) -> MotionPolicy:
        """
        It can be convenient to interact directly with the low level motion policy for testing and development,
        but in general the policy should be designed to function using only the motion_policy_interface.
        
        Returns:
            MotionPolicy: Underlying motion policy used by MotionGenerator.
        """
        return self.motion_policy
