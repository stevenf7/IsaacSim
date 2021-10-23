# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from pxr import UsdGeom, Gf, UsdPhysics, Sdf, UsdLux, PhysxSchema
import omni.ext
import omni.usd
import omni.kit.settings

from omni.isaac.motion_generation import MotionGenerator

from omni.isaac.dynamic_control import _dynamic_control
import omni.physx as _physx

from omni.physx.scripts.physicsUtils import add_ground_plane

from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.core.utils.stage import set_stage_up_axis
from omni.isaac.utils.scripts.scene_utils import setup_physics
from omni.isaac.core.utils import distance_metrics


def create_prim_from_usd(stage, prim_env_path, prim_usd_path, position):
    # create an empty Xform at the given path
    envPrim = stage.DefinePrim(prim_env_path, "Xform")
    # attach the USD to the given path
    envPrim.GetReferences().AddReference(prim_usd_path)

    xform = UsdGeom.Xformable(envPrim)
    xform.AddTransformOp().Set(position)


class RobotBenchmark:
    def __init__(self):
        self._timeline = omni.timeline.get_timeline_interface()

        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._physxIFace = _physx.acquire_physx_interface()

        self._first_step = True  # first step of simulation since things were reset or reloaded
        self.created = False  # robot has been created

        self._following = False  # following a cube that the user can drag around
        self._target_prim = None  # the prim for the cube that should be followed

        self._robot = None

        self._mg = None

        self._environment = None
        self._target_path = "/scene/target"

    def initialize_test(self, environment, robot_assets, policy_config, benchmark_logger=None):
        """ 
        load robot from USD
        """

        self._stage = omni.usd.get_context().get_stage()

        set_stage_up_axis("z")
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        self.motion_policy_config = policy_config

        """
        The path to the USD file for this robot is found in robot_assets.
        The USD file can be stored locally or be found on the Nucleus Server.
            If it is stored locally, the file path should be specified under "local_path_to_usd"
            If it is on the Nucleus Server, the file path should be specified under "nucleus_path_to_usd"
        """

        if "local_path_to_usd" in robot_assets:
            robot_usd = robot_assets["local_path_to_usd"]
        elif "nucleus_path_to_usd" in robot_assets:
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return
            asset_path = nucleus_server + "/Isaac"
            robot_usd = asset_path + robot_assets["nucleus_path_to_usd"]
        else:
            carb.log_error("No valid path to USD")
            return

        self.robot_path = "/scene/robot"
        robot_position = Gf.Matrix4d()  # identity matrix
        create_prim_from_usd(self._stage, self.robot_path, robot_usd, robot_position)

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
        self._mg = MotionGenerator(self._stage)
        self._environment = environment
        self._benchmark_logger = benchmark_logger

        self._default_target_position = Gf.Matrix4d().SetTranslate(Gf.Vec3d(30, 0.0, 30.0))
        self._default_target_position[0, 0] = -1
        self._default_target_position[2, 2] = -1

    def toggle_testing(self):
        if self._testing:
            self._testing = False
            self._mg.set_end_effector_target(None)
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

            if not self._mg.is_initialized():
                return

            if self._testing and not self.start_target_reached:
                """
                test is considered to have started when the initial target is reached
                start_target is conceptually different from a waypoint
                it is a position that the robot is expected to easily acheive in the environment
                """
                self._mg.move()
                self._toggle_obstacles(turn_on=False)
                self.start_target_reached = self._reached_target(self.start_target.GetPrim())

                if self.start_target_reached and self.waypoints:
                    waypoint = self.waypoints[self.waypoint_index]
                    waypoint.MakeVisible()
                    self.start_target.MakeInvisible()
                    self._mg.set_end_effector_target(waypoint.GetPrim())

            elif self._testing:
                # environment may change as a function of time once the robot is in place
                self._toggle_obstacles(turn_on=True)
                self._environment.update()
                self._log_frame()

                if not self.waypoints:
                    # just keep following start_target prim until timeout
                    self._mg.move()
                    if self._test_frame / self.fps >= self.test_timeout:
                        self._environment.reset(new_seed=self._environment.random_seed + 1)
                        self._initialize_new_scenario()
                        self._log_header(None)
                    else:
                        self._test_frame += 1

                else:
                    # follow a series of waypoints until timeout or completion
                    self._mg.move()

                    waypoint = self.waypoints[self.waypoint_index]
                    if self._reached_target(waypoint.GetPrim()):
                        waypoint.MakeInvisible()
                        self._log_header(True)
                        self.waypoint_index += 1
                        if self.waypoint_index == len(self.waypoints):
                            self._initialize_new_scenario()
                        else:
                            waypoint = self.waypoints[self.waypoint_index]
                            waypoint.MakeVisible()
                            self._mg.set_end_effector_target(waypoint.GetPrim())
                    elif self._test_frame / self.fps >= self.test_timeout:
                        waypoint.MakeInvisible()
                        self._log_header(False)
                        self._initialize_new_scenario()
                    else:
                        self._test_frame += 1

            elif self._following:
                """
                The target is a block that the user can drag around
                see follow_target()
                """
                self._environment.update()
                self._mg.move()
                self._toggle_obstacles(turn_on=True)

            else:
                """
                motion_generator will follow policy-specific default behavior when there is no target

                In lula based motion policies, a default c-space configuration is read from the
                robot description file to be used when there is no target specified
                """
                self._mg.set_end_effector_target(None)
                self._mg.move()
                self._toggle_obstacles(turn_on=False)

    def follow_target(self):
        # If target is not specified in `self._target_path`, position target will be set to [30, 0, 30] cm, with
        # an orientation target pi rad about the y axis
        if not self._stage.GetPrimAtPath(self._target_path):
            target_geom = UsdGeom.Cube.Define(self._stage, self._target_path)

            colors = Gf.Vec3f(1.0, 0, 0)
            target_size = 8
            target_geom.CreateSizeAttr(target_size)
            target_geom.AddTransformOp().Set(self._default_target_position)
            target_geom.CreateDisplayColorAttr().Set([colors])
            self._target_prim = self._stage.GetPrimAtPath(self._target_path)

        self._mg.set_end_effector_target(self._target_prim)

        # start following it
        self._following = True
        self._testing = False

    def reset(self):
        self._following = False
        self._testing = False
        self._test_frame = 0

        # reset the position of the followable target
        if self._target_prim:
            self._target_prim.GetAttribute("xformOp:transform").Set(self._default_target_position)

        if self._environment is not None:
            self._environment.reset()

        self._robot = None
        self._first_step = True

    def stop_tasks(self):
        self._robot = None
        self._first_step = True
        self._following = False
        self.created = False

    def get_articulation(self):
        return self._dc.get_articulation(self.robot_path)

    def _setup_world(self):
        # get handle to the articulation for this robot
        robot_prim = self._stage.GetPrimAtPath(self.robot_path)
        self._ar = self._dc.get_articulation(self.robot_path)

        body_count = self._dc.get_articulation_body_count(self._ar)
        for bodyIdx in range(body_count):
            body = self._dc.get_articulation_body(self._ar, bodyIdx)
            self._dc.set_rigid_body_disable_gravity(body, True)

        """
        Environments may specify a desired starting cspace position for the robot.  If specified, the robot
        will be teleported to this position on the first frame after loading or resetting.
        """
        init_robot_cspace_position = self._environment.get_initial_robot_cspace_position()
        if init_robot_cspace_position is not None:
            dof_states = self._dc.get_articulation_dof_states(self._ar, _dynamic_control.STATE_POS)
            dof_states["pos"] = init_robot_cspace_position
            self._dc.set_articulation_dof_states(self._ar, dof_states, _dynamic_control.STATE_ALL)

        """
        The MotionGenerator has its own internal world.  All obstacles that the
        robot should avoid should be passed in to the motion generator as prims.

        The MotionGenerator currently supports three primitive object types: sphere, cube, capsule
        Test Environments are created from only these types of prims
        """
        self._mg.initialize(self.motion_policy_config, robot_prim, self.fps)
        if not self._mg.is_initialized():
            carb.log_error("Motion Generator was unable to initialize")
            return

        self.obstacles = self._environment.get_all_prims()
        self.obstacles_on = True
        for prim in self.obstacles:
            obs_type = prim.GetCustomDataByKey("type")
            if obs_type == "box":
                self._mg.create_block(prim)
            elif obs_type == "sphere":
                self._mg.create_sphere(prim)
            elif obs_type == "capsule":
                self._mg.create_capsule(prim)

    def _reached_target(self, target_prim):
        ee_trans, ee_rot = self._mg.get_end_effector_pose()

        target_trans, target_rot = self._mg.get_prim_pose(target_prim, default_trans=None, default_rot=None)

        trans_thresh, rot_thresh = self._environment.get_target_thresholds()

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
                self._mg.disable_obstacle(obs)
            self.obstacles_on = False

        elif not self.obstacles_on and turn_on:
            for obs in self.obstacles:
                self._mg.enable_obstacle(obs)
            self.obstacles_on = True

    def _initialize_new_scenario(self):
        if not self._mg.is_initialized():
            carb.log_error("Attempted to start new scenario before MotionGenerator was initialized")

        self.start_target, self.waypoints, self.test_timeout = self._environment.get_new_scenario()
        """
        start_target and waypoints are UsdGeom objects.
        This makes it easier to change properties like visibility than if they were UsdPrims.

        If start_target is None, the scenario is considered to be completed immediately (nothing happens)
        """
        if self.start_target is None:
            self._testing = False
            return

        self._mg.set_end_effector_target(self.start_target.GetPrim())
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
        target_pos, target_rot = self._mg.get_prim_pose(target.GetPrim(), default_trans=None, default_rot=None)
        ee_pos, ee_rot = self._mg.get_end_effector_pose()
        frame_descriptor = {
            "robot_cspace_config": self._mg.get_active_joint_states()[0],
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
                waypoint_pos, waypoint_rot = self._mg.get_prim_pose(waypoint.GetPrim())
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

    def _create_ground(self):
        if not self._stage.GetPrimAtPath("/scene/ground"):
            self.ground_path = "/scene/ground"
            self.ground_geom = UsdGeom.Xform.Define(self._stage, self.ground_path)
            self.ground_geom.AddTranslateOp().Set(Gf.Vec3f(0, 0, -5))
            self.ground_prim = self._stage.GetPrimAtPath(self.ground_path)
        self._mg.create_block(self.ground_prim, (500, 500, 10), static=True)
