# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni
import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

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


EXTENSION_NAME = "Omniverse Cortex ROS"


def find_closest_transform(p_ref, q_ref, poses):
    dists = [np.linalg.norm(p_ref - p) for p, _ in poses]
    min_dist, min_pose = min(zip(dists, poses), key=lambda v: v[0])
    return min_pose


def print_articulation_action(action):
    print("articulation action:")
    print("- q:", action.joint_positions)
    print("- qd:", action.joint_velocities)
    print("- u:", action.joint_efforts)


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


class Extension(omni.ext.IExt):
    def _init_ros_node_if_needed(self):
        print(">> initializing ros node")
        node_name = "cortex"
        try:
            print("Initializing ROS node: %s" % node_name)
            rospy.init_node(node_name, log_level=rospy.ERROR, anonymous=False, disable_signals=True)
            print("<success>")
        except rospy.exceptions.ROSException as e:
            print("Node %s has already been initialized. Skipping initialization." % node_name)

    def on_startup(self):
        print()
        print()
        print("============================================================================")
        print("Initializing Omniverse Cortex ROS extension")
        print("============================================================================")
        print()
        print("If you see the extension hanging here, you might not have the roscore running.")
        print("Start up the roscore, and it should continue.")
        print()

        self._verbose = False
        self._print_diagnistics = False

        self._profiler = Profiler(name="cortex_ros", alpha=0.99, skip_cycles=10, print_rate_hz=1.0)
        self._is_first = True

        self._init_ros_node_if_needed()
        self._world_objects_path = "/cortex/belief/objects"
        self._objects = {}

        self._num_cycles = 0

        world = World.instance()  # Get the singleton.
        world.add_physics_callback("cortex_ros_cb", self._on_simulation_step)
        self._physics_call_count = 0
        self._start_time = None
        self._synced_time = SynchronizedTime()
        self._states_from_suppress = None

        # Some fixed properties. TODO: These should be configurable.
        self._js_msg_stale_thresh = rospy.Duration(0.5)
        self._suppress_msg_timeout = 0.2

        # Names filled in when robot is loaded.
        self._robot_info = None

        # Members filled in by ROS subscriber callbacks.
        self._is_suppressed = False
        self._packed_joint_msg_values = PackedAndPrunedJointMsgs()
        self._joint_states = None
        self._suppress_msg_stamp = None

        self._needs_eff_reset = False

        # TODO: we need a way of sending gripper commands. How do we synchronize with the real
        # gripper's state? Should we run behind it and always synchronize with its published pose?
        # We'd have to squeeze in a little on contact for grasping.

        self._next_msg_id = 0

        self._prev_gripper_command = None

        self._joint_command_pubs = []
        self._suppression_sub = rospy.Subscriber(
            "/rmpflow/commands/joint_command/suppress", RosBool, self._suppression_callback
        )
        self._joint_state_sub = rospy.Subscriber("/robot/joint_state", JointState, self._joint_state_callback)
        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer)

    @property
    def robot(self):
        return self._robot_info.robot

    def _get_transform(self, frame_id, in_coords="world"):
        try:
            transform_stamped = self._tf_buffer.lookup_transform(in_coords, frame_id, rospy.Time(0))
            T = ros_tf_util.transform_msg_to_T(transform_stamped.transform)
            return T
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            return None

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

    def _step_msg_meta_data(self, step):
        try:
            adaptive_cycle = self._synced_time.next_adaptive_cycle_time()
            cmd_time = adaptive_cycle.time
            if adaptive_cycle.is_period_available:
                adaptive_cycle_dt = adaptive_cycle.period.to_sec()

                self.robot.prim.GetAttribute("cortex:adaptive_cycle_dt").Set(Double(adaptive_cycle_dt))
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

        # If the robot's not loaded yet, try to load it. If it doesn't work, then just do nothing this round.
        if self._robot_info is None:
            robot = World.instance().scene.get_object("robot_belief")
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

            world_objects_path = self._world_objects_path
            if is_prim_path_valid(world_objects_path):
                world_objects_prim = get_prim_at_path(world_objects_path)
                prim_children = get_prim_children(world_objects_prim)
                for i, prim in enumerate(prim_children):
                    prim_path = get_prim_path(prim)
                    if prim_path.endswith("/properties"):
                        continue
                    obj_name = prim_path[len(world_objects_path + "/") :]
                    self._objects[obj_name] = XFormPrim(prim_path=prim_path, name=obj_name)
            return

        self._profiler.end_capture("load robot")

        if self._is_suppressed:
            print("<cortex suppressed by for synchronization>")
            self.robot.prim.GetAttribute("cortex:is_suppressed").Set(True)
            self._states_from_suppress = self._joint_states

            now = rospy.Time.now()
            if (now - self._suppress_msg_stamp).to_sec() > self._suppress_msg_timeout:
                self._is_suppressed = False
        else:
            if self._states_from_suppress is not None:
                print("Setting robot to measured joint states:", self._states_from_suppress)
                self.robot.set_joint_positions(self._states_from_suppress.pos)
                self.robot.set_joint_velocities(self._states_from_suppress.vel)
                self._needs_eff_reset = True
                self._states_from_suppress = None
            elif self._needs_eff_reset:
                eff_prim = get_prim_at_path(get_robot_hand_prim_path(self.robot) + "/eff")
                prim_tf = UsdGeom.Xformable(eff_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                print("prim_tf\n", prim_tf)
                transform = Gf.Transform()
                transform.SetMatrix(prim_tf)
                position = transform.GetTranslation()
                orientation = transform.GetRotation().GetQuat()

                print("Setting target prim from cortex ros")
                target_prim = get_prim_at_path("/cortex/belief/motion_controller_target")
                target_prim.GetAttribute("xformOp:translate").Set(position)
                target_prim.GetAttribute("xformOp:orient").Set(orientation)

                self.robot.prim.GetAttribute("cortex:is_suppressed").Set(False)
                self._needs_eff_reset = False

            self._profiler.start_capture("ros_command_pub")

            # Publish each subset of joints as a different joint command message.
            joint_names = self._robot_info.joint_names

            action = self.robot.get_applied_action()
            msg_id, stamp, period = self._step_msg_meta_data(step)
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
            self._profiler.start_capture("sync_objs")

            stamp = time.time()
            world_objects_path = self._world_objects_path
            if is_prim_path_valid(world_objects_path):
                world_objects_prim = get_prim_at_path(world_objects_path)
                prim_children_all = get_prim_children(world_objects_prim)

                prim_children = []
                for prim in prim_children_all:
                    prim_path = get_prim_path(prim)
                    if prim_path.endswith("/properties"):
                        continue
                    prim_children.append(prim)

                poses = {}
                for i, prim in enumerate(prim_children):
                    prim_path = get_prim_path(prim)
                    child_frame_id = prim_path[len(world_objects_path + "/") :]
                    # TODO: makes more sense to have poses published in world coordinates. We should
                    # rename the "sim" to "world" and with "belief" staying "belief", so we have a
                    # "belief" and "world". Currently, though, there's a "World" which shouldn't be
                    # separate from that.
                    in_coords = "sim"

                    try:
                        # Write the measured pose into the USD attribute in stage units so the USD
                        # data structure is all in consistent units.
                        transform_stamped = self._tf_buffer.lookup_transform(in_coords, child_frame_id, rospy.Time(0))
                        p, q = ros_tf_util.transform_msg_to_pq(transform_stamped.transform)
                        poses[prim] = (p, q)
                    except (
                        tf2_ros.LookupException,
                        tf2_ros.ConnectivityException,
                        tf2_ros.ExtrapolationException,
                    ) as e:
                        # print("exception:", e)
                        continue

                # If we've found some measured poses, try to place them.
                if len(poses) > 0:
                    verbose = False
                    if verbose:
                        print("Attempting to write measured pose into USD.")

                    assignment_mode = "direct"  # other option: "closest_prior"

                    if assignment_mode == "direct":
                        for i, prim in enumerate(prim_children):
                            if prim not in poses:
                                continue

                            p, q = poses[prim]

                            if verbose:
                                prim_path = get_prim_path(prim)
                                child_frame_id = prim_path[len(world_objects_path + "/") :]
                                print("%d) %s:" % (i, child_frame_id), p)
                            gf_p = math_util.to_stage_units(Gf.Vec3d(p[0], p[1], p[2]))
                            gf_q = Gf.Quatd(q[0], Gf.Vec3d(q[1], q[2], q[3]))

                            if prim.HasAttribute("cortex:measured_pose:position"):
                                prim.GetAttribute("cortex:measured_pose:position").Set(gf_p)
                            if prim.HasAttribute("cortex:measured_pose:orient"):
                                prim.GetAttribute("cortex:measured_pose:orient").Set(gf_q)
                            if prim.HasAttribute("cortex:measured_pose:stamp"):
                                prim.GetAttribute("cortex:measured_pose:stamp").Set(Double(stamp))
                            if prim.HasAttribute("cortex:measured_pose:timeout"):
                                prim.GetAttribute("cortex:measured_pose:timeout").Set(Double(0.25))
                    elif assignment_mode == "closest_prior":
                        # Assign measured transforms to the nearest prior pose.
                        for i, (child_frame_id, obj) in enumerate(self._objects.items()):
                            in_coords = "sim"

                            p_ref, q_ref = obj.get_local_pose()
                            p_ref = math_util.to_meters(p_ref)
                            p, q = find_closest_transform(p_ref, q_ref, poses)

                            if verbose:
                                print("%d) %s:" % (i, child_frame_id), p)
                            gf_p = math_util.to_stage_units(Gf.Vec3d(p[0], p[1], p[2]))
                            gf_q = Gf.Quatd(q[0], Gf.Vec3d(q[1], q[2], q[3]))

                            if prim.HasAttribute("cortex:measured_pose:position"):
                                prim.GetAttribute("cortex:measured_pose:position").Set(gf_p)
                            if prim.HasAttribute("cortex:measured_pose:orient"):
                                prim.GetAttribute("cortex:measured_pose:orient").Set(gf_q)
                            if prim.HasAttribute("cortex:measured_pose:stamp"):
                                prim.GetAttribute("cortex:measured_pose:stamp").Set(Double(stamp))
                            if prim.HasAttribute("cortex:measured_pose:timeout"):
                                prim.GetAttribute("cortex:measured_pose:timeout").Set(Double(0.25))
                    else:
                        raise RuntimeError("Unrecognized assignment mode:" + assignment_mode)

            self._profiler.end_capture("sync_objs")

        self._profiler.end_capture("sim_step_cb")

        self._profiler.end_cycle()
        if self._print_diagnistics:
            self._profiler.print_report()
        self._profiler.start_cycle()

    def on_shutdown(self):
        print()
        print()
        print("shutting down cortex ROS extension")
        print()
        print()
        gc.collect()
