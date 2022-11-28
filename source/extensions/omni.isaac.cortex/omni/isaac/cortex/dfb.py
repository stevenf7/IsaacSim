# Copyright (c) 2022, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" A collection of behavior tools.
"""

import copy
import numpy as np

from omni.isaac.core.utils.math import normalized

from omni.isaac.cortex.df import (
    DfLogicalState,
    DfNetwork,
    DfDecider,
    DfAction,
    DfDecision,
    DfState,
    DfStateMachineDecider,
    DfStateSequence,
)
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq


class DfContext(DfLogicalState):
    """ A base context object that captures the API for exposing the robot's API.
    """

    def __init__(self, robot):
        super().__init__()
        self.robot = robot

    def reset(self):
        pass


class DfGoTarget(DfAction):
    def __init__(self, set_target_only_on_entry=False):
        super().__init__()
        self.set_target_only_on_entry = set_target_only_on_entry

    def enter(self):
        if self.set_target_only_on_entry:
            command = self.params
            self.context.robot.arm.send(command)

    def step(self):
        if not self.set_target_only_on_entry:
            command = self.params
            self.context.robot.arm.send(command)


class DfApproachTarget(DfDecider):
    """ Takes a grasp target transform and approaches along the specified axis. Defaults to
    approaching along the z-axis.
    """

    def __init__(self, approach_along_axis=2, direction_length=0.1, std_dev=0.05, approach_params_rel=None):
        """ Initialize to approach along the specified axis. The specified axis should be an index
        with the mapping 0:ax, 1:ay, 2:az. Defaults to approaching along the z-axis.

        direction_length is the length of the direction parameter (the normalized vector itself is
        given by the chosen axis). std_dev is the standard deviation parameter passed to the
        approach params.

        If approach_params is set, those parameters override any explicitly set parameters.
        """

        super().__init__()

        self.approach_along_axis = approach_along_axis
        self.direction_length = direction_length
        self.std_dev = std_dev
        self.approach_params_rel = approach_params_rel

        self.add_child("go_target", DfGoTarget())

    @property
    def has_approach_params(self):
        return self.approach_along_axis is not None or self.approach_params_rel is not None

    def decide(self):
        target_T = self.params
        if target_T is None:
            return None

        eff_T = self.context.robot.arm.get_fk_T()

        target_R, target_p = math_util.unpack_T(target_T)
        eff_R, eff_p = math_util.unpack_T(eff_T)

        # If the end-effector would twist around awkwardly, make an intermediate target which will get
        # it to go around the right direction.
        #
        # TODO: generalize this to support choice of different dominate axes.
        eff_ax, eff_ay, eff_az = math_util.unpack_R(eff_R)
        target_ax, target_ay, target_az = math_util.unpack_R(target_R)
        if eff_ax.dot(target_ax) < -0.5:
            avg_p = 0.5 * (eff_p + target_p)
            avg_az = 0.5 * (eff_az + target_az)

            ref_ax = normalized(-avg_p)
            target_az = avg_az
            target_ax = math_util.proj_orth(ref_ax, target_az, normalize_res=True)
            target_ay = np.cross(target_az, target_ax)
            target_R = math_util.pack_R(target_ax, target_ay, target_az)

        approach_params = None
        if self.has_approach_params:
            approach_axis = target_R[:, self.approach_along_axis]
            _, _, az = math_util.unpack_R(target_R)
            if self.approach_params_rel is not None:
                direction = target_R.dot(self.approach_params_rel.direction)
                approach_params = ApproachParams(direction=direction, std_dev=self.std_dev)
            else:
                approach_params = ApproachParams(direction=self.direction_length * approach_axis, std_dev=self.std_dev)

        params = MotionCommand(PosePq(target_p, math_util.matrix_to_quat(target_R)), approach_params=approach_params)
        return DfDecision("go_target", params)


# Legacy naming
DfApproachGrasp = DfApproachTarget


class DfApproachTargetLinearly(DfDecider):
    def __init__(self, step_length):
        super().__init__()

        self.step_length = step_length
        self.add_child("go_target", DfGoTarget())

    def enter(self):
        self.target_T = self.params
        self.init_eff_T = self.context.robot.arm.get_fk_T()
        self.position_offset = self.target_T[:3, 3] - self.init_eff_T[:3, 3]
        self.T_offset = self.target_T - self.init_eff_T

        dist = np.linalg.norm(self.position_offset)
        self.step_increment = self.step_length / dist
        self.current_alpha = 0.0

    def decide(self):
        target_T = self.params
        if target_T is None:
            return None

        current_target_T = copy.deepcopy(self.init_eff_T)
        current_target_T += self.current_alpha * self.T_offset
        current_target_T = math_util.proj_T(current_target_T)
        self.current_alpha += self.step_increment
        if self.current_alpha > 1.0:
            self.current_alpha = 1.0

        target_R, target_p = math_util.unpack_T(current_target_T)
        params = MotionCommand(PosePq(target_p, math_util.matrix_to_quat(target_R)))

        return DfDecision("go_target", params)


class DfLift(DfDecider):
    """ Lifts the end-effector to a desired height. Uses DfGoTarget() internally, calculating the
    target based on the forward kinematics in enter(). 
    
    Assumes the context has a MotionCommander in context.robot.arm.
    """

    def __init__(self, height, axis=2):
        super().__init__()
        self.height = height
        self.axis = axis
        self.add_child("go_target", DfGoTarget())

    def enter(self):
        self.target_pq = self.context.robot.arm.get_fk_pq()
        self.target_pq.p[self.axis] += self.height

    def decide(self):
        return DfDecision("go_target", MotionCommand(self.target_pq))


class DfMoveEndEffectorRel(DfDecider):
    """ Moves the end-effector to a point the relative coordinates. Calculates the target as a world
    pose from the local information once during enter().

    Assumes the context has a MotionCommander in context.robot.arm.
    """

    def __init__(self, p_local, approach_params=None):
        super().__init__()
        self.p_local = p_local
        self.approach_params = approach_params
        self.add_child("go_target", DfGoTarget())

    def enter(self):
        eff_T = self.context.robot.arm.get_fk_T()
        R, p = math_util.unpack_T(eff_T)
        target_p = p + R.dot(self.p_local)
        target_q = math_util.matrix_to_quat(R)

        self.target_pq = PosePq(target_p, target_q)

    def decide(self):
        return DfDecision("go_target", MotionCommand(self.target_pq))


class DfOpenGripper(DfAction):
    def enter(self):
        self.context.robot.gripper.open()


class DfCloseGripper(DfAction):
    def __init__(self, width=None):
        super().__init__()
        self.width = width

    def enter(self):
        # If the params has a width, use that, otherwise use the specified default width. It's ok
        # for width to remain None. In that case, the gripper is closed all the way.
        width = self.width
        if self.width is None and self.params is not None:
            width = self.params
        # close_gripper(self.context.robot.gripper, width)
        # TODO: add width parameter
        self.context.robot.gripper.close()


class DfSetCommanderToPositionOnly(DfAction):
    def enter(self):
        self.context.robot.arm.set_target_position_only()


class DfSetCommanderToFullPose(DfAction):
    def enter(self):
        self.context.robot.arm.set_target_full_pose()


class GoHomeState(DfState):
    def __init__(self):
        super().__init__()

    def step(self):
        aji = self.context.robot.arm.aji  # Active joint indices
        home_config = self.context.robot.get_joints_default_state().positions[aji]
        target_T = self.context.robot.arm.get_fk_T(config=home_config)
        eff_T = self.context.robot.arm.get_fk_T()

        p, q = math_util.T2pq(target_T)
        command = MotionCommand(PosePq(p, q), posture_config=home_config)
        self.context.robot.arm.send(command)

        if np.linalg.norm(eff_T - target_T) < 0.01:
            return None

        return self


def make_go_home():
    return DfStateMachineDecider(DfStateSequence([GoHomeState()]))


def step_action(tools, action):
    """ Helper method for ticking a given action.
    """
    DfNetwork(decider=action, context=DfToolsContext(tools)).step()
