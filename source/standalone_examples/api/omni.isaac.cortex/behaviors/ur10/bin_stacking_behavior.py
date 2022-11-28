# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from collections import OrderedDict
import copy
import numpy as np
import random
import time

import omni
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid, VisualCapsule, VisualSphere
from omni.isaac.core.prims import XFormPrim, RigidPrim
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.materials import OmniPBR, VisualMaterial, PreviewSurface
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage

from omni.isaac.cortex.cortex_rigid_prim import CortexRigidPrim
from omni.isaac.cortex.df import DfNetwork
from omni.isaac.cortex.cortex_world import CortexWorld, LogicalStateMonitor, Behavior
from omni.isaac.cortex.robot import CortexUr10
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.motion_commander import MotionCommand, ApproachParams, PosePq
from omni.isaac.cortex.cortex_utils import get_assets_root_path_or_die
from omni.isaac.cortex.tools import SteadyRate
from omni.isaac.core.utils.rotations import quat_to_rot_matrix

from omni.isaac.core.utils.math import normalized

from omni.isaac.cortex.df import (
    DfLogicalState,
    DfNetwork,
    DfDecider,
    DfDeciderState,
    DfDecision,
    DfAction,
    DfState,
    DfStateSequence,
    DfTimedDeciderState,
    DfStateMachineDecider,
    DfSetLockState,
    DfWaitState,
    DfWriteContextState,
)
from omni.isaac.cortex.dfb import make_go_home, DfLift


class BinState:
    def __init__(self, bin_obj):
        self.bin_obj = bin_obj
        self.bin_base = XFormPrim(self.bin_obj.prim_path + "/Collision/Cube_03")
        self.grasp_T = None
        self.is_grasp_reached = None
        self.is_attached = None
        self.needs_flip = None


class BinStackingContext(DfLogicalState):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.world = CortexWorld.instance()
        self.bins = None
        self.diagnostic_print_dt = 0.5

        self.flip_station_bin_pt = np.array([0.766, 0.755, -0.066])
        self.flip_station_obs_z_thresh = None
        self.flip_station_obs = self.world.scene.get_object("flip_station_sphere")

        self.navigation_obs_is_active = True
        self.navigation_obstacles = [
            self.world.scene.get_object("navigation_dome_obs"),
            self.world.scene.get_object("navigation_barrier_obs"),
            self.world.scene.get_object("navigation_flip_station_obs"),
        ]

        h = 0.135
        e = 0.02
        full_stack = True
        if full_stack:
            self.stack_xs = np.array([1.00, 0.79, 0.58]) + 0.05
            self.stack_ys = [-0.62, -0.31, 0]
            self.stack_zs = [-0.59374 + (i * h) + h / 2 + e for i in range(4)]
        else:
            self.stack_xs = np.array([1.00, 0.79]) + 0.05
            self.stack_ys = [-0.62, -0.31]
            self.stack_zs = [-0.59374 + (i * h) + h / 2 + e for i in range(2)]

            # self.stack_xs = np.array([.58]) + 0.05
            # self.stack_ys = [-0.62]
            # self.stack_zs = [-0.59374 + (i * h) + h / 2 + e for i in range(4)]

        self.stack_coordinates = []
        for zi in range(len(self.stack_zs)):
            for yi in range(len(self.stack_ys)):
                for xi in range(len(self.stack_xs)):
                    self.stack_coordinates.append((self.stack_xs[xi], self.stack_ys[yi], self.stack_zs[zi]))

        self.active_bin = None
        self.stacked_bins = []

        self.add_monitors(
            [
                BinStackingContext.monitor_bins,
                BinStackingContext.monitor_active_bin,
                BinStackingContext.monitor_active_bin_grasp_T,
                BinStackingContext.monitor_active_bin_grasp_reached,
                BinStackingContext.monitor_flip_station_obs,
                BinStackingContext.monitor_diagnostics,
            ]
        )

    def enable_navigation_obstacles_if_needed(self):
        if not self.navigation_obs_is_active:
            self.navigation_obs_is_active = True
            for obs in self.navigation_obstacles:
                self.robot.arm.enable_obstacle(obs)

    def disable_navigation_obstacles_if_needed(self):
        if self.navigation_obs_is_active:
            self.navigation_obs_is_active = False
            for obs in self.navigation_obstacles:
                self.robot.arm.disable_obstacle(obs)

    def reset(self):
        # When reset() is called, the world and the objects populated by the task are available. Access
        # the relevant objects.
        # TODO: handle corresponding obs variable resets more carefully.
        self.robot.arm.disable_obstacle(self.flip_station_obs)
        self.disable_navigation_obstacles_if_needed()

        # Find the collection of bins in the world scene.
        self.bins = []
        i = 0
        while True:
            name = "bin_{}".format(i)
            bin_obj = self.world.scene.get_object(name)
            if bin_obj is None:
                break
            self.bins.append(BinState(bin_obj))
            i += 1

        self.start_time = time.time()
        self.num_diagnostic_prints = 0.0

        self.active_bin = None
        self.stacked_bins.clear()

    @property
    def stack_complete(self):
        return len(self.stacked_bins) == len(self.stack_coordinates)

    @property
    def elapse_time(self):
        return time.time() - self.start_time

    @property
    def has_active_bin(self):
        return self.active_bin is not None

    def monitor_bins(self):
        if self.active_bin is None:
            self.conveyer_bin = None
            min_y = None
            for bin_state in self.bins:
                p, _ = bin_state.bin_obj.get_world_pose()

                # Check whether it's on the conveyer in the active region.
                x, y, z = p
                if 0.0 < y and y < 0.7 and -0.4 < x and x < 0.4:
                    v = bin_state.bin_obj.get_linear_velocity()
                    if True or np.linalg.norm(v) < 0.01:
                        if self.active_bin is None or y < min_y:
                            self.active_bin = bin_state
                            min_y = y

    def monitor_active_bin(self):
        if self.active_bin is not None:
            p, _ = self.active_bin.bin_obj.get_world_pose()
            if p[2] < -1.0:
                self.active_bin = None

    def monitor_active_bin_grasp_T(self):
        if self.active_bin is not None:
            bin_T = math_util.pq2T(*self.active_bin.bin_base.get_world_pose())
            bin_R, bin_p = math_util.unpack_T(bin_T)
            bin_ax, bin_ay, bin_az = math_util.unpack_R(bin_R)

            self.active_bin.is_rightside_up = False
            up_vec = np.array([0.0, 0.0, 1.0])
            if self.active_bin.is_attached:
                fk_R = self.robot.arm.get_fk_R()
                fk_x, _, _ = math_util.unpack_R(fk_R)
                up_vec = -fk_x

            margin = 0.0
            base_width = 0.00233

            self.active_bin.needs_flip = up_vec.dot(bin_az) > 0.0
            if self.active_bin.needs_flip:
                # The bin is right side up (opens upward)
                target_ax = -bin_az
                margin = 0.005
            else:
                # The bin is upside down (opens downward)
                target_ax = bin_az
                margin = -0.005
            if bin_ax[1] < 0.0:
                # x axis is pointing toward the robot
                target_ay = -bin_ax
            else:
                target_ay = bin_ax
            target_az = np.cross(target_ax, target_ay)
            target_p = bin_p + margin * bin_az

            target_T = math_util.pack_Rp(math_util.pack_R(target_ax, target_ay, target_az), target_p)
            self.active_bin.grasp_T = target_T

    def monitor_active_bin_grasp_reached(self):
        if self.has_active_bin:
            fk_T = self.robot.arm.get_fk_T()
            self.active_bin.is_grasp_reached = math_util.transforms_are_close(
                self.active_bin.grasp_T, fk_T, p_thresh=0.005, R_thresh=0.01
            )
            # We can be looser with this proximity check.
            self.active_bin.is_attached = (
                math_util.transforms_are_close(self.active_bin.grasp_T, fk_T, p_thresh=0.1, R_thresh=1.0)
                and self.robot.suction_gripper.is_closed()
            )

    def monitor_flip_station_obs(self):
        # The flip_station_obs_z_thresh member being non-None indicates the obstacle is activated.
        if self.flip_station_obs_z_thresh is not None:
            eff_p = self.robot.arm.get_fk_p()
            if eff_p[2] >= self.flip_station_obs_z_thresh:
                self.robot.arm.disable_obstacle(self.flip_station_obs)
                self.flip_station_obs_z_thresh = None

    def activate_flip_station_obs_until_z_thresh(self, z_thresh=0.05):
        self.flip_station_obs_z_thresh = z_thresh
        self.robot.arm.enable_obstacle(self.flip_station_obs)

    def is_navigation_obs_needed(self, target_p):
        target_p = np.array([v for v in target_p])  # target_p may be a tuple, and we need to make a copy

        ref_p = np.array([0.6, 0.37, -0.99])
        eff_p = self.robot.arm.get_fk_p()

        ref_p[2] = 0.0
        eff_p[2] = 0.0
        target_p[2] = 0.0

        s_target = np.sign(np.cross(target_p, ref_p)[2])
        s_eff = np.sign(np.cross(eff_p, ref_p)[2])
        return s_target * s_eff < 0.0

    def activate_navigation_obs_if_needed(self, target_p):
        if self.is_navigation_obs_needed(target_p):
            self.enable_navigation_obstacles_if_needed()
        else:
            self.disable_navigation_obstacles_if_needed()

    def monitor_diagnostics(self):
        now = self.elapse_time
        if now >= (self.num_diagnostic_prints + 1) * self.diagnostic_print_dt:
            if self.has_active_bin:
                print("active bin info:")
                print("- bin_obj.name: {}".format(self.active_bin.bin_obj.name))
                print("- bin_base: {}".format(self.active_bin.bin_base))
                print("- grasp_T:\n{}".format(self.active_bin.grasp_T))
                print("- is_grasp_reached: {}".format(self.active_bin.is_grasp_reached))
                print("- is_attached:  {}".format(self.active_bin.is_attached))
                print("- needs_flip:  {}".format(self.active_bin.needs_flip))
            else:
                print("<no active bin>")
            self.num_diagnostic_prints += 1

    def mark_active_bin_as_complete(self):
        self.stacked_bins.append(self.active_bin)
        self.active_bin = None


class DfDecoratorDecider(DfDecider):
    """ A decorator decider simply computes parameters for the child.
    """

    def link_to(self, decider):
        self.add_child("child", decider)
        return self

    def compute_params(self):
        raise NotImplementedError()

    def decide(self):
        params = self.compute_params()
        return DfDecision("child", params)


class ChooseGrasp(DfDecoratorDecider):
    def compute_params(self):
        return self._compute_eff_target(math_util.pq2T(*self.context.active_bin.get_world_pose()))

    def _compute_eff_target(self, T):
        R, p = math_util.unpack_T(T)
        ax, ay, az = math_util.unpack_T(R)


class Pick(DfAction):
    def __init__(self):
        super().__init__()

    def step(self):
        R, p = math_util.unpack_T(self.context.active_bin_grasp_T)
        ax, ay, az = math_util.unpack_R(R)
        self.context.robot.arm.send_end_effector(
            target_pose=PosePq(p, math_util.matrix_to_quat(R)),
            approach_params=ApproachParams(direction=0.2 * ax, std_dev=0.05),
        )


class ActivateFlipStationObs(DfState):
    def enter(self):
        self.context.activate_flip_station_obs_until_z_thresh()


class ReachToPick(DfState):
    def __init__(self):
        super().__init__()

    def step(self):
        R, p = math_util.unpack_T(self.context.active_bin.grasp_T)
        self.context.activate_navigation_obs_if_needed(p)

        ax, ay, az = math_util.unpack_R(R)
        posture_config = np.array([-1.2654234, -2.9708025, -2.219733, 0.6445836, 1.5186214, 0.30098662])
        if self.context.active_bin.needs_flip:
            approach_length = 0.4
        else:
            approach_length = 0.2
        self.context.robot.arm.send_end_effector(
            target_pose=PosePq(p, math_util.matrix_to_quat(R)),
            approach_params=ApproachParams(direction=approach_length * ax, std_dev=0.05),
            posture_config=posture_config,
        )

        fk_T = self.context.robot.arm.get_fk_T()
        if math_util.transforms_are_close(self.context.active_bin.grasp_T, fk_T, p_thresh=0.005, R_thresh=0.01):
            return None
        return self


class MoveToTarget(DfState):
    def __init__(self, p_thresh, R_thresh):
        self.p_thresh = p_thresh
        self.R_thresh = R_thresh
        self.target_pose = None

    def step(self):
        fk_T = self.context.robot.arm.get_fk_T()
        if math_util.transforms_are_close(
            self.target_pose.to_T(), fk_T, p_thresh=self.p_thresh, R_thresh=self.R_thresh
        ):
            return None
        return self


class ReachToPlace(MoveToTarget):
    def __init__(self):
        super().__init__(p_thresh=0.01, R_thresh=2.0)

    def step(self):
        target_p = self.context.stack_coordinates[len(self.context.stacked_bins)]
        self.context.activate_navigation_obs_if_needed(target_p)

        target_ax = np.array([0.0, 0.0, -1.0])
        target_az = np.array([0.0, -1.0, 0.0])
        target_ay = np.cross(target_az, target_az)
        target_R = math_util.pack_R(target_ax, target_ay, target_az)

        # Correct the target by the error between where the end-effector if relative to the bin
        # and the grasp target.
        target_T = math_util.pack_Rp(target_R, target_p)
        eff_T = self.context.robot.arm.get_fk_T()

        posture_config = self.context.robot.default_config

        self.target_pose = PosePq(target_p, math_util.matrix_to_quat(target_R))
        approach_params = ApproachParams(direction=0.15 * np.array([0.0, 0.0, -1.0]), std_dev=0.005)
        self.context.robot.arm.send_end_effector(
            target_pose=self.target_pose, approach_params=approach_params, posture_config=posture_config
        )

        return super().step()


class CloseSuctionGripperWithRetries(DfState):
    def enter(self):
        pass

    def step(self):
        gripper = self.context.robot.suction_gripper
        gripper.close()
        if gripper.is_closed():
            return None
        return self


class CloseSuctionGripper(DfState):
    def enter(self):
        print("<close gripper>")
        self.context.robot.suction_gripper.close()

    def step(self):
        return None


class OpenSuctionGripper(DfState):
    def enter(self):
        print("<open gripper>")
        self.context.robot.suction_gripper.open()

    def step(self):
        return None


class RecordConfigState(DfState):
    def enter(self):
        q = self.context.robot.get_joint_positions()
        print("config: {}".format(q))

    def step(self):
        return None


class DoNothing(DfState):
    def enter(self):
        self.context.robot.arm.clear()

    def step(self):
        print("current command pq")
        print(self.context.robot.arm.target_prim.get_world_pose())
        return self


class LiftAndTurn(MoveToTarget):
    def __init__(self):
        super().__init__(p_thresh=0.05, R_thresh=0.1)

    def step(self):
        home_config = self.context.robot.default_config
        home_T = self.context.robot.arm.get_fk_T(config=home_config)

        p, q = math_util.T2pq(home_T)
        p += 0.5 * normalized(np.array([0.0, -0.5, -1.0]))
        self.target_pose = PosePq(p, q)
        command = MotionCommand(self.target_pose, posture_config=home_config)
        self.context.robot.arm.send(command)

        return super().step()


class PickBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    ReachToPick(),
                    DfWaitState(wait_time=1.0),
                    DfSetLockState(set_locked_to=True, decider=self),
                    CloseSuctionGripper(),
                    DfTimedDeciderState(DfLift(0.3), activity_duration=0.4),
                    DfSetLockState(set_locked_to=False, decider=self),
                ],
                loop=False,
            )
        )


class FlipBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    LiftAndTurn(),
                    MoveToFlipStation(),
                    DfSetLockState(set_locked_to=True, decider=self),
                    OpenSuctionGripper(),
                    ReleaseFlipStationBin(duration=0.65),
                    ActivateFlipStationObs(),
                    DfSetLockState(set_locked_to=False, decider=self),
                ]
            )
        )


class PlaceBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    ReachToPlace(),
                    DfWaitState(wait_time=1.0),
                    DfSetLockState(set_locked_to=True, decider=self),
                    OpenSuctionGripper(),
                    DfTimedDeciderState(DfLift(0.1), activity_duration=0.25),
                    DfWriteContextState(lambda ctx: ctx.mark_active_bin_as_complete()),
                    DfSetLockState(set_locked_to=False, decider=self),
                ],
                loop=False,
            )
        )


class MoveToFlipStation(DfState):
    def __init__(self):
        self.target_pose = PosePq(
            np.array([0.7916634, 0.73902607, -0.02897218]), np.array([0.52239186, 0.6296602, -0.5042411, 0.27636158])
        )

        self.approach_params = ApproachParams(direction=0.4 * normalized(np.array([0.5, -0.3, -0.75])), std_dev=0.05)

        self.posture_config = np.array(
            [
                -2.1273114681243896,
                -3.004627227783203,
                -1.0576069355010986,
                -0.5193580389022827,
                -1.0809129476547241,
                2.0418107509613037,
            ]
        )

    def enter(self):
        motion_command = MotionCommand(
            target_pose=self.target_pose, approach_params=self.approach_params, posture_config=self.posture_config
        )
        self.context.robot.arm.send(motion_command)

    def step(self):
        fk_T = self.context.robot.arm.get_fk_T()
        if math_util.transforms_are_close(self.target_pose.to_T(), fk_T, p_thresh=0.005, R_thresh=2.0, verbose=False):
            return None
        return self


class ReleaseFlipStationBin(DfState):
    def __init__(self, duration):
        self.duration = duration

    def enter(self):
        self.entry_time = time.time()

        fk_T = self.context.robot.arm.get_fk_T()
        fk_R, fk_p = math_util.unpack_T(fk_T)
        ax, ay, az = math_util.unpack_R(fk_R)

        home_config = self.context.robot.default_config
        home_T = self.context.robot.arm.get_fk_T(config=home_config)
        home_R, home_p = math_util.unpack_T(home_T)

        v = normalized(np.array([-1.0, -0.3, 0.0]))
        toward_base_alpha = 0.2
        target_p = fk_p - 0.3 * ax + toward_base_alpha * v
        self.target_p = target_p
        self.ax = ax
        self.v = v

        target_ax = normalized(np.array([1.0, -0.0, 0.0]))
        target_ay = ay
        target_az = np.cross(target_ax, target_ay)
        target_R = math_util.pack_R(target_ax, target_ay, target_az)

        self.target_pose = PosePq(target_p, math_util.matrix_to_quat(target_R))
        motion_command = MotionCommand(
            target_pose=self.target_pose,
            approach_params=ApproachParams(direction=toward_base_alpha * v, std_dev=0.1),
            posture_config=self.context.robot.get_joint_positions().astype(float),
        )
        self.context.robot.arm.send(motion_command)

    def step(self):
        if time.time() - self.entry_time >= self.duration:
            return None
        return self


class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()

        self.add_child("flip_bin", FlipBin())
        self.add_child("pick_bin", PickBin())
        self.add_child("place_bin", PlaceBin())
        self.add_child("go_home", make_go_home())
        self.add_child("do_nothing", DfStateMachineDecider(DoNothing()))

    def decide(self):
        if self.context.stack_complete:
            return DfDecision("go_home")

        if self.context.has_active_bin:
            if not self.context.active_bin.is_attached:
                return DfDecision("pick_bin")
            elif self.context.active_bin.needs_flip:
                return DfDecision("flip_bin")
            else:
                return DfDecision("place_bin")
        else:
            return DfDecision("go_home")


def make_decider_network(robot):
    return DfNetwork(decider=Dispatch(), context=BinStackingContext(robot))
