# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


# TODO: clean up the imports
import omni

# import omni.ext
# import omni.ui as ui

import gc
import asyncio
import copy
import json
import math
import numpy as np
import os
import socket
import sys
import time

import rospy
import rosgraph

from cortex_control.msg import JointPosVelAccCommand, CortexCommandAck
from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from std_msgs.msg import Bool as RosBool
import tf2_ros

import omni.physx as _physx
from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid, DynamicCuboid
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_path, get_prim_children, is_prim_path_valid
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units, traverse_stage

from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Sdf, Gf, Usd, UsdGeom
from pxr.Vt import Bool, Double

from omni.isaac.cortex.cortex_utils import get_robot_hand_prim_path, PosVel, RobotInfo, try_wrap_cortex_robot
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.tools import Profiler
from omni.isaac.cortex_sync.cortex_ros_utils import get_standard_split_joint_subset_commands
import omni.isaac.cortex_sync.ros_tf_util as ros_tf_util
from omni.isaac.cortex_sync.synchronized_time import SynchronizedTime

from omni.isaac.cortex.cortex_utils import (
    configure_robot,
    extract_joint_state_subset,
    make_core_objects,
    PosVel,
    RobotInfo,
    set_home_config,
    try_wrap_cortex_robot,
)


class StampedValue:
    def __init__(self, stamp, value):
        self.stamp = stamp
        self.value = value


class PackedAndPrunedJointMsgs:
    def __init__(self):
        self._stamped_name_value_pairs = {}

    def add_stamped_value(self, stamp, name, value):
        self._stamped_name_value_pairs[name] = StampedValue(stamp, value)

    def add_stamped_joint_values(self, stamp, name, pos, vel):
        self.add_stamped_value(stamp, name, PosVel(pos, vel))

    def prune_by_stamp(self, prune_thresh_stamp):
        names_to_prune = []
        for name, stamped_value in self._stamped_name_value_pairs.items():
            if stamped_value.stamp < prune_thresh_stamp:
                names_to_prune.append(name)

        for name in names_to_prune:
            del self._stamped_name_value_pairs[name]

    def get_joint_states(self, joint_names):
        try:
            pos = [self._stamped_name_value_pairs[name].value.pos for name in joint_names]
            vel = [self._stamped_name_value_pairs[name].value.vel for name in joint_names]
        except KeyError as e:
            # If one of the keys isn't yet available, return None
            # print("Joint state not available:",  e.args[0])
            return None
        return PosVel(pos, vel)


class GripperCommand(object):
    @staticmethod
    def parse_json(json_str):
        pass

    def __init__(self, finger_joint_values):
        self.width = math_util.to_meters(sum(finger_joint_values))

        if self.width < 0:
            self.command = "close_to_grasp"
        else:
            self.command = "move_to"

    def is_different(self, other):
        if self.command != other.command:
            return True

        if self.command == "move_to" and self.width != other.width:
            return True

        return False

    def to_msg_dict(self):
        msg = {}
        msg["command"] = self.command
        if self.command == "move_to":
            msg["width"] = self.width
        return msg

    def to_msg(self):
        try:
            msg_dict = self.to_msg_dict()
            s = json.dumps(msg_dict)
            msg = String(s)
        except ValueError as ve:
            print("Json parse error:\n", msg_dict)
            print("ERROR:", ve)
        return msg


def cortex_init_ros_node(node_name="cortex"):
    rospy.init_node(node_name, log_level=rospy.ERROR, anonymous=False, disable_signals=True)


class CortexControl(object):
    def __init__(self, robot, commander):
        self.robot = robot
        self.commander = commander

        self._robot_info = None

        self._verbose = False
        self._print_diagnistics = False

        self._profiler = Profiler(name="cortex_control", alpha=0.99, skip_cycles=10, print_rate_hz=1.0)
        self._is_first = True

        self._num_cycles = 0

        # We'll add this as a physics callback because physics callbacks are called after the physics step.
        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_control_cb", self._on_simulation_step)

        self._physics_call_count = 0
        self._start_time = None
        self._synced_time = SynchronizedTime()
        self._states_from_suppress = None

        # Some fixed properties. TODO: These should be configurable.
        self._js_msg_stale_thresh = rospy.Duration(0.5)
        self._suppress_msg_timeout = 0.2

        # Members filled in by ROS subscriber callbacks.
        self._is_suppressed = False
        self._packed_joint_msg_values = PackedAndPrunedJointMsgs()
        self._joint_states = None
        self._suppress_msg_stamp = None

        # Members filled in each physics step from _on_simulation_step
        self._needs_eff_reset = False
        self._next_msg_id = 0
        self._prev_gripper_command = None

        self._joint_command_pubs = []
        self._suppression_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/suppress", RosBool, self._suppression_callback
        )
        self._joint_state_sub = rospy.Subscriber("/robot/joint_state", JointState, self._joint_state_callback)

    def _joint_state_callback(self, msg):
        try:
            # If the robot info isn't loaded, then the simulation hasn't started yet. Do nothing.
            if self._robot_info is None:
                return

            stamp = rospy.Time.now()
            for name, (pos, vel) in zip(msg.name, zip(msg.position, msg.velocity)):
                self._packed_joint_msg_values.add_stamped_joint_values(stamp, name, pos, vel)
            self._packed_joint_msg_values.prune_by_stamp(stamp - self._js_msg_stale_thresh)
            self._joint_states = self._packed_joint_msg_values.get_joint_states(self._robot_info.joint_names)
        except Exception as e:
            print("\nProblem processing joint state message.")
            import traceback

            traceback.print_exc()

    def _suppression_callback(self, msg):
        self._is_suppressed = msg.data
        self._suppress_msg_stamp = rospy.Time.now()

    def _step_msg_meta_data(self):
        try:
            adaptive_cycle = self._synced_time.next_adaptive_cycle_time()
            cmd_time = adaptive_cycle.time
            if adaptive_cycle.is_period_available:
                adaptive_cycle_dt = adaptive_cycle.period.to_sec()
                self.commander.set_adaptive_cycle_dt(adaptive_cycle_dt)
                period = cmd_time - self._prev_cmd_time
            else:
                period = rospy.Duration(0)

            return self._next_msg_id, cmd_time, period

        except Exception as e:
            print("\nProblem packing command message.")
            import traceback

            traceback.print_exc()
        finally:
            # Always increment and safe off time at the end.
            self._next_msg_id += 1
            self._prev_cmd_time = cmd_time
            self._num_cycles += 1

    def _on_simulation_step(self, step):
        self._physics_call_count += 1
        if self._verbose:
            print("cortex_ros:", self._physics_call_count, "t:", time.time())

        if self._is_first:
            self._profiler.start_cycle()
            self._is_first = False

        self._profiler.start_capture("sim_step_cb")
        self._profiler.start_capture("load robot")

        ## If the robot's not loaded yet, try to load it. If it doesn't work, then just do nothing this round.
        if self._robot_info is None:
            robot = self.robot
            if robot is None:
                return

            self._robot_info = RobotInfo(robot)
            return
        elif not self._robot_info.is_configured and self._robot_info.ready_to_configure:
            self._robot_info.configure()
            self._joint_subsets_commands = get_standard_split_joint_subset_commands(self._robot_info)
            for name, subset in self._joint_subsets_commands.items():
                self._joint_command_pubs.append(rospy.Publisher(subset.topic, JointPosVelAccCommand, queue_size=10))
            self.gripper_command_pub = rospy.Publisher("/cortex/gripper/command", String, queue_size=10)
            return

        self._profiler.end_capture("load robot")

        if self._is_suppressed:
            print("<cortex suppressed by for synchronization>")
            self._synced_time.reset()
            self._states_from_suppress = self._joint_states

            now = rospy.Time.now()
            delta_secs = (now - self._suppress_msg_stamp).to_sec()
            if delta_secs > self._suppress_msg_timeout:
                self._is_suppressed = False
            return
        else:
            if self._states_from_suppress is not None:
                print("Setting robot to measured joint states:", self._states_from_suppress)
                self.robot.set_joint_positions(self._states_from_suppress.pos)
                self.robot.set_joint_velocities(self._states_from_suppress.vel)
                self._needs_eff_reset = True
                self._states_from_suppress = None

                print("Resetting motion commander")
                self.commander.reset()
            elif self._needs_eff_reset:
                self._needs_eff_reset = False

            self._profiler.start_capture("ros_command_pub")

            # Publish each subset of joints as a different joint command message.
            joint_names = self._robot_info.joint_names

            action = self.robot.get_applied_action()
            msg_id, stamp, period = self._step_msg_meta_data()
            for pub, (name, subset) in zip(self._joint_command_pubs, self._joint_subsets_commands.items()):
                if not subset.is_empty:
                    pub.publish(subset.pack_msg(joint_names, action, msg_id, stamp, period))

            # Create a gripper command object and publish that on the gripper command publisher.
            gripper_values = action.joint_positions[self._joint_subsets_commands["gripper"].indices]
            gripper_command = GripperCommand(gripper_values)
            if self._prev_gripper_command is None or gripper_command.is_different(self._prev_gripper_command):
                self.gripper_command_pub.publish(gripper_command.to_msg())
                self._prev_gripper_command = gripper_command

            self._profiler.end_capture("ros_command_pub")
            return


class StampedMsg:
    def __init__(self, stamp, msg, expiration_duration=rospy.Duration(0.25)):
        self.stamp = stamp
        self.msg = msg
        self.expiration_duration = expiration_duration

    def has_expired(self, now):
        return (now - self.stamp) > self.expiration_duration


class CortexSimRobot(object):
    def __init__(self, robot):
        self.robot = robot

        self._verbose = False
        self._print_diagnistics = False

        self._profiler = Profiler(name="cortex_sim", alpha=0.99, skip_cycles=10, print_rate_hz=1.0)
        self._is_first = True

        self._camera_frame_id = None
        self._camera_prim = None
        self._sim_prim = None

        self._robot_info = None

        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_sim_cb", self._on_simulation_step)
        self._physics_call_count = 0

        self._latest_stamped_command_msg = None
        self._latest_stamped_gripper_command_msg = None

        self._joint_subsets_commands = None
        self._interpolated_joint_command_sub = None
        self._gripper_command_sub = None
        self._joint_state_pub = rospy.Publisher("/robot/joint_state", JointState, queue_size=10)

        self.tf_broadcaster = tf2_ros.TransformBroadcaster()

    def _interpolated_joint_command_callback(self, msg):
        self._latest_stamped_command_msg = StampedMsg(rospy.Time.now(), msg)

    def _gripper_command_callback(self, msg):
        self._latest_stamped_gripper_command_msg = StampedMsg(rospy.Time.now(), msg)

    def _publish_joint_state_subset(self, indices):
        names = [self._robot_info.joint_names[i] for i in indices]
        joint_state = extract_joint_state_subset(self._robot_info.robot.get_joints_state(), indices)

        msg = JointState()
        msg.header = Header()
        msg.header.stamp = rospy.Time.now()

        msg.name = names
        msg.position = joint_state.positions
        msg.velocity = joint_state.velocities
        msg.effort = []
        self._joint_state_pub.publish(msg)

    def _publish_commanded_joints(self):
        self._publish_joint_state_subset(self._joint_subsets_commands["arm"].indices)

    def _publish_uncommanded_joints(self):
        self._publish_joint_state_subset(self._joint_subsets_commands["gripper"].indices)

    def _on_simulation_step(self, step):
        self._physics_call_count += 1
        if self._verbose:
            print("cortex_sim:", self._physics_call_count, "t:", time.time())

        if self._is_first:
            self._profiler.start_cycle()
            self._is_first = False

        self._profiler.start_capture("sim_step_cb")
        self._profiler.start_capture("load robot")

        # If the robot's not loaded yet, try to load it. If it doesn't work, then just do nothing this round.
        do_gains_hack = True
        if self._robot_info is None:
            self._robot_info = RobotInfo(self.robot)
            return
        elif not self._robot_info.is_configured and self._robot_info.ready_to_configure:
            self._robot_info.configure()
            configure_robot(self.robot, verbose=True)
            set_home_config(self.robot)

            self._belief_objects, _ = make_core_objects("belief")
            self._sim_objects, _ = make_core_objects("sim")

            self._joint_subsets_commands = get_standard_split_joint_subset_commands(self._robot_info)
            self._interpolated_joint_command_sub = rospy.Subscriber(
                self._joint_subsets_commands["arm"].topic + "/interpolated",
                JointPosVelAccCommand,
                self._interpolated_joint_command_callback,
            )
            self._gripper_command_sub = rospy.Subscriber(
                "/cortex/gripper/command", String, self._gripper_command_callback
            )
            return
        elif do_gains_hack:
            # TODO: do we still need the gains hack?
            if self._physics_call_count < 10:
                return
            elif self._physics_call_count == 10:
                configure_robot(self.robot, verbose=True)
                return

        self._profiler.end_capture("load robot")

        self._profiler.start_capture("commands")
        now = rospy.Time.now()
        stamped_msg = self._latest_stamped_command_msg
        if stamped_msg is not None and not stamped_msg.has_expired(now):
            q = stamped_msg.msg.q
            qd = stamped_msg.msg.qd
            self.robot.apply_action(
                ArticulationAction(joint_positions=q, joint_indices=self._joint_subsets_commands["arm"].indices)
            )

            stamped_gripper_msg = self._latest_stamped_gripper_command_msg
            if stamped_gripper_msg is not None and not stamped_gripper_msg.has_expired(now):
                self._latest_stamped_gripper_command_msg = None
                cmd = json.loads(stamped_gripper_msg.msg.data)
                if cmd["command"] == "move_to":
                    q = np.ones(2) * math_util.to_stage_units(cmd["width"] / 2.0)
                    print("setting sim gripper to:", q)
                    self.robot.gripper.apply_action(ArticulationAction(joint_positions=q))
                elif cmd["command"] == "close_to_grasp":
                    q = np.zeros(2)
                    self.robot.gripper.apply_action(ArticulationAction(joint_positions=q))
                else:
                    print("WARNING -- unrecognized gripper command:", cmd["command"])

        self._profiler.end_capture("commands")

        self._profiler.start_capture("ros_pub")
        self._publish_commanded_joints()
        self._publish_uncommanded_joints()
        self._profiler.end_capture("ros_pub")

        self._profiler.end_capture("sim_step_cb")

        self._profiler.end_cycle()
        if self._print_diagnistics:
            self._profiler.print_report()
        self._profiler.start_cycle()
