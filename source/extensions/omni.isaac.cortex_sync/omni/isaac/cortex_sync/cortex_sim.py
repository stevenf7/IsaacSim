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

import asyncio
import gc
import json
import math
import numpy as np
import os
import sys
import time

import rospy
from cortex_control.msg import JointPosVelAccCommand
from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from std_msgs.msg import Bool as RosBool
import tf2_ros

import omni.physx as _physx
from omni.isaac.core import World
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_path, get_prim_children, is_prim_path_valid
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units, traverse_stage
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Sdf
from pxr.Vt import Bool, Double

from omni.isaac.cortex.cortex_utils import (
    configure_robot,
    extract_joint_state_subset,
    make_core_objects,
    PosVel,
    RobotInfo,
    set_home_config,
    try_wrap_cortex_robot,
)
import omni.isaac.cortex.math_util as math_util
from omni.isaac.cortex.tools import Profiler
from omni.isaac.cortex_sync.cortex_ros_utils import get_standard_split_joint_subset_commands
import omni.isaac.cortex_sync.ros_tf_util as ros_tf_util
from omni.isaac.cortex_sync.synchronized_time import SynchronizedTime


EXTENSION_NAME = "Omniverse Cortex Sim"


class StampedMsg:
    def __init__(self, stamp, msg, expiration_duration=rospy.Duration(0.25)):
        self.stamp = stamp
        self.msg = msg
        self.expiration_duration = expiration_duration

    def has_expired(self, now):
        return (now - self.stamp) > self.expiration_duration


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
        print("Initializing Omniverse Cortex Sim extension")
        print("============================================================================")
        print()
        print("If you see the extension hanging here, you might not have the roscore running.")
        print("Start up the roscore, and it should continue.")
        print()

        self._verbose = False
        self._print_diagnistics = False

        self._profiler = Profiler(name="cortex_sim", alpha=0.99, skip_cycles=10, print_rate_hz=1.0)
        self._is_first = True

        self._camera_frame_id = None
        self._camera_prim = None
        self._sim_prim = None

        self._init_ros_node_if_needed()
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

    @property
    def robot(self):
        return self._robot_info.robot

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

    def _publish_world_object_tfs(self):
        # frame_id = "world"
        frame_id = "sim"

        stamp = rospy.Time.now()
        sim_objects_path = "/cortex/sim/objects"
        if is_prim_path_valid(sim_objects_path):
            sim_objects_prim = get_prim_at_path(sim_objects_path)
            prim_children = get_prim_children(sim_objects_prim)
            for prim in prim_children:
                prim_path = get_prim_path(prim)
                if not prim.HasAttribute("xformOp:orient"):
                    continue
                p = math_util.to_meters(prim.GetAttribute("xformOp:translate").Get())
                q = math_util.usd_quat_to_numpy(prim.GetAttribute("xformOp:orient").Get())
                T = math_util.pq2T(p, q)

                child_frame_id = prim_path[len("/cortex/sim/objects/") :]

                tf = ros_tf_util.pack_transform_stamped(T, child_frame_id, frame_id, stamp)
                # TODO: Enable easily switching between pyblishing ground truth and poses predicted
                # by perception.
                self.tf_broadcaster.sendTransform(tf)

            do_publish_camera_hack = False
            if do_publish_camera_hack:
                # Publish camera
                # TODO: hack to get the camera frame published. We need functionality from Isaac Sim to
                # publish a tf using the rospy.Time.now() rather than counting from 0.
                if self._camera_frame_id is None:
                    self._camera_frame_id = "rgb_camera_link"
                    self._camera_prim = XFormPrim(
                        "/cortex/sim/zelle2_with_frames_1/zelle2/rgb_camera_mount/%s" % self._camera_frame_id
                    )
                    self._sim_prim = XFormPrim("/cortex/sim")

                camera_frame_id = self._camera_frame_id
                camera_prim = self._camera_prim
                sim_prim = self._sim_prim

                camera_world_T = math_util.T_to_meters(math_util.pq2T(*camera_prim.get_world_pose()))
                sim_T = math_util.T_to_meters(math_util.pq2T(*sim_prim.get_world_pose()))
                camera_sim_T = math_util.invert_T(sim_T).dot(camera_world_T)

                child_frame_id = camera_frame_id
                verbose = False
                if verbose:
                    print("publishing camera_sim_T\n:", camera_sim_T)
                    print("- child_frame_id:", child_frame_id)
                    print("- frame_id:", frame_id)
                    print("sim_T:\n", sim_T)
                tf = ros_tf_util.pack_transform_stamped(camera_sim_T, child_frame_id, frame_id, stamp)
                self.tf_broadcaster.sendTransform(tf)

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
            robot = try_wrap_cortex_robot(domain="sim")
            if robot is None:
                return

            world = World.instance()
            world.scene.add(robot)

            self._robot_info = RobotInfo(robot)
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

        self._profiler.start_capture("sync_sim_objs")
        for name, obj in self._belief_objects.items():
            sync_sim = obj.prim.GetAttribute("cortex:sync_sim").Get()
            if sync_sim:
                print("syncing:", name)
                self._sim_objects["sim_" + name].set_local_pose(*obj.get_local_pose())
                obj.prim.GetAttribute("cortex:sync_sim").Set(Bool(False))

        self._profiler.start_capture("ros_pub")
        self._publish_commanded_joints()
        self._publish_uncommanded_joints()
        self._publish_world_object_tfs()
        self._profiler.end_capture("ros_pub")

        self._profiler.end_capture("sim_step_cb")

        self._profiler.end_cycle()
        if self._print_diagnistics:
            self._profiler.print_report()
        self._profiler.start_cycle()

    def on_shutdown(self):
        print()
        print()
        print("shutting down cortex sim extension")
        print()
        print()
        gc.collect()
