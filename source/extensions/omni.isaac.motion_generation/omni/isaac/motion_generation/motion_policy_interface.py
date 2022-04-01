# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
import numpy as np
import carb
from typing import Tuple, List, Union
import omni.isaac.core.objects
from omni.isaac.core.objects import cuboid, sphere, capsule, cylinder, cone, ground_plane


class MotionPolicy:
    """Interface for implementing motion policies for compatibility with `MotionGenerator` interface.
    """

    def __init__(self) -> None:
        pass

    def update_world(self, updated_obstacles: List = None) -> None:
        """Applies all necessary updates to the internal world representation.

        Args:
            updated_obstacles (list, optional): If provided, only the given obstacles will have their poses updated.
                For motion policies that use obstacle poses relative to the robot base (e.g. Lula based policies), 
                this list will be ignored if the robot base has moved because all object poses will have changed 
                relative to the robot. Defaults to None.
        
        Returns:
            None
        """
        pass

    def set_robot_base_pose(self, robot_translation: np.array, robot_orientation: np.array):
        """Update position of the robot base. 

        Args:
            robot_translation (np.array): (3 x 1) translation vector describing the translation of the robot base relative to the USD stage origin.
                The translation vector should be specified in the units of the USD stage
            robot_orientation (np.array): (4 x 1) quaternion describing the orientation of the robot base relative to the USD stage global frame
        """
        pass

    def compute_joint_targets(
        self,
        active_joint_positions: np.array,
        active_joint_velocities: np.array,
        watched_joint_positions: np.array,
        watched_joint_velocities: np.array,
        frame_duration: float,
    ) -> Tuple[np.array, np.array]:
        """Compute position and velocity targets for the next frame given the current robot state.
        Position and velocity targets are used in Isaac Sim to generate forces using the PD equation
        kp*(joint_position_targets-joint_positions) + kd*(joint_velocity_targets-joint_velocities).

        Args:
            active_joint_positions (np.array): current positions of joints specified by get_active_joints()
            active_joint_velocities (np.array): current velocities of joints specified by get_active_joints()
            watched_joint_positions (np.array): current positions of joints specified by get_watched_joints()
            watched_joint_velocities (np.array): current velocities of joints specified by get_watched_joints()
            frame_duration (float): duration of the physics frame

        Returns:
            Tuple[np.array,np.array]: 
            joint position targets for the active robot joints for the next frame \n
            joint velocity targets for the active robot joints for the next frame 
        """

        return active_joint_positions, np.zeros_like(active_joint_velocities)

    def get_active_joints(self) -> List[str]:
        """Active joints are directly controlled by this MotionPolicy

        Some articulated robot joints may be ignored by some policies. E.g., the gripper of the Franka arm is not used 
        to follow targets, and the RMPflow config files excludes the joints in the gripper from the list of articulated 
        joints.

        Returns:
            List[str]: names of active joints.  The order of joints in this list determines the order in which a 
            MotionPolicy expects joint states to be specified in functions like compute_joint_targets(active_joint_positions,...)
        """
        return []

    def get_watched_joints(self) -> List[str]:
        """Watched joints are joints whose position/velocity matters to the MotionPolicy, but are not directly controlled.
        e.g. A MotionPolicy may control a robot arm on a mobile robot.  The joint states in the rest of the robot directly affect the position of the arm, but they are not actively controlled by this MotionPolicy

        Returns:
            List[str]: Names of joints that are being watched by this MotionPolicy. The order of joints in this list determines the order in which a 
            MotionPolicy expects joint states to be specified in functions like compute_joint_targets(...,watched_joint_positions,...)
        """
        return []

    def set_cspace_target(self, active_joint_targets: np.array) -> None:
        """Set configuration space target for the robot.

        Args:
            active_joint_target (np.array): Desired configuration for the robot as (m x 1) vector where m is the number of active 
                joints.

        Returns:
            None
        """
        pass

    def set_end_effector_target(self, target_translation=None, target_orientation=None) -> None:
        """Set end effector target.

        Args:
            target_translation (nd.array): Translation vector (3x1) for robot end effector.
                Target translation should be specified in the same units as the USD stage, relative to the stage origin.
            target_orientation (nd.array): Quaternion of desired rotation for robot end effector relative to USD stage global frame  

        Returns:
            None
        """
        pass

    def add_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Add an obstacle 

        Args:
            obstacle (omni.isaac.core.objects): An obstacle from the package omni.isaac.core.obstacles
                            The type of the obstacle will be checked, and the appropriate add function will be called \n
                            --Dynamic obstacles will be assumed to move over time e.g. objects.cuboid.DynamicCuboid, objects.sphere.DynamicSphere \n
                            --Visual obstacles will be assumed to move over time e.g. objects.cuboid.VisualCuboid, objects.sphere.VisualSphere \n
                            --Fixed obstacles will be assumed to remain static.  Currently objects.cuboid.FixedCuboid is the only Fixed obstacle type

        Returns:
            success (bool): Returns True if the obstacle type is valid and the appropriate add function has been implemented
        """

        # Some object types have not been added to core.objects yet, but will be added in the future
        # Will uncomment lines below when types are added to core.objects

        if isinstance(obstacle, cuboid.DynamicCuboid) or isinstance(obstacle, cuboid.VisualCuboid):
            return self.add_cuboid(obstacle, static=False)
        elif isinstance(obstacle, cuboid.FixedCuboid):
            return self.add_cuboid(obstacle, static=True)

        elif isinstance(obstacle, cylinder.DynamicCylinder) or isinstance(obstacle, cylinder.VisualCylinder):
            return self.add_cylinder(obstacle, static=False)
        # elif isinstance(obstacle, cylinder.FixedCylinder):
        #     self.add_cylinder(obstacle,static=True)

        elif isinstance(obstacle, sphere.DynamicSphere) or isinstance(obstacle, sphere.VisualSphere):
            return self.add_sphere(obstacle, static=False)
        # elif isinstance(obstacle,sphere.FixedSphere):
        #     self.add_sphere(obstacle,static=True)

        elif isinstance(obstacle, capsule.DynamicCapsule) or isinstance(obstacle, capsule.VisualCapsule):
            return self.add_capsule(obstacle, static=False)
        # elif isinstance(obstacle,capsule.FixedCapsule):
        #     self.add_capsule(obstacle,static=True)

        elif isinstance(obstacle, cone.DynamicCone) or isinstance(obstacle, cone.VisualCone):
            return self.add_cone(obstacle, static=False)
        # elif isinstance(obstacle,cone.FixedCone):
        #     self.add_cone(obstacle,static=True)

        elif isinstance(obstacle, ground_plane.GroundPlane):
            return self.add_ground_plane(obstacle)

        else:
            carb.log_warning(
                "Obstacle added with unsuported type: "
                + str(type(obstacle))
                + "\nObstacle should be from the package omni.isaac.core.objects"
            )
            return False

    def add_cuboid(
        self, cuboid: Union[cuboid.DynamicCuboid, cuboid.FixedCuboid, cuboid.VisualCuboid], static: bool = False
    ):
        """Add a block obstacle.

        Args:
            cuboid (core.objects.cuboid): Wrapper object for handling rectangular prism Usd Prims.
            static (bool, optional): If True, indicate that cuboid will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_cuboid()
        """
        carb.log_warning("Function add_cuboid() has not been implemented for this MotionPolicy")
        return False

    def add_sphere(self, sphere: Union[sphere.DynamicSphere, sphere.VisualSphere], static: bool = False) -> bool:
        """Add a sphere obstacle.

        Args:
            sphere (core.objects.sphere): Wrapper object for handling sphere Usd Prims.
            static (bool, optional): If True, indicate that sphere will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_sphere()
        """
        carb.log_warning("Function add_sphere() has not been implemented for this MotionPolicy")
        return False

    def add_capsule(self, capsule: Union[capsule.DynamicCapsule, capsule.VisualCapsule], static: bool = False) -> bool:
        """Add a capsule obstacle.

        Args:
            capsule (core.objects.capsule): Wrapper object for handling capsule Usd Prims.
            static (bool, optional): If True, indicate that capsule will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_capsule()
        """
        carb.log_warning("Function add_capsule() has not been implemented for this MotionPolicy")
        return False

    def add_cylinder(
        self, cylinder: Union[cylinder.DynamicCylinder, cylinder.VisualCylinder], static: bool = False
    ) -> bool:
        """Add a cylinder obstacle.

        Args:
            cylinder (core.objects.cylinder): Wrapper object for handling rectangular prism Usd Prims.
            static (bool, optional): If True, indicate that cuboid will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_cylinder()
        """
        carb.log_warning("Function add_cylinder() has not been implemented for this MotionPolicy")
        return False

    def add_cone(self, cone: Union[cone.DynamicCone, cone.VisualCone], static: bool = False) -> bool:
        """Add a cone obstacle.

        Args:
            cone (core.objects.cone): Wrapper object for handling cone Usd Prims.
            static (bool, optional): If True, indicate that cone will never change pose, and may be ignored in internal 
                world updates. Defaults to False.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_cone()
        """
        carb.log_warning("Function add_cone() has not been implemented for this MotionPolicy")
        return False

    def add_ground_plane(self, ground_plane: ground_plane.GroundPlane) -> bool:
        """Add a ground_plane

        Args:
            ground_plane (core.objects.ground_plane.GroundPlane): Wrapper object for handling ground_plane Usd Prims.

        Returns:
            bool: Return True if underlying MotionPolicy has implemented add_ground_plane()
        """
        carb.log_warning("Function add_ground_plane() has not been implemented for this MotionPolicy")
        return False

    def disable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Disable collision avoidance for obstacle.

        Args:
            obstacle (core.object): obstacle to be disabled.

        Returns:
            bool: Return True if obstacle was identified and successfully disabled.
        """
        carb.log_warning("Function disable_obstacle() has not been implemented for this MotionPolicy")
        return False

    def enable_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Enable collision avoidance for obstacle.

        Args:
            obstacle (core.object): obstacle to be enabled.

        Returns:
            bool: Return True if obstacle was identified and successfully enabled.
        """
        carb.log_warning("Function enable_obstacle() has not been implemented for this MotionPolicy")
        return False

    def remove_obstacle(self, obstacle: omni.isaac.core.objects) -> bool:
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle (core.object): obstacle to be removed.

        Returns:
            bool: Return True if obstacle was identified and successfully removed.
        """
        carb.log_warning("Function remove_obstacle() has not been implemented for this MotionPolicy")
        return False

    def reset(self) -> None:
        """Reset all state inside the MotionPolicy to its initial values

        """
        pass
