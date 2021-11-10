# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from pxr import UsdGeom
from enum import Enum
import numpy as np
import copy


class PolicyType(Enum):
    VELOCITY = 1
    POSITION = 2


class MotionPolicy:
    """Interface for implementing motion policies for compatibility with `MotionGenerator` interface.
    """

    def __init__(self, _stage, policy_type):
        self._stage = _stage
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._target_prim = None
        self._target_prim_is_position_only = None
        self.initialized = False
        self.policy_type = policy_type

    def set_initialized(self):
        """Set self.initialized to True after a successful initialization.

        Returns:
            None
        """
        self.initialized = True

    def update(self, updated_obstacles=None):
        """Applies all necessary updates to the internal world/robot state.

        Args:
            updated_obstacles (list, optional): If provided, only the given obstacles will have their poses updated.
                For motion policies that use obstacle poses relative to the robot base (e.g. Lula based planners), 
                this list will be ignored if the robot base has moved because all object poses will have changed 
                relative to the robot. Defaults to None.
        """
        pass

    def get_joint_velocity_targets(self, joint_positions, joint_velocities, frame_duration):
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

    def get_joint_position_targets(self, joint_positions, joint_velocities, frame_duration):
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

    def get_active_joints(self):
        """Return names of active joints.

        Some articulated robot joints may be ignored by some policies. E.g., the gripper of the Franka arm is not used 
        to follow targets, and the RMPflow config files excludes the joints in the gripper from the list of articulated 
        joints.

        Returns:
            list of str: names of active joints.
        """
        return []

    def set_cspace_target(self, target):
        """Set configuration space target for the robot.

        Args:
            target (np.array): Desired configuration for the robot as (m x 1) vector where m is the number of active 
                joints.

        Returns:
            None
        """
        pass

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
        self._target_prim = target_prim
        self._target_prim_is_position_only = position_only

    def get_end_effector_pose(self, joint_positions):
        """Return current pose of the end effector.

        Returns:
            Tuple[np.array, np.array]: End effector pose returned as translation vector (3 x 1) and rotation matrix (3 x 3).
        """
        pass

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
        xform = UsdGeom.Xformable(prim)
        if xform.GetXformOpOrderAttr().Get() is None:
            return default_trans, default_rot

        attr_name_base = "xformOp:"

        rotation_attrs = [
            "transform",
            "orient",
            "rotateX",
            "rotateXYZ",
            "rotateXZY",
            "rotateY",
            "rotateYXZ",
            "rotateYZX",
            "rotateZ",
            "rotateZYX",
            "rotateZXY",
        ]
        rotation_attrs = [attr_name_base + r for r in rotation_attrs]

        translation_attrs = ["transform", "translate"]
        translation_attrs = [attr_name_base + t for t in translation_attrs]

        has_rot_attr = False
        has_trans_attr = False
        for op in xform.GetXformOpOrderAttr().Get():
            if op in rotation_attrs:
                has_rot_attr = True
            if op in translation_attrs:
                has_trans_attr = True

        mat = xform.GetLocalTransformation()

        if has_trans_attr:
            trans = np.array(mat.ExtractTranslation())
        else:
            trans = default_trans

        # GfMatrix4d() objects have transposed rotation matrices
        # rotation matrix may not have normalized rows due to xformOp:scale
        if has_rot_attr:
            rot = np.array(mat.ExtractRotationMatrix()).T
            row_norms = np.linalg.norm(rot, axis=1)
            rot = rot / row_norms[:, np.newaxis]
        else:
            rot = default_rot

        return self._meters_per_unit * trans, rot

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
        return False

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
        return False

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
        return False

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
        return False

    def disable_obstacle(self, obstacle_prim):
        """Disable collision avoidance for obstacle.

        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be disabled.

        Returns:
            bool: Return true if obstacle was identified and successfully disabled.
        """
        return False

    def enable_obstacle(self, obstacle_prim):
        """Enable collision avoidance for obstacle.

        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be enabled.

        Returns:
            bool: Return true if obstacle was identified and successfully enabled.
        """
        return False

    def remove_obstacle(self, obstacle_prim):
        """Remove obstacle from collision avoidance. Obstacle cannot be re-enabled via enable_obstacle() after 
        removal.
        
        Args:
            obstacle_prim (pxr.Usd.Prim): USD prim for obstacle to be removed.

        Returns:
            bool: Return true if obstacle was identified and successfully removed.
        """
        return False
