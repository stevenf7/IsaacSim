# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from pxr import Usd, UsdGeom
from enum import Enum
import numpy as np
import carb
import typing
import omni.isaac.core.objects
from omni.isaac.core.objects import cuboid, sphere, capsule, cylinder, cone, ground_plane


class PolicyType(Enum):
    VELOCITY = 1
    POSITION = 2


class MotionPolicy:
    """Interface for implementing motion policies for compatibility with `MotionGenerator` interface.
    """

    def __init__(self, policy_type: PolicyType) -> None:
        self.initialized = False
        self.policy_type = policy_type

    def set_initialized(self) -> None:
        """Set self.initialized to True after a successful initialization.

        Returns:
            None
        """
        self.initialized = True

    def update(self, updated_obstacles: typing.List[Usd.Prim] = None) -> None:
        """Applies all necessary updates to the internal world/robot state.

        Args:
            updated_obstacles (list, optional): If provided, only the given obstacles will have their poses updated.
                For motion policies that use obstacle poses relative to the robot base (e.g. Lula based planners), 
                this list will be ignored if the robot base has moved because all object poses will have changed 
                relative to the robot. Defaults to None.
        
        Returns:
            None
        """
        pass

    def get_joint_velocity_targets(
        self, joint_positions: np.array, joint_velocities: np.array, frame_duration: float
    ) -> np.array:
        """Compute new velocity targets based on robot state.

        This function will be used by MotionGenerator to set a velocity target at every frame.
        This function only needs to be implemented if the MotionPolicy has the PolicyType VELOCITY_POLICY

        Args:
            joint_positions (np.array): (m x 1) vector with position of each active robot joint.
            joint_velocities (np.array): (m x 1) vector with velocity of each active robot joint.
            frame_duration (float): Duration of a single frame of simulation in seconds.

        Returns:
            np.array: (m x 1) vector with velocity target for each active joint.
        """
        return np.zeros_like(joint_positions)

    def get_joint_position_targets(
        self, joint_positions: np.array, joint_velocities: np.array, frame_duration: float
    ) -> np.array:
        """Compute new position targets based on robot state.

        This function will be used by MotionGenerator to set a position target at every frame.
        This function only needs to be implemented if the MotionPolicy has the PolicyType POSITION_POLICY

        Args:
            joint_positions (np.array): (m x 1) vector with position of each active robot joint.
            joint_velocities (np.array): (m x 1) vector with velocity of each active robot joint.
            frame_duration (float): Duration of a single frame of simulation in seconds.

        Returns:
            np.array: (m x 1) vector with position target for each active joint.
        """
        return np.zeros_like(joint_positions)

    def get_active_joints(self) -> typing.List[str]:
        """Return names of active joints.

        Some articulated robot joints may be ignored by some policies. E.g., the gripper of the Franka arm is not used 
        to follow targets, and the RMPflow config files excludes the joints in the gripper from the list of articulated 
        joints.

        Returns:
            list of str: names of active joints.
        """
        return []

    def set_cspace_target(self, target: np.array) -> None:
        """Set configuration space target for the robot.

        Args:
            target (np.array): Desired configuration for the robot as (m x 1) vector where m is the number of active 
                joints.

        Returns:
            None
        """
        pass

    def set_end_effector_target(self, target_translation=None, target_orientation=None) -> None:
        """Set end effector target.

        Args:
            target_translation (nd.array): Translation vector (3x1) for robot end effector
            target_orientation (nd.array): Quaternion of desired rotation for robot end effector 

        Returns:
            None
        """
        pass

    def get_end_effector_pose(self, joint_positions: np.array) -> typing.Tuple[np.array, np.array, np.array]:
        """Return pose of the end effector at the given end effector position.

        Args:
            joint_positions (np.array): (m x 1) vector of joint positions for which to compute forward kinematics.

        Returns:
            Tuple[np.array, np.array]: End effector pose returned as translation vector (3 x 1) and rotation matrix (3 x 3).
        """
        pass

    def add_cuboid(self, cuboid: cuboid.DynamicCuboid, static: bool = False) -> bool:
        """Add a block obstacle.

        Args:
            cuboid (cuboid.DynamicCuboid): Wrapper object for handling rectangular prism Usd Prims.
            static (bool, optional): If True, indicate that cuboid will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_cuboid()
        """
        carb.log_warning("Function create_cuboid() has not been implemented for this MotionPolicy")
        return False

    def add_sphere(self, sphere: sphere.DynamicSphere, static: bool = False) -> bool:
        """Add a sphere obstacle.

        Args:omni.isaac.core.objectshange pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_sphere()
        """
        carb.log_warning("Function create_sphere() has not been implemented for this MotionPolicy")
        return False

    def add_capsule(self, capsule: capsule.DynamicCapsule, static: bool = False) -> bool:
        """Add a capsule obstacle.

        Args:
            capsule (capsule.DynamicCapsule): Wrapper object for handling capsule Usd Prims.
            static (bool, optional): If True, indicate that capsule will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_capsule()
        """
        carb.log_warning("Function create_capsule() has not been implemented for this MotionPolicy")
        return False

    def add_cylinder(self, cylinder: cylinder.DynamicCylinder, static: bool = False) -> bool:
        """Add a cylinder obstacle.

        Args:
            cylinder (cylinder.DynamicCylinder): Wrapper object for handling cylinder Usd Prims.
            static (bool, optional): If True, indicate that cylinder will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_cylinder()
        """
        carb.log_warning("Function create_cylinder() has not been implemented for this MotionPolicy")
        return False

    def add_cone(self, cone: cone.DynamicCone, static: bool = False) -> bool:
        """Add a cone obstacle.

        Args:
            cone (cone.DynamicCylinder): Wrapper object for handling cone Usd Prims.
            static (bool, optional): If True, indicate that cone will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_cone()
        """
        carb.log_warning("Function create_cone() has not been implemented for this MotionPolicy")
        return False

    def add_ground_plane(self, ground_plane: ground_plane.GroundPlane) -> bool:
        """Add a ground_plane

        Args:
            ground_plane (ground_plane.DynamicCylinder): Wrapper object for handling ground_plane Usd Prims.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented create_ground_plane()
        """
        carb.log_warning("Function create_ground_plane() has not been implemented for this MotionPolicy")
        return False

    def disable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Disable collision avoidance for obstacle.

        Args:
            obstacle (core.object): obstacle to be disabled.

        Returns:
            bool: Return true if obstacle was identified and successfully disabled.
        """
        carb.log_warning("Function disable_obstacle() has not been implemented for this MotionPolicy")
        return False

    def enable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Enable collision avoidance for obstacle.

        Args:
            obstacle (core.object): obstacle to be enabled.

        Returns:
            bool: Return true if obstacle was identified and successfully enabled.
        """
        carb.log_warning("Function enable_obstacle() has not been implemented for this MotionPolicy")
        return False

    def remove_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle (core.object): obstacle to be removed.

        Returns:
            bool: Return true if obstacle was identified and successfully removed.
        """
        carb.log_warning("Function remove_obstacle() has not been implemented for this MotionPolicy")
        return False
