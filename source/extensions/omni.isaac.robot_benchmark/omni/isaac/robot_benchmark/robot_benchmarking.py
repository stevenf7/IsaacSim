# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from pxr import UsdPhysics, Sdf, UsdLux, PhysxSchema
import omni.ext
import omni.usd

from omni.isaac.motion_generation import ArticulationSubset, ArticulationMotionPolicy
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import set_stage_up_axis
from omni.isaac.core.utils import distance_metrics
from omni.isaac.core.utils.prims import create_prim
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core import PhysicsContext
from omni.isaac.core import objects

import numpy as np


class RobotBenchmark:
    def __init__(self):
        self._timeline = omni.timeline.get_timeline_interface()

        self._first_step = True  # first step of simulation since things were reset or reloaded
        self.created = False  # robot has been created

        self._following = False  # following a cube that the user can drag around
        self._follow_target = None  # the cuboid that should be followed

        self._robot = None

        self._art_policy = None

        self._environment = None
        self._target_path = "/scene/target"

    def initialize_test(self, environment, robot_assets, motion_policy, benchmark_logger=None):
        """ 
        load robot from USD
        """

        self._stage = omni.usd.get_context().get_stage()

        set_stage_up_axis("z")
        PhysicsContext(physics_dt=1.0 / 60.0)

        self._ground_plane = objects.ground_plane.GroundPlane("/scene/ground_plane")

        self._motion_policy = motion_policy

        """
        The path to the USD file for this robot is found in robot_assets.
        The USD file can be stored locally or be found on the Nucleus Server.
            If it is stored locally, the file path should be specified under "local_path_to_usd"
            If it is on the Nucleus Server, the file path should be specified under "nucleus_path_to_usd"
        """

        if "local_path_to_usd" in robot_assets:
            robot_usd = robot_assets["local_path_to_usd"]
        elif "nucleus_path_to_usd" in robot_assets:
            assets_root_path = get_assets_root_path()
            if assets_root_path is None:
                carb.log_error("Could not find Isaac Sim assets folder")
                return
            robot_usd = assets_root_path + robot_assets["nucleus_path_to_usd"]
        else:
            carb.log_error("No valid path to USD")
            return

        self.robot_path = "/scene/robot"
        create_prim(prim_path=self.robot_path, usd_path=robot_usd)

        light_prim = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        light_prim.CreateIntensityAttr(500)

        # get the frequency in Hz of the simulation
        physxSceneAPI = None
        for prim in self._stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                physxSceneAPI = PhysxSchema.PhysxSceneAPI.Apply(prim)
        if physxSceneAPI is not None:
            self.fps = physxSceneAPI.GetTimeStepsPerSecondAttr().Get()
        else:
            self.fps = 60

        self._first_step = True
        self._following = False
        self.created = True
        self._testing = False
        self._environment = environment
        self._benchmark_logger = benchmark_logger

        self._default_target_trans = np.array([0.30, 0, 0.30])
        self._default_target_orient = np.array([0.0, 0, 1.0, 0.0])

        self._ignore_target_orientation = True

    def toggle_testing(self):
        if self._testing:
            self._testing = False
            self._motion_policy.set_end_effector_target(None)
        else:
            self._testing = True
            self._initialize_new_scenario()

    def step(self, step):
        """This function is called every timestep in the editor

        Arguments:
            step (float): elapsed time between steps
        """
        if self.created and self._timeline.is_playing():
            if self._first_step:
                self._first_step = False
                self._setup_world()

            if self._art_policy is None:
                return

            if self._testing and not self.start_target_reached:
                """
                test is considered to have started when the initial target is reached
                start_target is conceptually different from a waypoint
                it is a position that the robot is expected to easily acheive in the environment
                """
                self._motion_policy.update_world()
                self._art_policy.move()
                # self._toggle_obstacles(turn_on=False)
                self.start_target_reached = self._reached_end_effector_target(*self.start_target.get_world_pose())

                if self.start_target_reached and self.waypoints:
                    waypoint = self.waypoints[self.waypoint_index]
                    waypoint.set_visibility(True)
                    self.start_target.set_visibility(False)
                    self._set_end_effector_target(*waypoint.get_world_pose())

            elif self._testing:
                # environment may change as a function of time once the robot is in place
                # self._toggle_obstacles(turn_on=True)
                self._environment.update()
                self._log_frame()

                if not self.waypoints:
                    # just keep following start_target prim until timeout
                    self._motion_policy.update_world()
                    self._art_policy.move()
                    self._set_end_effector_target(*self.start_target.get_world_pose())
                    if self._test_frame / self.fps >= self.test_timeout:
                        self._environment.reset(new_seed=self._environment.random_seed + 1)
                        self._initialize_new_scenario()
                        self._log_header(None)
                    else:
                        self._test_frame += 1

                else:
                    # follow a series of waypoints until timeout or completion
                    waypoint = self.waypoints[self.waypoint_index]
                    self._set_end_effector_target(*waypoint.get_world_pose())
                    self._motion_policy.update_world()
                    self._art_policy.move()

                    if self._reached_end_effector_target(*waypoint.get_world_pose()):
                        waypoint.set_visibility(False)
                        self.waypoint_index += 1
                        if self.waypoint_index == len(self.waypoints):
                            self._log_header(True)
                            self._initialize_new_scenario()
                        else:
                            waypoint = self.waypoints[self.waypoint_index]
                            waypoint.set_visibility(True)
                            self._set_end_effector_target(*waypoint.get_world_pose())
                    elif self._test_frame / self.fps >= self.test_timeout:
                        waypoint.set_visibility(False)
                        self._log_header(False)
                        self._initialize_new_scenario()
                    else:
                        self._test_frame += 1

            elif self._following:
                """
                The target is a block that the user can drag around
                see follow_target()
                """
                self._set_end_effector_target(*self._follow_target.get_world_pose())
                self._environment.update()
                self._motion_policy.update_world()
                self._art_policy.move()
                # self._toggle_obstacles(turn_on=True)

            else:
                """
                motion_generator will follow policy-specific default behavior when there is no target

                In lula based motion policies, a default c-space configuration is read from the
                robot description file to be used when there is no target specified
                """
                self._motion_policy.set_end_effector_target(None)
                self._motion_policy.update_world()
                self._art_policy.move()
                # self._toggle_obstacles(turn_on=False)

    def _set_end_effector_target(self, target_trans, target_rot):
        if self._ignore_target_orientation:
            self._motion_policy.set_end_effector_target(target_trans)
        else:
            self._motion_policy.set_end_effector_target(target_trans, target_rot)

    def follow_target(self):
        # If target is not specified in `self._target_path`, position target will be set to [30, 0, 30] cm, with
        # an orientation target pi rad about the y axis
        self._follow_target = objects.cuboid.VisualCuboid(self._target_path, size=0.08, color=np.array([1.0, 0, 0]))
        self._follow_target.set_world_pose(self._default_target_trans, self._default_target_orient)

        self._set_end_effector_target(self._default_target_trans, self._default_target_orient)

        # start following it
        self._following = True
        self._testing = False

    def reset(self):
        self._following = False
        self._testing = False
        self._test_frame = 0

        # reset the position of the followable target
        if self._follow_target is not None:
            self._follow_target.set_world_pose(self._default_target_trans, self._default_target_orient)

        if self._environment is not None:
            self._environment.reset()

        self._robot = None
        self._first_step = True

    def stop_tasks(self):
        self._robot = None
        self._first_step = True
        self._following = False
        self.created = False

    def _setup_world(self):
        self._robot = Articulation(self.robot_path)
        self._robot.initialize()

        self._art_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, 1.0 / self.fps)

        self._robot.set_joint_velocities(np.zeros_like(self._robot.get_joint_velocities()))
        self._motion_policy.set_robot_base_pose(*self._robot.get_world_pose())

        self.obstacles = self._environment.get_all_obstacles()
        self.obstacles_on = True

        for obstacle in self.obstacles:
            self._motion_policy.add_obstacle(obstacle)

        self._motion_policy.add_obstacle(self._ground_plane)

    def _reached_end_effector_target(self, target_trans, target_orient):
        ee_trans, ee_rot = self._motion_policy.get_end_effector_pose(
            self._art_policy.get_active_joints_subset().get_joint_positions()
        )  # Implemented for RMPflow, but not required for all motion_policies -> Fix in future MR
        trans_thresh, rot_thresh = self._environment.get_target_thresholds()
        if self._ignore_target_orientation:
            target_orient = None

        if target_orient is not None:
            target_rot = quat_to_rot_matrix(target_orient)
        else:
            target_rot = None

        if target_rot is None and target_trans is None:
            return True
        elif target_rot is None:
            trans_dist = distance_metrics.weighted_translational_distance(ee_trans, target_trans)
            return trans_dist < trans_thresh
        elif target_trans is None:
            rot_dist = distance_metrics.rotational_distance_angle(ee_rot, target_rot)
            return rot_dist < rot_thresh
        else:
            trans_dist = distance_metrics.weighted_translational_distance(ee_trans, target_trans)
            rot_dist = distance_metrics.rotational_distance_angle(ee_rot, target_rot)
            return trans_dist < trans_thresh and rot_dist < rot_thresh

    def _toggle_obstacles(self, turn_on=True):
        if self.obstacles_on and not turn_on:
            for obs in self.obstacles:
                self._motion_policy.disable_obstacle(obs)
                # self.environment.set_collisions(False)
            self.obstacles_on = False

        elif not self.obstacles_on and turn_on:
            for obs in self.obstacles:
                self._motion_policy.enable_obstacle(obs)
                # self.environment.set_collisions(False)
            self.obstacles_on = True

    def _initialize_new_scenario(self):
        if self._art_policy is None:
            carb.log_error("Attempted to start new scenario before test was initialized")

        self.start_target, self.waypoints, self.test_timeout = self._environment.get_new_scenario()
        """
        start_target and waypoints are UsdGeom objects.
        This makes it easier to change properties like visibility than if they were UsdPrims.

        If start_target is None, the scenario is considered to be completed immediately (nothing happens)
        """

        if self.start_target is None:
            self._testing = False
            return

        self._set_end_effector_target(*self.start_target.get_world_pose())
        self.waypoint_index = 0  # on waypoint 0 in test
        self.start_target_reached = False
        self.end_target_reached = False
        self._test_frame = 0  # count of frames passed in test

        if self._benchmark_logger is not None:
            # start saving a new test
            self._benchmark_logger.new_test()

    def _log_frame(self):
        """
        the benchmark logger object accepts dictionaries to describe every frame
        any primitive type or iterable containing primitive types is supported as an argument

        the resulting json is written as a list of dictionaries for the frames of a test
        """

        if self._benchmark_logger is None:
            return

        if not self.waypoints:
            target = self.start_target
        else:
            target = self.waypoints[self.waypoint_index]
        target_pos, target_rot = target.get_world_pose()
        if self._ignore_target_orientation:
            target_rot = None
        ee_pos, ee_rot = self._motion_policy.get_end_effector_pose(
            self._art_policy.get_active_joints_subset().get_joint_positions()
        )
        frame_descriptor = {
            "robot_cspace_config": self._art_policy.get_active_joints_subset().get_joint_positions(),
            "ee_pos": ee_pos,
            "ee_rot": ee_rot,
            "target_pos": target_pos,
            "target_rot": target_rot,
            "frame_number": self._test_frame,
        }
        self._benchmark_logger.log_frame(**frame_descriptor)

    def _log_header(self, success):
        """
        each test can have one header associated with it to describe overarching information

        writing a header to a test that already has one will replace the old header
        """

        if self._benchmark_logger is None:
            return
        waypoint_poses = []
        waypoint_rots = []
        if self.waypoints:
            for waypoint in self.waypoints:
                waypoint_pos, waypoint_rot = waypoint.get_world_pose()
                waypoint_poses.append(waypoint_pos)
                waypoint_rots.append(waypoint_rot)
        header = {
            "success": success,
            "waypoint_poses": waypoint_poses,
            "waypoint_rots": waypoint_rots,
            "env_name": self._environment.name,
            "fps": self.fps,
        }
        self._benchmark_logger.log_header(**header)
