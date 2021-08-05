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
from scipy.spatial.transform import Rotation as R


class PolicyType(Enum):
    ACCELERATION = 0
    VELOCITY = 1
    POSITION = 2


class MotionPolicy:
    def __init__(self, _stage, policy_type):
        self._stage = _stage
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._target_prim = None
        self.initialized = False
        self.policy_type = policy_type

    def set_initialized(self):
        """
        set self.initialized to True after a successful initialization
        """
        self.initialized = True

    def update(self, updated_obstacles=None):
        """
        applies all necessary updates to the internal world/robot state

        Param updated_obstacles (list): if provided, only the given obstacles will have their poses updated
                For motion policies that use obstacle poses relative to the robot base
                (e.g. Lula based planners) this list will be ignored if the robot base has moved
                because all object poses will have changed relative to the robot.
        """
        pass

    def evaluate_acceleration(self, joint_position, joint_velocity):
        """
        Params:
                joint_position (m x 1): positions of each joint
                joint_velocity (m x 1): velocity of each joint
        Return:
                joint_acceleration (m x 1): a function of robot state, world state, and target
        """
        return np.zeros_like(joint_position)

    def get_active_joints(self):
        """
        Return:
                The names of joints that the motion policy considers to be active
                in the order the policy expects them.  Some articulated robot joints may be
                ignored by some policies.  e.g. The gripper of the Franka arm is not used to
                follow targets, and the RMPflow config files excludes the joints
                in the gripper from the list of articulated joints.
        """
        return []

    def set_cspace_target(self, target):
        """
        Args:
                target (m x 1): desired configuration for the robot,
                where m is the number of active joints
        Return:
                None
        """

    def set_end_effector_target(self, target_prim):
        """
        Args:
                param prim : the usd prim of the target
                    target_prim may also be None, in which case it is up to the policy
                    to specify the desired behavior of the robot.
                    Some policies store a default c-space configuration in their config files
                    and drive the robot to that position when there is no target specified
        Return:
                None
        """
        self._target_prim = target_prim

    def get_end_effector_pose(self, joint_positions):
        """
        Args:
            positions of active joints
        Returns:
            pose of end effector in the world frame
            np array (3x1) translation
            np array (3x3) rotation matrix
        """
        pass

    def get_prim_pose(self, prim, default_trans=np.zeros(3), default_rot=np.eye(3)):
        """
        Args:
                param prim : the usd prim of the object
                param default_trans: the translation component of pose to be returned
                    if the prim has no translational information
                param default_rot: the rotational component of pose to be returned
                    if the prim contains no rotational information

                USD prims that lack translational information are placed on the stage at the 
                point (0,0,0)
                USD prims that lack rotational information are placed on the stage with the 
                identity rotation
                Reading translation/rotation information from prims directly yields a 4x4 
                transform matrix, which necessitates filling in missing information with 
                default information.
                This method allows the caller to know what information is actually present in the USD prims
                by passing in None for the defaults.

        Return:
                pos (np array): 3D translation of prim
                rot (np array): Rotation Matrix for prim
        """
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

        xform = UsdGeom.Xformable(prim)
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
        """
        Args:
                param block_prim: the usd prim of the cube
                        prim must have pose information
                param side_length (scalar):
                        if not specified, side_length is read from 'size' attribute of prim
                param static (bool): this object will never move or change, and may be ignored
                        in internal world updates.

        Return:
                bool success: block_prim exists and has required attributes;
                size must be specified somewhere
        """

        return False

    def create_block(self, block_prim, dimensions=None, static=False):
        """
        Args:
                param block_prim: the usd prim of the cube
                        prim must have pose information
                param dimensions (np.array):
                        length of block in (x,y,z) dimensions
                        if not specified, prim must have 'xformOp:scale' and "size" attribute
                param static (bool): this object will never move or change, and may be ignored
                        in internal world updates.

        Return:
                bool success: block_prim exists and has required attributes
        """
        return False

    def create_sphere(self, sphere_prim, radius=None, static=False):
        """
        Args:
                param sphere_prim: the usd prim of the sphere
                        prim must have pose information
                param radius (scalar):
                        if not specified, radius is read from 'radius' attribute of prim
                param static (bool): this object will never move or change, and may be ignored
                        in internal world updates.

        Return:
                bool success: sphere_prim exists and has required attributes;
                radius must be specified somewhere
        """

        return False

    def create_capsule(self, capsule_prim, radius=None, height=None, static=False):
        """
        Args:
                param capsule_prim: the usd prim of the capsule
                        prim must have pose information
                param radius (scalar):
                        if not specified, radius is read from 'radius' attribute of prim
                param height (scalar):
                        if not specified, height is read from 'height' attribute of prim
                param static (bool): this object will never move or change

                A capsule is defined as the space that is within "radius" of a line segment
                with length "height".

        Return:
                bool success: capsule_prim exists and has required attributes;
                radius and height must be specified somewhere.
        """

        return False

    def disable_obstacle(self, obstacle_prim):
        """
        Args:
                param obstacle_prim: usd prim of obstacle

        Returns:
                bool success: associated obstacle handle exists and was disabled
        """
        return False

    def enable_obstacle(self, obstacle_prim):
        """
        Note this method should change
        Args:
                param obstacle_prim: usd prim of obstacle

        Returns:
                bool success: associated obstacle handle exists and was enabled
        """

        return False

    def remove_obstacle(self, obstacle_prim):
        """
        Args:
                param obstacle_prim: usd prim of obstacle

        Returns:
                bool success: associated obstacle handle exists and was removed
        """

        return False
