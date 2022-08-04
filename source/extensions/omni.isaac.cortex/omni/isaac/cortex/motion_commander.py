# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import copy
from pxr import Usd, UsdGeom
import numpy as np
import typing

from omni.isaac.core.objects import VisualCuboid
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.math import normalized
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.utils.string import find_unique_string_name
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.prims import (
    get_prim_at_path,
    move_prim,
    query_parent_path,
    is_prim_path_valid,
    define_prim,
    get_prim_parent,
    get_prim_object_type,
)
from pxr import Gf, UsdGeom, Usd

from omni.isaac.cortex.cortex_object import CortexObject
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.smoothed_command import SmoothedCommand, TargetAdapter


class ApproachParams(object):
    """ Parameters describing how to approach a target (in position).

    The direction is a 3D vector pointing in the direction of approach. It'd magnitude defines the
    max offset from the position target the intermediate approach target will be shifted by. The std
    dev defines the length scale a radial basis (Gaussian) weight function that defines what
    fraction of the shift we take. The radial basis function is defined on the orthogonal distance
    to the line defined by the target and the direction vector.

    Intuitively, the normalized vector direction of the direction vector defines which direction to
    approach from, and it's magnitude defines how far back we want the end effector to come in from.
    The std dev defines how tighly the end-effector approaches along that line. Small std dev is
    tight around that approach line, large std dev is looser. A good value is often between 1 and 3
    cm.

    See calc_shifted_approach_target() for the specific implementation of how these parameters are
    used.
    """

    def __init__(self, direction, std_dev):
        self.direction = direction
        self.std_dev = std_dev

    def __str__(self):
        return "{direction: %s, std_dev %s}" % (str(self.approach), str(self.std_dev))


class PosePq:
    """ A pose represented internally as a position p and quaternion orientation q.
    """

    def __init__(self, p, q):
        self.p = p
        self.q = q

    def to_T(self):
        return math_util.pack_Rp(quat_to_rot_matrix(self.q), self.p)


class MotionCommand:
    """ A motion command includes the motion API parameters: a target pose (required), optional
    approach parameters, and an optional posture configuration.

    The target pose is a full position and orientation target. The approach params define how the
    end-effector should approach that target. And the posture config defines how the system should
    resolve redundancy and generally posture the arm on approach.
    """

    def __init__(self, target_pose, approach_params=None, posture_config=None):
        self.target_pose = target_pose
        self.approach_params = approach_params
        self.posture_config = posture_config

    @property
    def has_approach_params(self):
        return self.approach_params is not None

    @property
    def has_posture_config(self):
        return self.posture_config is not None


def calc_shifted_approach_target(target_T, eff_T, approach_params):
    """ Calculates how the target should be shifted to implement the approach given the current
    end-effector position.

    - target_p: Final target position.
    - eff_p: Current end effector position.
    - approach_params: The approach parameters.
    """
    target_R, target_p = math_util.unpack_T(target_T)
    eff_R, eff_p = math_util.unpack_T(eff_T)

    direction = approach_params.direction
    std_dev = approach_params.std_dev

    v = eff_p - target_p
    an = normalized(direction)
    norm = np.linalg.norm
    dist = norm(v - np.dot(v, an) * an)
    dist += 0.5 * norm(target_R - eff_R) / 3
    alpha = 1.0 - np.exp(-0.5 * dist * dist / (std_dev * std_dev))
    shifted_target_p = target_p - alpha * direction

    return shifted_target_p


class MotionCommandAdapter(TargetAdapter):
    """ A simple adapter class to extract the target information to pass into the SmoothedCommand
    object.
    """

    def __init__(self, command):
        self.command = command

    def get_position(self):
        return self.command.target_pose.p

    def has_rotation(self):
        return True

    def get_rotation_matrix(self) -> np.array:
        return quat_to_rot_matrix(self.command.target_pose.q)


def get_prim_world_T_meters(prim_path):
    """ Computes and returns the world transform of the prim at the provided prim path in units of
    meters.
    """
    prim = get_prim_at_path(prim_path)
    prim_tf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    transform = Gf.Transform()
    transform.SetMatrix(prim_tf)
    position = transform.GetTranslation()
    orientation = transform.GetRotation().GetQuat()

    p = np.array(position)
    R = np.array(Gf.Matrix3d(orientation).GetTranspose())

    T = math_util.pack_Rp(R, math_util.to_meters(p))
    return T


class MotionCommander:
    """ The motion commander provides an abstraction of motion for the cortex wherein a lower-level
    policy implements the motion commands defined by MotionCommand objects.

    This class adds and end-effector prim to the robot's hand and creates a target prim for setting
    targets. The target prim can be set to a target manually via a call to set_target() or it can be
    controlled using a gizmo through the OV viewport.

    Independent of what the stage units currently are, this class provides an SI interface. Commands
    are specified in units of meters and forward kinematics is returned in units of meters.
    """

    def __init__(self, robot, motion_controller, target_prim):
        self.robot = robot
        self.motion_controller = motion_controller
        self.smoothed_command = SmoothedCommand()

        self.robot_prim = get_prim_at_path(self.amp.get_robot_articulation().prim_path)
        self.target_prim = None

        self.register_target_prim(target_prim)

        self.is_target_position_only = False

    def set_target_position_only(self):
        self.is_target_position_only = True

    def set_target_full_pose(self):
        self.is_target_position_only = False

    def register_target_prim(self, target_prim):
        """ Register the specified target prim with this commander. This prim will both visualize
        the commands being sent to the motion commander, and it can be used to manually control the
        robot using the OV viewport's gizmo.
        """
        self.target_prim = CortexObject(target_prim)  # Target prim will be in units of meters.
        self.set_command(MotionCommand(self.get_fk_pq()))

    def calc_policy_eff_pose_rel_to_hand(self, ref_prim_path):
        """ Calculates the pose of the controlled end-effector in coordinates of the reference prim
        in the named path.

        The underlying motion policy uses an end-effector that's not necessarily available in the
        franka robot. It's that control end-effector pose that's returned by the forward kinematics
        (fk) methods below. This method gets that control end-effector pose relative to a given prim
        (such as the hand frame) so, for instance, a new prim can be added relative to that frame
        for reference elsewhere.
        """

        ref_T = get_prim_world_T_meters(ref_prim_path)
        print("hand_prim_T_meter:\n", ref_T)
        eff_T = self.get_fk_T()
        print("eff_T from mg:\n", eff_T)
        eff_T_rel2ref = math_util.invert_T(ref_T).dot(eff_T)

        R, p = math_util.unpack_T(eff_T_rel2ref)
        q = math_util.matrix_to_quat(R)
        return PosePq(p, q)

    def reset(self):
        """ Reset this motion controller. This method ensures that any internal integrators of the
        motion policy are reset, as is the smoothed command.
        """
        self.motion_policy.reset()
        self.smoothed_command.reset()

    @property
    def amp(self):
        """ Accessor for articulation motion policy from the motion controller.
        """
        return self.motion_controller.get_articulation_motion_policy()

    @property
    def motion_policy(self):
        """ The motion policy used to command the robot.
        """
        return self.motion_controller.get_articulation_motion_policy().get_motion_policy()

    @property
    def aji(self):
        """ Active joint indices. These are the indices into the full C-space configuration vector
        of the joints which are actively controlled.
        """
        return self.amp.get_active_joints_subset().get_joint_subset_indices()

    def get_end_effector_pose(self, config=None):
        """ Returns the control end-effector pose in units of meters (the end-effector used by
        motion gen).

        Motion generation returns the end-effector pose in stage units. We convert it to meters
        here. Returns the result in the same (<position>, <rotation_matrix>) tuple form as motion
        generation.

        If config is None (default), it uses the current applied action (i.e. current integration
        state of the underlying motion policy which the robot is trying to follow). By using the
        applied action (rather than measured simulation state) the behavior is robust and consistent
        regardless of simulated PD control nuances. Otherwise, if config is set, calculates the
        forward kinematics for the provided joint config. config should be the full C-space
        configuration of the robot.
        """

        if config is None:
            # No active joints config was specified, so fill it in with the current applied action.
            action = self.robot.get_applied_action()
            config = np.array(action.joint_positions)

        active_joints_config = config[self.aji]

        p, R = self.motion_policy.get_end_effector_pose(active_joints_config)
        p = math_util.to_meters(p)
        return p, R

    def get_fk_T(self, config=None):
        """ Returns the forward kinematic transform to the control frame as a 4x4 homogeneous
        matrix.
        """
        p, R = self.get_end_effector_pose(config)
        return math_util.pack_Rp(R, p)

    def get_fk_pq(self, config=None):
        """ Returns the forward kinematic transform to the control frame as a
        (<position>,<quaternion>) pair.
        """
        p, R = self.get_end_effector_pose(config)
        return PosePq(p, math_util.matrix_to_quat(R))

    def get_fk_p(self, config=None):
        """ Returns the position components of the forward kinematics transform to the end-effector 
        control frame.
        """
        p, _ = self.get_end_effector_pose(config)
        return p

    def get_fk_R(self, config=None):
        """ Returns the rotation matrix components of the forward kinematics transform to the
        end-effector control frame.
        """
        _, R = self.get_end_effector_pose(config)
        return R

    def set_command(self, command):
        """ Set the active command to the specified value. The command is smoothed before passing it
        into the underlying policy to ensure it doesn't change too quickly.

        If the command does not have a rotational target, the end-effector's current rotation is
        used in its place.

        Note the posture configure should be a full C-space configuration for the robot.
        """
        eff_T = self.get_fk_T()
        eff_p = eff_T[:3, 3]
        eff_R = eff_T[:3, :3]

        command = copy.deepcopy(command)

        if command.target_pose.q is None:
            command.target_pose.q = math_util.matrix_to_quat(eff_R)

        if command.has_approach_params:
            target_T = math_util.pack_Rp(quat_to_rot_matrix(command.target_pose.q), command.target_pose.p)
            command.target_pose.p = calc_shifted_approach_target(target_T, eff_T, command.approach_params)

        adapted_command = MotionCommandAdapter(command)
        self.smoothed_command.update(adapted_command, command.posture_config, eff_p, eff_R)

        target_p = self.smoothed_command.x
        target_R = self.smoothed_command.R
        target_T = math_util.pack_Rp(target_R, target_p)
        target_posture = self.smoothed_command.q

        self.target_prim.set_world_pose(position=target_p, orientation=math_util.matrix_to_quat(target_R))

        if target_posture is not None:
            self.set_posture_config(target_posture)

    def set_posture_config(self, posture_config):
        """ Set the posture configuration of the underlying motion policy.

        The posture configure should be a full C-space configuration for the robot.
        """
        policy = self.motion_policy._policy
        policy.set_cspace_attractor(posture_config)

    def get_adaptive_cycle_dt(self):
        """ Returns the adaptive cycle dt stored in the robot's cortex attribute.
        """
        suppress_adaptive_cycle_dt = False
        if not suppress_adaptive_cycle_dt and self.robot_prim.HasAttribute("cortex:adaptive_cycle_dt"):
            return self.robot_prim.GetAttribute("cortex:adaptive_cycle_dt").Get()
        else:
            return self.motion_controller._physics_dt

    def _sync_end_effector_target_to_motion_policy(self):
        """ Set the underlying motion generator's target to the pose in the target prim.

        Note that the world prim is a CortexObject which is always in units of meters. The motion
        generator uses stage units, so we have to convert.
        """
        target_translation, target_orientation = self.target_prim.get_world_pose()
        if self.is_target_position_only:
            self.motion_policy.set_end_effector_target(math_util.to_stage_units(target_translation))

            p, _ = self.target_prim.get_world_pose()
            q = self.get_fk_pq().q
            self.target_prim.set_world_pose(p, q)
        else:
            self.motion_policy.set_end_effector_target(math_util.to_stage_units(target_translation), target_orientation)

    def get_action(self):
        """ Get the next action from the underlying motion policy. Returns the result as an
        ArticulationAction object.
        """
        self.amp.physics_dt = self.get_adaptive_cycle_dt()

        self._sync_end_effector_target_to_motion_policy()
        self.motion_policy.update_world()

        return self.amp.get_next_articulation_action()

    def add_obstacles(self, obstacles):
        """ Add the provided obstacles to the underlying motion policy so they will be avoided.

        The obstacles must be core primitive types. See omni.isaac.core/omni/isaac/core/objects for
        options.

        See also omni.isaac.motion_generation/omni/isaac/motion_generation/world_interface.py:
        WorldInterface.add_obstacle(...)
        """
        for name, obs in obstacles.items():
            self.motion_policy.add_obstacle(obs)

    def disable_obstacle(self, obj):
        """ Distable the given object as an obstacle in the underlying motion policy.

        Disabling can be done repeatedly safely. The object can either be a core api object or a
        cortex object.
        """
        try:
            # Handle cortex objects -- extract the underlying core api object.
            if hasattr(obj, "obj"):
                obj = obj.obj
            self.motion_policy.disable_obstacle(obj)
        except Exception as e:
            err_substr = "Attempted to disable an already-disabled obstacle"
            if err_substr in str(e):
                print("<lula error caught and ignored (obj already disabled)>")
            else:
                raise e

    def enable_obstacle(self, obj):
        """ Enable the given object as an obstacle in the underlying motion policy.

        Enabling can be done repeatedly safely. The object can either be a core api object or a
        cortex object.
        """
        try:
            # Handle cortex objects -- extract the underlying core api object.
            if hasattr(obj, "obj"):
                obj = obj.obj
            self.motion_policy.enable_obstacle(obj)
        except Exception as e:
            err_substr = "Attempted to enable an already-enabled obstacle"
            if err_substr in str(e):
                print("<lula error caught and ignored (obj already enabled)>")
            else:
                raise e


def open_gripper(gripper):
    """ Open the gripper to the open position stored in the gripper object.
    """
    gripper.apply_action(ArticulationAction(joint_positions=gripper.joint_opened_positions))


def close_gripper(gripper, width=None):
    """ Close the gripper to the desired width position. Non-zero widths can be used for gripping
    objects without putting too much force on it.
    """
    if width is not None:
        joint_positions = math_util.to_stage_units(np.array([width / 2, width / 2]))
    else:
        joint_positions = gripper.joint_closed_positions
    gripper.apply_action(ArticulationAction(joint_positions=joint_positions))
