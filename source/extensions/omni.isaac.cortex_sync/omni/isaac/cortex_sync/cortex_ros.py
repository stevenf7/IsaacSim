# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


# TODO: clean up the imports
import omni

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

import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.tools import Profiler
from omni.isaac.cortex.motion_commander import MotionCommander
from omni.isaac.cortex.robot import CortexGripper, DirectSubsetCommander
from omni.isaac.cortex.cortex_object import CortexMeasuredPose
import omni.isaac.cortex_sync.ros_tf_util as ros_tf_util
from omni.isaac.cortex_sync.synchronized_time import SynchronizedTime


class PosVel:
    """ Convenient paring of a position and velocity. Provides a string conversion method which
    gives it semantics of configuration q: <pos>\n qd: <vel>.
    """

    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel

    def __str__(self):
        return "\nq: %s\nqd: %s" % (str(self.pos), str(self.vel))


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


class GripperCommandSerializer(object):
    @staticmethod
    def parse_json(json_str):
        pass

    def __init__(self, gripper_command):
        self.gripper_command = gripper_command

    def is_different(self, other):
        if self.command != other.command:
            return True

        if self.command == "move_to" and (
            self.gripper_command.width != other.gripper_command.width
            or self.gripper_command.speed != other.gripper_command.speed
        ):
            return True

        return False

    def to_msg_dict(self):
        msg = {}
        msg["width"] = self.gripper_command.width
        msg["speed"] = self.gripper_command.speed
        msg["force"] = self.gripper_command.force
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


def make_motion_command_ros_pub(topic):
    pub = rospy.Publisher(topic, JointPosVelAccCommand, queue_size=10)
    return pub


def pack_motion_command_ros_msg(motion_commander, msg_id, stamp, period):
    action = motion_commander.latest_action
    joint_names = motion_commander.articulation_subset.joint_names

    msg = JointPosVelAccCommand()
    msg.period = period

    msg.id = msg_id
    msg.header = Header()
    msg.header.seq = msg_id
    msg.header.stamp = stamp

    msg.q = action.joint_positions
    msg.qd = action.joint_velocities
    msg.qdd = []  # Note, change to np.zeros(len(qd)) if using older builds of cortex_control_franka
    msg.names = joint_names
    msg.t = stamp

    return msg


def make_gripper_command_ros_pub(topic):
    return rospy.Publisher(topic, String, queue_size=10)


def pack_gripper_command_ros_msg(gripper_commander, msg_id, stamp, period):
    serializer = GripperCommandSerializer(gripper_commander.latest_command)
    return serializer.to_msg()


def make_ros_pub(commander):
    if isinstance(commander, MotionCommander):
        return make_motion_command_ros_pub("/cortex/arm/command")
    elif isinstance(commander, CortexGripper):
        return make_gripper_command_ros_pub("/cortex/gripper/command")
    else:
        raise RuntimeError("Could not pack ros message for commander: {}".format(commander))


def pack_ros_msg(commander, msg_id, stamp, period):
    if isinstance(commander, MotionCommander):
        return pack_motion_command_ros_msg(commander, msg_id, stamp, period)
    elif isinstance(commander, CortexGripper):
        return pack_gripper_command_ros_msg(commander, msg_id, stamp, period)
    else:
        raise RuntimeError("Could not pack ros message for commander: {}".format(commander))


class CortexControlRos(object):
    def __init__(self, robot):
        self.robot = robot
        self._verbose = False

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
        self._next_msg_id = 0
        self._prev_gripper_command = None

        self._suppression_sub = rospy.Subscriber("/cortex/arm/command/suppress", RosBool, self._suppression_callback)
        self._joint_state_sub = rospy.Subscriber("/robot/joint_state", JointState, self._joint_state_callback)

        # Setup publishers
        self._joint_command_pubs = {}
        for _, commander in self.robot.commanders.items():
            self._joint_command_pubs[commander] = make_ros_pub(commander)

    def _joint_state_callback(self, msg):
        try:
            stamp = rospy.Time.now()
            for name, (pos, vel) in zip(msg.name, zip(msg.position, msg.velocity)):
                self._packed_joint_msg_values.add_stamped_joint_values(stamp, name, pos, vel)
            self._packed_joint_msg_values.prune_by_stamp(stamp - self._js_msg_stale_thresh)
            self._joint_states = self._packed_joint_msg_values.get_joint_states(self.robot.dof_names)
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
                self.robot.set_commanders_step_dt(adaptive_cycle_dt)
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
                self._states_from_suppress = None

                print("Resetting robot")
                self.robot.flag_commanders_for_reset()

            msg_id, stamp, period = self._step_msg_meta_data()
            for _, commander in self.robot.commanders.items():
                if commander.latest_command is not None:
                    pub = self._joint_command_pubs[commander]
                    msg = pack_ros_msg(commander, msg_id, stamp, period)
                    pub.publish(msg)

            return


class StampedMsg:
    def __init__(self, stamp, msg, expiration_duration=rospy.Duration(0.25)):
        self.stamp = stamp
        self.msg = msg
        self.expiration_duration = expiration_duration

    def has_expired(self, now):
        return (now - self.stamp) > self.expiration_duration


class CortexSimRobotRos(object):
    def __init__(self, robot):
        self.robot = robot
        self._verbose = False

        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_sim_cb", self._on_simulation_step)
        self._physics_call_count = 0

        self._latest_stamped_command_msg = None
        self._latest_stamped_gripper_command_msg = None

        self._joint_state_pub = rospy.Publisher("/robot/joint_state", JointState, queue_size=10)

        self._interpolated_joint_command_sub = rospy.Subscriber(
            "/cortex/arm/command/interpolated", JointPosVelAccCommand, self._interpolated_joint_command_callback
        )
        self._gripper_command_sub = rospy.Subscriber("/cortex/gripper/command", String, self._gripper_command_callback)

    def _interpolated_joint_command_callback(self, msg):
        self._latest_stamped_command_msg = StampedMsg(rospy.Time.now(), msg)

    def _gripper_command_callback(self, msg):
        self._latest_stamped_gripper_command_msg = StampedMsg(rospy.Time.now(), msg)

    def _publish_joint_state_subset(self, articulation_subset):
        names = articulation_subset.joint_names
        joint_state = articulation_subset.get_joints_state()

        msg = JointState()
        msg.header = Header()
        msg.header.stamp = rospy.Time.now()

        msg.name = names
        msg.position = joint_state.positions
        msg.velocity = joint_state.velocities
        msg.effort = []
        self._joint_state_pub.publish(msg)

    def _on_simulation_step(self, step):
        self._physics_call_count += 1
        if self._verbose:
            print("cortex_sim:", self._physics_call_count, "t:", time.time())

        now = rospy.Time.now()
        stamped_msg = self._latest_stamped_command_msg
        if stamped_msg is not None and not stamped_msg.has_expired(now):
            q = stamped_msg.msg.q
            qd = stamped_msg.msg.qd
            self.robot.arm.send(DirectSubsetCommander.Command(q, qd))

            stamped_gripper_msg = self._latest_stamped_gripper_command_msg
            if stamped_gripper_msg is not None and not stamped_gripper_msg.has_expired(now):
                self._latest_stamped_gripper_command_msg = None
                cmd = json.loads(stamped_gripper_msg.msg.data)
                self.robot.gripper.send(CortexGripper.Command(cmd["width"], speed=cmd["speed"], force=cmd["force"]))

        for _, commander in self.robot.commanders.items():
            self._publish_joint_state_subset(commander.articulation_subset)


class CortexObjectsRos:
    def __init__(self, objects=[], auto_sync_objects=False):
        self.objects = objects
        self.auto_sync_objects = auto_sync_objects
        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_objects_ros_cb", self._on_simulation_step)

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer)

    def _get_transform(self, frame_id, in_coords="world"):
        try:
            transform_stamped = self._tf_buffer.lookup_transform(in_coords, frame_id, rospy.Time(0))
            T = ros_tf_util.transform_msg_to_T(transform_stamped.transform)
            return T
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            return None

    def _on_simulation_step(self, step):
        # TODO: handle in_coords correctly.
        in_coords = "sim"
        for name, obj in self.objects.items():
            try:
                child_frame_id = name
                transform_stamped = self._tf_buffer.lookup_transform(in_coords, child_frame_id, rospy.Time(0))
                p, q = ros_tf_util.transform_msg_to_pq(transform_stamped.transform)
                obj.set_measured_pose(CortexMeasuredPose(transform_stamped.header.stamp.to_sec(), (p, q), timeout=0.25))

                if self.auto_sync_objects:
                    obj.sync_to_measured_pose()
            except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
                print("exception:", e)
                continue


class CortexSimObjectsRos:
    def __init__(self, sim_objects, belief_objects=None):
        self._sim_objects = sim_objects
        self._belief_objects = belief_objects

        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_sim_objects_ros_cb", self._on_simulation_step)

        self.tf_broadcaster = tf2_ros.TransformBroadcaster()

    def _on_simulation_step(self, step):
        self._publish_world_object_tfs()

    def _publish_world_object_tfs(self):
        # TODO: handle frame_id systematically
        frame_id = "sim"

        stamp = rospy.Time.now()
        for name, obj in self._sim_objects.items():
            T = math_util.pq2T(*obj.get_local_pose())
            child_frame_id = name
            tf = ros_tf_util.pack_transform_stamped(T, child_frame_id, frame_id, stamp)
            self.tf_broadcaster.sendTransform(tf)
