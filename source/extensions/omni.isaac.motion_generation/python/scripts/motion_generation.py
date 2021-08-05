# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
from omni.isaac.dynamic_control import _dynamic_control
from enum import Enum
import carb
from .lula_motion_policies import *
from .motion_policy_interface import *
import time


class MotionGenerator:

    """
    Comments are sparse for this class because most of the functions are wrappers for MotionPolicy functions
    Look at the MotionPolicy class to see detailed descriptions of of each function
    """

    def __init__(self, _dynamic_control, _stage):
        self._dc = _dynamic_control
        self._stage = _stage
        self.initialized = False

    def initialize(self, policy_config, robot_prim, sim_fps, velocity_control_damping=1e8):
        """
        Args:
            param policy_config : dictionary containing the necessary configurations for a motion policy

                    policy_config must specify "policy_type" to select a specific motion policy such as "RMPflow"

                    policy_config must specify "evaluations_per_frame" to specify the number of times that
                        the motion policy is called between every frame of the simulation.  Ex. RMPflow will have smoother
                        motions if it has a high number of evaluations per frame.  Euler integration is used to allow policies
                        to be evaluated at smaller timesteps than the simulator.

                    All other specifications are policy dependent.

            param robot_prim: USD prim for robot

            param sim_fps: the frequency at which Isaac Sim updates the world.  It is usually 60 Hz
        """

        if "evaluations_per_frame" not in policy_config:
            carb.log_error("Required arg evaluations_per_frame was not specified in policy_config.")
            return  # still uninitialized

        policy_evals_per_frame = policy_config["evaluations_per_frame"]
        if policy_evals_per_frame // 1 != policy_evals_per_frame or policy_evals_per_frame < 1:
            carb.log_error("evaluations_per_frame must be a positive integer in the motion policy config file")
            return  # still uninitialized

        self.sim_timestep = 1 / sim_fps
        self.policy_evals_per_frame = int(policy_evals_per_frame)

        # initialize motion policy
        if "policy_type" not in policy_config:
            carb.log_error("Required arg policy_type was not specified in policy_config")
            return

        if policy_config["policy_type"] == "RMPflow":
            self._motion_policy = RmpFlow(policy_config, self._stage, robot_prim)
        else:
            carb.log_error("invalid value of policy_type in policy_config")
            return  # still uninitialized

        if not self._motion_policy.initialized:
            return  # still uninitialized

        # initialize controller

        self._ar = self._dc.get_articulation(robot_prim.GetPath().pathString)
        self._active_joints = self._motion_policy.get_active_joints()
        self._active_joint_inds = [
            self._dc.find_articulation_dof_index(self._ar, joint) for joint in self._active_joints
        ]

        self._default_dc_config = self._dc.get_articulation_dof_properties(self._ar)

        if (
            self._motion_policy.policy_type == PolicyType.ACCELERATION
            or self._motion_policy.policy_type == PolicyType.VELOCITY
        ):
            self._configure_velocity_control(damping=velocity_control_damping)

        self.initialized = self._motion_policy.initialized

    def is_initialized(self):
        return self.initialized

    def move(self, updated_obstacles=None):
        self._motion_policy.update(updated_obstacles=updated_obstacles)  # update motion_policy internal world state

        if self._motion_policy.policy_type == PolicyType.ACCELERATION:
            self._follow_acceleration_policy()
        if self._motion_policy.policy_type == PolicyType.VELOCITY:
            self._follow_velocity_policy()
        if self._motion_policy.policy_type == PolicyType.POSITION:
            self._follow_position_policy()

    def get_joint_states(self):
        joint_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_ALL)
        pos, vel, accel = zip(*joint_states)

        return np.array(pos, dtype=np.float64), np.array(vel, dtype=np.float64), np.array(accel, dtype=np.float64)

    def get_active_joint_states(self):
        joint_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_ALL)
        pos, vel, accel = zip(*joint_states)

        pos = np.array(pos, dtype=np.float64)[self._active_joint_inds]
        vel = np.array(vel, dtype=np.float64)[self._active_joint_inds]
        accel = np.array(accel, dtype=np.float64)[self._active_joint_inds]

        return pos, vel, accel

    def get_end_effector_pose(self):
        joint_poses = self.get_active_joint_states()[0]
        return self._motion_policy.get_end_effector_pose(joint_poses)

    def set_cspace_target(self, target):
        self._motion_policy.set_cspace_target(target)

    def set_end_effector_target(self, target_prim):
        self._motion_policy.set_end_effector_target(target_prim)

    def create_cube(self, block_prim, side_length=None, static=False):
        return self._motion_policy.create_cube(block_prim, side_length, static)

    def create_block(self, block_prim, dimensions=None, static=False):
        return self._motion_policy.create_block(block_prim, dimensions, static)

    def create_sphere(self, sphere_prim, radius=None, static=False):
        return self._motion_policy.create_sphere(sphere_prim, radius, static)

    def create_capsule(self, capsule_prim, radius=None, height=None, static=False):
        return self._motion_policy.create_capsule(capsule_prim, radius, height, static)

    def get_prim_pose(self, prim, default_trans=np.zeros(3), default_rot=np.eye(3)):
        return self._motion_policy.get_prim_pose(prim, default_trans=default_trans, default_rot=default_rot)

    def disable_obstacle(self, obstacle_prim):
        return self._motion_policy.disable_obstacle(obstacle_prim)

    def enable_obstacle(self, obstacle_prim):
        return self._motion_policy.enable_obstacle(obstacle_prim)

    def remove_obstacle(self, obstacle_prim):
        return self._motion_policy.remove_obstacle(obstacle_prim)

    def get_velocity_target_from_acceleration_policy(self):
        joint_positions, joint_velocities, joint_accel = self.get_joint_states()
        dji = self._active_joint_inds

        # do steps of Euler integration to match the desired number of policy evals per frame
        policy_timestep = self.sim_timestep / self.policy_evals_per_frame

        for i in range(self.policy_evals_per_frame):
            joint_accel[dji] = self._motion_policy.evaluate_acceleration(joint_positions[dji], joint_velocities[dji])
            joint_positions[dji] += policy_timestep * joint_velocities[dji]
            joint_velocities[dji] += policy_timestep * joint_accel[dji]

        return joint_velocities

    def _configure_velocity_control(self, damping):
        # Set robot to use velocity control rather than position control

        props = _dynamic_control.DofProperties()
        props.drive_mode = _dynamic_control.DRIVE_VEL
        props.damping = damping
        props.stiffness = 0
        for ind in self._active_joint_inds:
            self._dc.set_dof_properties(self._dc.find_articulation_dof(self._ar, self._active_joints[ind]), props)

    def _set_joint_velocity_target(self, joint_velocities):
        self._dc.wake_up_articulation(self._ar)

        self._dc.set_articulation_dof_velocity_targets(self._ar, joint_velocities.astype(np.float32))

    def _follow_acceleration_policy(self):
        joint_velocities = self.get_velocity_target_from_acceleration_policy()

        self._set_joint_velocity_target(joint_velocities)

    def _follow_velocity_policy(self):
        # Not implemented because no velocity motion policy has been implemented yet
        pass

    def _follow_position_policy(self):
        # Not implemented because no position motion policy has been implemented yet

        # self._dc.set_articulation_dof_position_targets(self._ar, joint_positions.astype(np.float32))
        pass
