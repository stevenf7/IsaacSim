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
from lula_ros.msg import JointPosVelAccCommand
from sensor_msgs.msg import JointState
from std_msgs.msg import Header, String
from std_msgs.msg import Bool as RosBool
import tf2_ros

import omni.physx as _physx
from omni.isaac.core import World
from omni.isaac.core.prims import XFormPrim, GeometryPrim
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_path, get_prim_children, is_prim_path_valid
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units, traverse_stage
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.franka import Franka
from pxr import Sdf
from pxr.Vt import Bool, Double

sys.path.append(os.path.dirname(__file__))
from cortex_utils import (
    find_nucleus_server_with_error_checks,
    try_load_robot,
    PosVel,
    extract_joint_state_subset,
    get_standard_split_joint_subset_commands,
    configure_franka,
)
import math_util
import ros_tf_util
from synchronized_time import SynchronizedTime
from tools import Profiler


# Stuff from cortex_create_main.py
import omni
from omni.isaac.core import World
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.materials.visual_material import VisualMaterial
from omni.isaac.core.objects import VisualCuboid, DynamicCuboid, FixedCuboid
from omni.isaac.core.prims import XFormPrim, RigidPrim, GeometryPrim
from omni.isaac.core.robots import Robot
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.prims import (
    delete_prim,
    is_prim_path_valid,
    get_prim_at_path,
    get_prim_path,
    define_prim,
    get_all_matching_child_prims,
    move_prim,
    get_prim_children,
)
from omni.isaac.core.utils.rotations import (
    quat_to_rot_matrix,
    matrix_to_euler_angles,
    euler_angles_to_quat,
    quat_to_euler_angles,
)
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units, traverse_stage
from omni.isaac.core.utils.string import find_unique_string_name
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.franka import Franka
from omni.isaac.motion_generation import RMPFlowController
from pxr import Sdf, Gf, UsdGeom, Usd
from pxr.Vt import Bool, Double

import math_util
from motion_commander import MotionCommander, open_gripper, close_gripper
from state_trajectory_recorder import StateTrajectoryRecorder
from tools import dynamic_reload, SteadyRate, CycleTimer, Profiler
from cortex_utils import configure_franka


class DfTreeWatcher:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.dbm = None
        self.stamp = None
        self.tree = None

        self.recording_attr = "record_animation_state_trajectory"

    @property
    def recording_requested(self):
        if not hasattr(self.dbm, self.recording_attr):
            return False
        return getattr(self.dbm, self.recording_attr)

    def deleted_recording_attribute_if_needed(self):
        if hasattr(self.dbm, self.recording_attr):
            delattr(self.dbm, self.recording_attr)

    def load(self, context_tools):
        import df_behavior_module as dbm

        self.dbm = dbm
        self.stamp = os.stat(self.dbm.__file__).st_mtime
        self.build_tree(context_tools)

    def reload_if_needed(self, context_tools):
        try:
            new_stamp = os.stat(self.dbm.__file__).st_mtime
        except Exception as e:
            print("<missing dbm (usually transient), retrying>")
            return False

        try:
            if new_stamp > self.stamp:
                if self.verbose:
                    print("<reloading dbm>")

                    self.deleted_recording_attribute_if_needed()
                    dynamic_reload(self.dbm)
                self.build_tree(context_tools)

                self.stamp = new_stamp
                return True
        except Exception as e:
            print("\nProblem dynamically reloading behavior.")
            import traceback

            traceback.print_exc()
        return False

    def build_tree(self, context_tools):
        try:
            self.tree = self.dbm.build_tree(context_tools)
        except Exception as e:
            print("\nProblem building tree.")
            import traceback

            traceback.print_exc()


class ContextTools:
    def __init__(self, world, objects, obstacles, robot, commander, sim_objects=None):
        self.world = world
        self.objects = objects
        self.obstacles = obstacles
        self.robot = robot
        self.commander = commander
        self.sim_objects = sim_objects


def add_end_effector_prim_to_franka(
    motion_commander, hand_prim_path="/cortex/world/franka/panda_hand", eff_prim_name="eff"
):
    eff_prim_path = hand_prim_path + "/" + eff_prim_name
    if is_prim_path_valid(eff_prim_path):
        # Don't need to add it. It already exists.
        return

    eff_prim = define_prim(prim_path=eff_prim_path, prim_type="Xform")
    xformable = UsdGeom.Xformable(eff_prim)
    xformable.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
    xformable.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionDouble, "")

    pose = motion_commander.calc_policy_eff_pose_rel_to_hand(hand_prim_path)
    p = pose.p / get_stage_units()
    q = pose.q

    transform = Gf.Transform()
    eff_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*p.tolist()))
    eff_prim.GetAttribute("xformOp:orient").Set(Gf.Quatd(*q.tolist()))


def make_target_prim(prim_path="/cortex/world/motion_controller_target"):
    # width = .03
    width = 0.01
    target_prim = VisualCuboid(
        prim_path, size=100.0 * np.array([width, width, width]), color=np.array([0.15, 0.15, 0.15])
    )
    return target_prim


def read_attr(prim, attr_name, default_value=None):
    if not prim.HasAttribute("cortex:is_obstacle"):
        return default_value
    return prim.GetAttribute("cortex:is_obstacle").Get()


def create_attr_if_nonexistent(prim, attr_name, sdf_type, default_value):
    if prim.HasAttribute(attr_name):
        return

    prim.CreateAttribute(attr_name, sdf_type, False).Set(default_value)


def add_cortex_attributes_to_robot(robot, is_suppressed, adaptive_cycle_dt):
    robot_prim = get_prim_at_path(robot.prim_path)
    create_attr_if_nonexistent(robot_prim, "cortex:is_suppressed", Sdf.ValueTypeNames.Bool, Bool(False))
    create_attr_if_nonexistent(
        robot_prim, "cortex:adaptive_cycle_dt", Sdf.ValueTypeNames.Double, Double(adaptive_cycle_dt)
    )

    # robot_prim.CreateAttribute("cortex:is_suppressed", Sdf.ValueTypeNames.Bool, False).Set(
    #        Bool(False))
    # robot_prim.CreateAttribute("cortex:adaptive_cycle_dt", Sdf.ValueTypeNames.Double, False).Set(
    #        Double(adaptive_cycle_dt))


def make_empty_world():
    world = World(stage_units_in_meters=0.01)
    return world


def load_festo_world():
    festo_assets_dir_path = "/assets/festo_workcell"
    # path = festo_assets_dir_path + "/festo_belief_sim_env.usd"
    path = festo_assets_dir_path + "/festo_cortex_world_env.usd"
    add_reference_to_stage(usd_path=path, prim_path="/cortex")


def make_api_objects(domain):
    objects = {}
    obstacles = {}

    world_objects_path = "/cortex/%s/objects" % domain
    if is_prim_path_valid(world_objects_path):
        print("api objs path valid:", world_objects_path)
        world_objects_prim = get_prim_at_path(world_objects_path)
        prim_children = get_prim_children(world_objects_prim)
        for prim in prim_children:
            prim_path = get_prim_path(prim)
            name = prim_path[len(world_objects_path + "/") :]
            # objects[name] = XFormPrim(prim_path=prim_path, name=name)
            objects[name] = GeometryPrim(prim_path=prim_path, name=name)

            if domain == "world":
                if read_attr(objects[name].prim, "cortex:is_obstacle", False):
                    obstacles[name] = objects[name]

    else:
        print("api objs path invalid:", world_objects_path)
    # objects["fixture"] = XFormPrim(prim_path="/cortex/%s/vtem_fixture"%domain, name="fixture")

    return objects, obstacles


def add_cortex_attributes_to_object(obj):
    prim = obj.prim

    create_attr_if_nonexistent(
        prim, "cortex:measured_pose:position", Sdf.ValueTypeNames.Vector3d, Gf.Vec3d(0.0, 0.0, 0.0)
    )
    create_attr_if_nonexistent(
        prim, "cortex:measured_pose:orient", Sdf.ValueTypeNames.Quatd, Gf.Quatd(1.0, 0.0, 0.0, 0.0)
    )
    create_attr_if_nonexistent(prim, "cortex:measured_pose:stamp", Sdf.ValueTypeNames.Double, Double(0.0))
    create_attr_if_nonexistent(prim, "cortex:measured_pose:timeout", Sdf.ValueTypeNames.Double, Double(-1.0))

    # prim.CreateAttribute("cortex:measured_pose:position", Sdf.ValueTypeNames.Vector3d, False).Set(
    #        Gf.Vec3d(0.,0.,0.))
    # prim.CreateAttribute("cortex:measured_pose:orient", Sdf.ValueTypeNames.Quatd, False).Set(
    #        Gf.Quatd(1., 0.,0.,0.))
    # prim.CreateAttribute("cortex:measured_pose:stamp", Sdf.ValueTypeNames.Double, False).Set(
    #        Double(0.))
    # prim.CreateAttribute("cortex:measured_pose:timeout", Sdf.ValueTypeNames.Double, False).Set(
    #        Double(-1.))


def add_cortex_attributes_to_objects(objects):
    for _, obj in objects.items():
        add_cortex_attributes_to_object(obj)


def add_obstacles_to_commander(commander, obstacles):
    for name, obs in obstacles.items():
        commander.mg.add_obstacle(obs)


def build_commander(physics_dt, robot, obstacles):
    # TODO(nratliff): there's some redundancy in the parameters. I added robot at the last minute to fix a bug
    # in MotionCommander's forward kin (should be from targets for consistency). Reconcile.

    # Setup the robot commander and replace its (xform) target prim with a visible version.
    motion_policy = RMPFlowController(
        name="rmpflow_controller",
        robot_prim_path="/cortex/world/franka",
        policy_map_path=["Franka", "RMPflowSmoothed"],
        # policy_map_path=["Franka", "RMPflowNoFeedback"],
        physics_dt=physics_dt,
    )
    target_prim = make_target_prim()
    commander = MotionCommander(robot, motion_policy, target_prim)

    add_end_effector_prim_to_franka(commander)
    add_obstacles_to_commander(commander, obstacles)

    return commander


def get_robot_and_add_to_world(name, path, world):
    if is_prim_path_valid(path):
        robot = world.scene.add(Franka(prim_path=path, name=name))
        return robot
    return None


EXTENSION_NAME = "Omni Isaac Cortex Core"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print()
        print()
        print("============================================================================")
        print("Initializing cortex core extension")
        print("============================================================================")
        print()

        self._verbose = False

        self._profiler = Profiler(name="cortex_core", alpha=0.99, skip_cycles=10, print_rate_hz=1.0)

        self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
        self._physics_call_count = 0
        self._is_setup = False

    def _setup(self):
        print("entering main")
        sim_position_offset = np.array([-2.0, 0.0, 0.0])

        world = make_empty_world()
        robot = None
        objects = None
        obstacles = None
        sim_robot = None
        sim_objects = None
        objects_need_initialization = False

        self._needs_reset = False

        # load_festo_world()

        # For setting up a camera viewport. Don't use this. Use isaac sim instead.
        # Set up the camera
        # viewport_handle = omni.kit.viewport_legacy.get_viewport_interface().create_instance()
        # viewport_window = omni.kit.viewport_legacy.get_viewport_interface().get_viewport_window(viewport_handle)

        robot = get_robot_and_add_to_world("franka", "/cortex/world/franka", world)
        sim_robot = get_robot_and_add_to_world("sim_franka", "/cortex/sim/franka", world)
        has_sim = sim_robot is not None

        objects, obstacles = make_api_objects(domain="world")
        if has_sim:
            sim_objects, _ = make_api_objects(domain="sim")

        # if has_sim and args.add_sim_obj_pose_noise:
        #    print("perturbing objects:")
        #    for i, (name, obj) in enumerate(sim_objects.items()):
        #        print("%d) checking %s" % (i, name))
        #        if "vtem" in name:
        #            print("  perturbing")
        #            p,q = obj.get_local_pose()
        #            e = quat_to_euler_angles(q)
        #            e[2] += .025*np.pi * np.random.standard_normal(1)
        #            q = euler_angles_to_quat(e)
        #            p += math_util.to_stage_units(.005 * np.random.standard_normal(3))
        #            print("  setting position to:", p)
        #            obj.set_local_pose(p,q)

        world.reset()
        world.play()

        # TODO: move this to a cortex_ext extension similar to cortex_sim. Currently, configuring the
        # sim robot is handled by the sim extension because it needs to work with Isaac Sim loaded sim
        # envs. Best to handle configuring the robot similarly in all cases.
        configure_franka(robot)

        add_cortex_attributes_to_objects(objects)

        rate_hz = 60.0
        physics_dt = 1.0 / rate_hz
        add_cortex_attributes_to_robot(robot, is_suppressed=False, adaptive_cycle_dt=physics_dt)

        # Set the robot to a retracted initial configuration.
        retracted_config = np.array([0.00, -1.3, 0.00, -2.87, 0.00, 2.00, 0.75, 0.0, 0.0])
        robot.set_joint_positions(retracted_config)

        # TODO: worry about this
        # world.step()  # Step the world to ensure the joint positions changes are available.

        ## Setup the robot commander and package it into context tools.
        commander = build_commander(physics_dt, robot, obstacles)
        context_tools = ContextTools(world, objects, obstacles, robot, commander, sim_objects)

        df_tree_watcher = DfTreeWatcher(verbose=True)
        df_tree_watcher.load(context_tools)

        self._robot = robot
        self._context_tools = context_tools
        self._df_tree_watcher = df_tree_watcher

        # print("<looping>")
        # rate = SteadyRate(rate_hz)
        # cycle_timer = CycleTimer()

        # report_errors = True

        # needs_reset = False

        # run_behaviors = True

        # profiler = Profiler(name="cortex_loop_runner", alpha=.99, skip_cycles=100)
        # state_trajectory_recorder = None
        # if args.record:
        #    state_trajectory_recorder = StateTrajectoryRecorder(
        #            "traj.pkl", robot, objects, sim_robot, sim_objects)

        # This is only need if we're running camera generation in sim and the belief at the same time. No longer a common use case.
        # if has_sim:
        #    left_viewport = omni.ui.Workspace.get_window("Viewport")
        #    right_viewport = omni.ui.Workspace.get_window("Viewport 2")
        #    right_viewport.dock_in(left_viewport, omni.ui.DockPosition.RIGHT)

    def _on_simulation_step(self, step):
        try:
            record = False
            self._physics_call_count += 1
            if self._verbose:
                print("cortex_core:", self._physics_call_count, "t:", time.time())

            if not self._is_setup:
                self._setup()
                self._profiler.start_cycle()
                self._is_setup = True

            robot_prim = get_prim_at_path(self._robot.prim_path)
            is_suppressed = robot_prim.GetAttribute("cortex:is_suppressed").Get()
            if is_suppressed:
                print("<cortex suppressed>")
                self._needs_reset = True
            else:
                # This signal of the attribute no longer being set is set by the ROS cortex extension in
                # the world.step() method below. This section runs after that, so the robot's joints
                # will already be set to the right things.
                if self._needs_reset:
                    print("<cortex resetting>")
                    self._context_tools.commander.reset()
                    self._needs_reset = False

                is_reloaded = self._df_tree_watcher.reload_if_needed(self._context_tools)
                if is_reloaded:
                    report_errors = True
                    if record:
                        if self._df_tree_watcher.recording_requested:
                            print("<starting recording>")
                            state_trajectory_recorder.activate()
                        else:
                            if state_trajectory_recorder.is_active:
                                print("<saving recording>")
                                state_trajectory_recorder.save()

                            print("<not recording>")

                if record and state_trajectory_recorder.is_active:
                    state_trajectory_recorder.snap()

                try:
                    self._df_tree_watcher.tree.tick()
                except Exception as e:
                    if True or report_errors:
                        print("\nProblem ticking tree.")
                        import traceback

                        traceback.print_exc()

                # Retrieve the latest action specified by the target prim.
                action = self._context_tools.commander.get_action()
                self._robot.get_articulation_controller().apply_action(action)

            self._profiler.end_cycle()
            self._profiler.print_report(max_rate_hz=1.0)
            self._profiler.start_cycle()

        except Exception as e:
            print("General exception caught:")
            import traceback

            traceback.print_exc()

    def on_shutdown(self):
        print()
        print("Shutting down cortex core extension")
        print()
        gc.collect()
