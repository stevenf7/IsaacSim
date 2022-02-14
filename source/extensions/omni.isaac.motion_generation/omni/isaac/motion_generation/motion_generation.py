# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import carb
from .lula_motion_policies import *
from .motion_policy_interface import *
from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.utils.types import ArticulationAction, JointsState
import omni.isaac.core.objects as objects
from omni.isaac.core.objects import cuboid, sphere, capsule, cylinder, cone, ground_plane
from pxr import Usd


class MotionGenerator:
    """Interface for running MotionPolicy on simulated robots.
    """

    def __init__(self) -> None:
        self.initialized = False

    def initialize(self, policy_config: dict, robot_prim_path: str, sim_fps: float) -> None:
        """Initialize MotionGenerator.

        Args:
            policy_config (dict): Dictionary containing the necessary configurations for a motion policy. 
                policy_config must specify "policy_type" to select a specific motion policy such as "RMPflow". 
                All other specifications are policy dependent.
            robot_prim (str): Path to USD prim for the robot
            sim_fps (float): Frequency at which Isaac Sim updates the world, typically 60 Hz

        Returns:
            None
        """

        self.sim_timestep = 1 / sim_fps

        # initialize motion policy
        if "policy_type" not in policy_config:
            carb.log_error("Required arg policy_type was not specified in policy_config")
            return

        self._robot_articulation = Articulation(robot_prim_path)
        self._robot_articulation.initialize()

        if policy_config["policy_type"] == "RMPflow":
            self._motion_policy = RmpFlow(policy_config, self._robot_articulation)
        else:
            carb.log_error("invalid value of policy_type in policy_config")
            return  # still uninitialized

        if not self._motion_policy.initialized:
            return  # still uninitialized

        # initialize controller
        self._articulation_controller = self._robot_articulation.get_articulation_controller()

        self._active_joints = self._motion_policy.get_active_joints()

        self._active_joint_inds = [self._robot_articulation.get_dof_index(joint) for joint in self._active_joints]

        if self._motion_policy.policy_type == PolicyType.VELOCITY:
            self._articulation_controller.switch_control_mode("velocity")
        else:
            self._articulation_controller.switch_control_mode("position")

        self.initialized = self._motion_policy.initialized

    def is_initialized(self) -> bool:
        """Indicates whether MotionGenerator has been initialized.

        Returns:
            bool: Return True if MotionGenerator has been initialized. Else return False.
        """
        return self.initialized

    def move(self, updated_obstacles: typing.List[Usd.Prim] = None) -> None:
        """Generate new joint targets using MotionPolicy and apply joint targets to the robot.
        
        Args:
            updated_obstacles (list, optional): List of obstacles that need to have their poses updated. 
                If provided, only these obstacles will have their poses updated. Defaults to None.

        Return:
            None
        """
        self._motion_policy.update(updated_obstacles=updated_obstacles)  # update motion_policy internal world state

        action = self.get_next_articulation_action()
        self._articulation_controller.apply_action(action)

    def get_next_articulation_action(self) -> ArticulationAction:
        """Return ArticulationAction for the next frame following the underlying MotionPolicy

        Returns: 
            ArticulationAction: Desired position/velocity target for the robot in the next frame
        """

        if self._motion_policy.policy_type == PolicyType.VELOCITY:
            action = self._get_joint_velocity_targets()

        if self._motion_policy.policy_type == PolicyType.POSITION:
            action = self._get_joint_position_targets()

        return action

    def get_joint_states(self) -> typing.Tuple[np.array, np.array, np.array]:
        """Return the states (position, velocity and acceleration) of all robot joints.

        Returns:
            Tuple[np.array, np.array, np.array]: States (position, velcocity and acceleration) for all robot joints.
        """
        joints_state = self._robot_articulation.get_joints_state()
        return joints_state.positions, joints_state.velocities, joints_state.efforts

    def get_active_joint_states(self) -> typing.Tuple[np.array, np.array, np.array]:
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

    def get_end_effector_pose(self) -> typing.Tuple[np.array, np.array, np.array]:
        """Return current pose of the end effector.

        Returns:
            Tuple[np.array, np.array]: End effector pose returned as translation vector (3 x 1) and rotation matrix (3 x 3).
        """
        joint_poses = self.get_active_joint_states()[0]
        return self._motion_policy.get_end_effector_pose(joint_poses)

    def set_cspace_target(self, target: np.array) -> None:
        """Set configuration space target for the robot.

        Args:
            target (np.array): Desired configuration for the robot as (m x 1) vector where m is the number of active 
                joints.

        Returns:
            None
        """
        self._motion_policy.set_cspace_target(target)

    def set_end_effector_target(self, target_translation=None, target_orientation=None) -> None:
        """Set end effector target.

        Args:
            target_translation (nd.array): Translation vector (3x1) for robot end effector
            target_orientation (nd.array): Quaternion of desired rotation for robot end effector 

        Returns:
            None
        """
        self._motion_policy.set_end_effector_target(target_translation, target_orientation)

    def add_obstacle(self, obstacle: omni.isaac.core.objects) -> None:
        """Add an obstacle 

        Args:
            obstacle (omni.isaac.core.objects): An obstacle from the package omni.isaac.core.obstacles
                            The type of the obstacle will be checked, and the appropriate adder will be called
                            --Dynamic obstacles will be assumed to move over time
                            --Fixed obstacles will be assumed to remain static

        Returns:
            None
        """

        if isinstance(obstacle, cuboid.DynamicCuboid):
            self._motion_policy.add_cuboid(obstacle, static=False)
        elif isinstance(obstacle, cuboid.FixedCuboid):
            self._motion_policy.add_cuboid(obstacle, static=True)

        elif isinstance(obstacle, cylinder.DynamicCylinder):
            self._motion_policy.add_cylinder(obstacle, static=False)
        # elif isinstance(obstacle, cylinder.FixedCylinder):
        #     self._motion_policy.add_cylinder(obstacle,static=True)

        elif isinstance(obstacle, sphere.DynamicSphere):
            self._motion_policy.add_sphere(obstacle, static=False)
        # elif isinstance(obstacle,sphere.FixedSphere):
        #     self._motion_policy.add_sphere(obstacle,static=True)

        elif isinstance(obstacle, capsule.DynamicCapsule):
            self._motion_policy.add_capsule(obstacle, static=False)
        # elif isinstance(obstacle,capsule.FixedCapsule):
        #     self._motion_policy.add_capsule(obstacle,static=True)

        elif isinstance(obstacle, cone.DynamicCone):
            self._motion_policy.add_cone(obstacle, static=False)
        # elif isinstance(obstacle,cone.FixedCone):
        #     self._motion_policy.add_cone(obstacle,static=True)

        elif isinstance(obstacle, ground_plane.GroundPlane):
            self._motion_policy.add_ground_plane(obstacle)

        else:
            carb.log_warning(
                "Obstacle added with unsuported type: "
                + str(type(obstacle))
                + "\nObstacle should be from the package omni.isaac.core.objects"
            )

    def disable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Disable collision avoidance for obstacle.

        Args:
            obstacle_prim (core.object): USD prim for obstacle to be disabled.

        Returns:
            bool: Return true if obstacle was identified and successfully disabled.
        """
        return self._motion_policy.disable_obstacle(obstacle)

    def enable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Enable collision avoidance for obstacle.

        Args:
            obstacle_prim (core.object): USD prim for obstacle to be enabled.

        Returns:
            bool: Return true if obstacle was identified and successfully enabled.
        """
        return self._motion_policy.enable_obstacle(obstacle)

    def remove_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle_prim (core.object): USD prim for obstacle to be removed.

        Returns:
            bool: Return true if obstacle was identified and successfully removed.
        """
        return self._motion_policy.remove_obstacle(obstacle)

    def _get_joint_velocity_targets(self) -> ArticulationAction:
        """Compute and return joint velocity targets using underlying MotionPolicy.

        Returns:
            ArticulationAction: Wrapper object containing velocity targets for the robot
        """
        aji = self._active_joint_inds

        joint_positions, joint_velocities, _ = self.get_active_joint_states()

        velocity_targets = self._motion_policy.get_joint_velocity_targets(
            joint_positions, joint_velocities, self.sim_timestep
        )

        velocity_action = [None] * self._robot_articulation.num_dof
        for ind in aji:
            velocity_action[ind] = velocity_targets[ind]

        return ArticulationAction(joint_velocities=velocity_action)

    def _get_joint_position_targets(self) -> ArticulationAction:
        """Compute and return joint position targets using underlying MotionPolicy.

        Active joint targets are computed by MotionPolicy. Position targets for non-active joints are kept identical
        to those currently set in the articulation.

        Returns:
            ArticulationAction: Wrapper object containing position targets for the robot
        """
        aji = self._active_joint_inds

        joint_positions, joint_velocities, _ = self.get_active_joint_states()

        position_targets = self._motion_policy.get_joint_position_targets(
            joint_positions, joint_velocities, self.sim_timestep
        )

        position_action = [None] * self._robot_articulation.num_dof
        for ind in aji:
            position_action[ind] = position_targets[ind]

        return ArticulationAction(joint_positions=position_action)

    def get_motion_policy(self) -> MotionPolicy:
        """
        It can be convenient to interact directly with the low level motion policy for testing and development,
        but in general the policy should be designed to function using only the motion_policy_interface.
        
        Returns:
            MotionPolicy: Underlying motion policy used by MotionGenerator.
        """
        return self._motion_policy
