# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
from omni.isaac.dynamic_control import _dynamic_control
import carb
from .lula_motion_policies import *
from .motion_policy_interface import *
from pxr import Usd


class MotionGenerator:
    """Interface for running MotionPolicy on simulated robots.
    """

    def __init__(self, stage: Usd.Stage):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._stage = stage
        self.initialized = False

    def initialize(self, policy_config, robot_prim, sim_fps, velocity_control_damping=1e8):
        """Initialize MotionGenerator.

        Args:
            policy_config (dict): Dictionary containing the necessary configurations for a motion policy. 
                policy_config must specify "policy_type" to select a specific motion policy such as "RMPflow". 
                All other specifications are policy dependent.
            robot_prim (pxr.Usd.Prim): USD prim for robot.
            sim_fps (float): Frequency at which Isaac Sim updates the world, typically 60 Hz
            velocity_control_damping (float, optional): Damping gain if using velocity control. Defaults to 1e8.

        Returns:
            None
        """

        if "evaluations_per_frame" not in policy_config:
            carb.log_error("Required arg evaluations_per_frame was not specified in policy_config.")
            return  # still uninitialized

        self.sim_timestep = 1 / sim_fps

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

        if self._motion_policy.policy_type == PolicyType.VELOCITY:
            self._configure_velocity_control(damping=velocity_control_damping)
        else:
            self._configure_position_control()

        self.initialized = self._motion_policy.initialized

    def is_initialized(self):
        """Indicates whether MotionGenerator has been initialized.

        Returns:
            bool: Return True if MotionGenerator has been initialized. Else return False.
        """
        return self.initialized

    def move(self, updated_obstacles=None):
        """Generate new joint targets using MotionPolicy and apply joint targets to the robot.
        
        Args:
            updated_obstacles (list, optional): List of obstacles that need to have their poses updated. 
                If provided, only these obstacles will have their poses updated. Defaults to None.
        """
        self._motion_policy.update(updated_obstacles=updated_obstacles)  # update motion_policy internal world state

        if self._motion_policy.policy_type == PolicyType.VELOCITY:
            self._follow_velocity_policy()
        if self._motion_policy.policy_type == PolicyType.POSITION:
            self._follow_position_policy()

    def get_joint_states(self):
        """Return the states (position, velocity and acceleration) of all robot joints.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for all robot joints.
        """
        joint_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_ALL)
        pos, vel, accel = zip(*joint_states)

        return np.array(pos, dtype=np.float64), np.array(vel, dtype=np.float64), np.array(accel, dtype=np.float64)

    def get_active_joint_states(self):
        """Return the states (position, velocity and acceleration) of active robot joints.
        Active joints are joints controlled by the underlying MotionPolicy.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for active robot joints.
        """
        joint_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_ALL)
        pos, vel, accel = zip(*joint_states)

        pos = np.array(pos, dtype=np.float64)[self._active_joint_inds]
        vel = np.array(vel, dtype=np.float64)[self._active_joint_inds]
        accel = np.array(accel, dtype=np.float64)[self._active_joint_inds]

        return pos, vel, accel

    def get_end_effector_pose(self):
        """Return current pose of the end effector.

        Returns:
            Tuple[np.array, np.array]: End effector pose returned as translation vector (3 x 1) and rotation matrix (3 x 3).
        """
        joint_poses = self.get_active_joint_states()[0]
        return self._motion_policy.get_end_effector_pose(joint_poses)

    def set_cspace_target(self, target):
        """Set configuration space target for the robot.

        Args:
            target (np.array): Desired configuration for the robot as (m x 1) vector where m is the number of active 
                joints.

        Returns:
            None
        """
        self._motion_policy.set_cspace_target(target)

    def set_end_effector_target(self, target_prim, position_only=False):
        """Set end effector target.

        Args:
            target_prim (pxr.Usd.Prim): USD prim of the target. target_prim may also be None, in which case it is up 
                to the policy to specify the desired behavior of the robot. Some policies store a default  c-space 
                configuration in their config files and drive the robot to that position when there is no target 
                specified.
            position_only (bool, optional):  When True, the policy will use only the position (not orientation) of the 
                target_prim as the target. Defaults to False.

        Returns:
            None
        """
        self._motion_policy.set_end_effector_target(target_prim, position_only)

    def create_cube(self, block_prim, side_length=None, static=False):
        """Create a cube obstacle.

        Args:
            block_prim (pxr.Usd.Prim): USD prim representing the cube. Must have pose information.
            side_length (float, optional): [description]. Length of each side of the cube. If not specified, 
                side_length is read from 'size' attribute of block_prim. Defaults to None.
            static (bool, optional): If True, indicate that cube will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if block_prim exists and has required attributes (i.e., size must be specified \
                somewhere, either in block_prim or via side_length param).
        """
        return self._motion_policy.create_cube(block_prim, side_length, static)

    def create_block(self, block_prim, dimensions=None, static=False):
        """Create a block obstacle.

        Args:
            block_prim (pxr.Usd.Prim): USD prim representing the block. Must have pose information.
            dimensions (np.array, optional): Length of block in (x,y,z) dimensions. If not specified, prim must have 
                'xformOp:scale' and "size" attribute. Defaults to None.
            static (bool, optional): If True, indicate that cube will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if block_prim exists and has required attributes (i.e., side lengths must be specified \
                somewhere, either in block_prim or via dimensions param).
        """
        return self._motion_policy.create_block(block_prim, dimensions, static)

    def create_sphere(self, sphere_prim, radius=None, static=False):
        """Create a sphere obstacle.

        Args:
            sphere_prim (pxr.Usd.Prim): USD prim representing the sphere. Must have pose information.
            radius (float, optional): Radius of the sphere. If not specified, radius is read from 'radius' attribute of 
                sphere_prim. Defaults to None.
            static (bool, optional): If True, indicate that cube will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if sphere_prim exists and has required attributes (i.e., radius must be specified \
                somewhere, either in sphere_prim or via radius param).
        """
        return self._motion_policy.create_sphere(sphere_prim, radius, static)

    def create_capsule(self, capsule_prim, radius=None, height=None, static=False):
        """Create a capsule obstacle.

        Args:
            capsule_prim (pxr.Usd.Prim): USD prim representing the capsule. Must have pose information.
            radius (float, optional): Radius of the capsule. If not specified, radius is read from 'radius' attribute 
                of  capsule_prim. Defaults to None.
            height (float, optional): Height of the capsule. If not specified, height is read from 'height' attribute of 
                capsule_prim. Defaults to None.
            static (bool, optional): If True, indicate that cube will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if capsule_prim exists and has required attributes (i.e., radius and height must be \
                specified  somewhere, either in capsule_prim or via radius and height params).
        """
        return self._motion_policy.create_capsule(capsule_prim, radius, height, static)

    def get_prim_pose(self, prim, default_trans=np.zeros(3), default_rot=np.eye(3)):
        """Return pose of prim.
        
        USD prims that lack translational information are placed on the stage at the point (0,0,0). USD prims that lack 
        rotational information are placed on the stage with the identity rotation. Reading translation/rotation 
        information from prims directly yields a 4x4 transform matrix, which necessitates filling in missing information 
        with default information. This method allows the caller to know what information is actually present in the USD 
        prims by passing in None for the defaults.

        Args:
            prim (pxr.Usd.Prim): Prim for which pose will be returned.
            default_trans (np.array, optional): Translation component of pose to be returned
                if the prim has no translational information. Defaults to np.zeros(3).
            default_rot (cp.array, optional): Rotational component of pose to be returned
                if the prim contains no rotational information. Defaults to np.eye(3).

        Returns:
            Tuple[np.array, np.array]: Prim pose returned as translation vector (3 x 1) and rotation matrix  (3 x 3).
        """
        return self._motion_policy.get_prim_pose(prim, default_trans=default_trans, default_rot=default_rot)

    def disable_obstacle(self, obstacle_prim):
        """Disable collision avoidance for obstacle.

        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be disabled.

        Returns:
            bool: Return true if obstacle was identified and successfully disabled.
        """
        return self._motion_policy.disable_obstacle(obstacle_prim)

    def enable_obstacle(self, obstacle_prim):
        """Enable collision avoidance for obstacle.

        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be enabled.

        Returns:
            bool: Return true if obstacle was identified and successfully enabled.
        """
        return self._motion_policy.enable_obstacle(obstacle_prim)

    def remove_obstacle(self, obstacle_prim):
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be removed.

        Returns:
            bool: Return true if obstacle was identified and successfully removed.
        """
        return self._motion_policy.remove_obstacle(obstacle_prim)

    def get_joint_velocity_targets(self):
        """Compute and return joint velocity targets using underlying MotionPolicy.

        Returns:
            np.array: (m x 1) vector of velocity targets, where m is the number of active joints.
        """
        joint_positions, joint_velocities, joint_accel = self.get_joint_states()
        aji = self._active_joint_inds

        velocity_targets = self._dc.get_articulation_dof_velocity_targets(self._ar)
        velocity_targets[aji] = self._motion_policy.get_joint_velocity_targets(
            joint_positions[aji], joint_velocities[aji], self.sim_timestep
        )
        return velocity_targets

    def get_joint_position_targets(self):
        """Compute and return joint position targets using underlying MotionPolicy.

        Active joint targets are computed by MotionPolicy. Position targets for non-active joints are kept identical
        to those currently set in the articulation.

        Returns:
            np.array: (m x 1) vector of position targets, where m is the total number of joints.
        """
        joint_positions, joint_velocities, joint_accel = self.get_joint_states()
        aji = self._active_joint_inds

        position_targets = self._dc.get_articulation_dof_position_targets(self._ar)
        position_targets[aji] = self._motion_policy.get_joint_position_targets(
            joint_positions[aji], joint_velocities[aji], self.sim_timestep
        )
        return position_targets

    def get_motion_policy(self):
        """
        It can be convenient to interact directly with the low level motion policy for testing and development,
        but in general the policy should be designed to function using only the motion_policy_interface.
        
        Returns:
            MotionPolicy: Underlying motion policy used by MotionGenerator.
        """
        return self._motion_policy

    def _zero_robot_velocity(self):
        """Set robot joint velocities to zero.
        
        Returns:
            None
        """
        # Instantaneously set the robot's velocity to zero (used on initialization).
        dof_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_VEL)
        dof_states["vel"] = np.zeros_like(dof_states["vel"])
        self._dc.set_articulation_dof_states(self._ar, dof_states, _dynamic_control.STATE_VEL)

    def _configure_position_control(self):
        """Configure articulation for position control.

        Returns:
            None
        """
        self._zero_robot_velocity()

    def _configure_velocity_control(self, damping):
        """Configure articulation for velocity control.

        Returns:
            None
        """
        self._zero_robot_velocity()

        props = _dynamic_control.DofProperties()
        props.drive_mode = _dynamic_control.DRIVE_FORCE
        props.damping = damping
        props.stiffness = 0

        for ind in self._active_joint_inds:
            self._dc.set_dof_properties(self._dc.find_articulation_dof(self._ar, self._active_joints[ind]), props)

    def _set_joint_velocity_targets(self, joint_velocities):
        """Set joint velocity targets.

        Args:
            joint_velocities (np.array): (m x 1) vector of joint velocities, where m is the total number of joints.

        Returns:
            None
        """
        self._dc.wake_up_articulation(self._ar)
        self._dc.set_articulation_dof_velocity_targets(self._ar, joint_velocities.astype(np.float32))

    def _set_joint_position_targets(self, joint_positions):
        """Set joint position targets.

        Args:
            joint_positions (np.array): (m x 1) vector of joint positions, where m is the total number of joints.

        Returns:
            None
        """
        self._dc.wake_up_articulation(self._ar)
        self._dc.set_articulation_dof_position_targets(self._ar, joint_positions.astype(np.float32))

    def _follow_velocity_policy(self):
        """Follow joint velocity policy.

        Returns:
            None
        """
        joint_velocities = self.get_joint_velocity_targets()
        self._set_joint_velocity_targets(joint_velocities)

    def _follow_position_policy(self):
        """Follow joint position policy.

        Returns:
            None
        """
        joint_positions = self.get_joint_position_targets()
        self._set_joint_position_targets(joint_positions)
