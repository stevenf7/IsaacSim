# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.kit.test
import carb
import asyncio
from pxr import Gf

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.motion_generation import ArticulationMotionPolicy, interface_config_loader
from omni.isaac.motion_generation.lula.motion_policies import RmpFlow
from omni.isaac.core.utils import distance_metrics
from omni.isaac.core.utils.stage import open_stage_async, update_stage_async
from omni.isaac.core.utils.rotations import gf_quat_to_np_array, quat_to_rot_matrix
from omni.isaac.core.utils.prims import is_prim_path_valid
import omni.isaac.core.objects as objects
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.robots.robot import Robot
import os
import json
import numpy as np


# Having a test class derived from omni.kit.test.AsyncTestCase declared on the root of module will
# make it auto-discoverable by omni.kit.test
class TestMotionPolicy(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._physics_dt = 1 / 60  # duration of physics frame in seconds

        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.motion_generation")
        self._articulation_policy_extension_path = ext_manager.get_extension_path(ext_id)

        self._polciy_config_dir = os.path.join(self._articulation_policy_extension_path, "motion_policy_configs")
        self.assertTrue(os.path.exists(os.path.join(self._polciy_config_dir, "policy_map.json")))
        with open(os.path.join(self._polciy_config_dir, "policy_map.json")) as policy_map:
            self._policy_map = json.load(policy_map)

        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(1 / self._physics_dt))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(1 / self._physics_dt))

        await update_stage_async()

        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await update_stage_async()
        self._articulation_policy = None
        self._dc = None
        await update_stage_async()
        pass

    async def test_rmpflow_visualization_franka(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")

        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        self._motion_policy.set_end_effector_target(np.array([40.0, 20.0, 40.0]))

        self._motion_policy.visualize_collision_spheres()
        self._motion_policy.visualize_end_effector_position()

        test_sphere = self._motion_policy.get_collision_spheres_as_prims()[-1]
        test_ee_visual = self._motion_policy.get_end_effector_as_prim()

        panda_hand_prim = XFormPrim("/panda/panda_hand")

        self._articulation_policy.move()

        for _ in range(100):
            sphere_pos, _ = test_sphere.get_world_pose()
            ee_pos, _ = test_ee_visual.get_world_pose()

            hand_pose, _ = panda_hand_prim.get_world_pose()

            self.assertTrue(
                abs(np.linalg.norm(sphere_pos - ee_pos) - 9.014) < 0.1,
                "End effector visualization is not consistent with sphere visualization",
            )
            self.assertTrue(
                abs(np.linalg.norm(hand_pose - ee_pos) - 10) < 1, "Simulated robot moved too far from RMP belief robot"
            )

            self._motion_policy.update_world()
            self._articulation_policy.move()
            await update_stage_async()

        self._motion_policy.delete_collision_sphere_prims()
        self._motion_policy.delete_end_effector_prim()
        self.assertTrue(not is_prim_path_valid("/lula/end_effector"))
        self.assertTrue(not is_prim_path_valid("/lula/collision_sphere0"))

        self._motion_policy.set_end_effector_target(np.array([80.0, 20.0, 80.0]))

        test_sphere = self._motion_policy.get_collision_spheres_as_prims()[-1]
        test_ee_visual = self._motion_policy.get_end_effector_as_prim()

        # self._articulation_policy.move()
        await update_stage_async()

        for _ in range(100):
            sphere_pos, _ = test_sphere.get_world_pose()
            ee_pos, _ = test_ee_visual.get_world_pose()

            hand_pose, _ = panda_hand_prim.get_world_pose()
            self.assertTrue(
                abs(np.linalg.norm(sphere_pos - ee_pos) - 9.014) < 0.1,
                "End effector visualization is not consistent with sphere visualization",
            )
            self.assertTrue(
                abs(np.linalg.norm(hand_pose - ee_pos) - 10) < 1, "Simulated robot moved too far from RMP belief robot"
            )

            self._motion_policy.update_world()
            self._articulation_policy.move()
            await update_stage_async()

        self._motion_policy.reset()
        self.assertTrue(not is_prim_path_valid("/lula/end_effector"))
        self.assertTrue(not is_prim_path_valid("/lula/collision_sphere0"))

    async def test_rmpflow_obstacle_adders(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")

        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        # These obstacle types are supported by RmpFlow
        obstacles = [
            objects.cuboid.VisualCuboid("/visual_cube"),
            objects.cuboid.DynamicCuboid("/dynamic_cube"),
            objects.cuboid.FixedCuboid("/fixed_cube"),
            objects.sphere.VisualSphere("/visual_sphere"),
            objects.sphere.DynamicSphere("/dynamic_sphere"),
            objects.capsule.VisualCapsule("/visual_capsule"),
            objects.capsule.DynamicCapsule("/dynamic_capsule"),
            objects.ground_plane.GroundPlane("/ground_plane"),
        ]

        # check that all the supported world update functions return successfully without error
        for obstacle in obstacles:
            self.assertTrue(self._motion_policy.add_obstacle(obstacle))
            self.assertTrue(self._motion_policy.disable_obstacle(obstacle))
            self.assertTrue(self._motion_policy.enable_obstacle(obstacle))
            self.assertTrue(self._motion_policy.remove_obstacle(obstacle))

        # make sure lula cleaned up after removing ground plane : Lula creates a wide, flat cuboid to mimic the ground because it doesn't support ground planes directly
        self.assertFalse(is_prim_path_valid("/lula/ground_plane"))

        for obstacle in obstacles:
            self.assertTrue(self._motion_policy.add_obstacle(obstacle))
        for obstacle in obstacles:
            # obstacle already in there
            self.assertFalse(self._motion_policy.add_obstacle(obstacle))
        self._motion_policy.reset()
        for obstacle in obstacles:
            # obstacles should have been deleted in reset
            self.assertFalse(self._motion_policy.disable_obstacle(obstacle))
            self.assertFalse(self._motion_policy.enable_obstacle(obstacle))
            self.assertFalse(self._motion_policy.remove_obstacle(obstacle))

        self.assertFalse(is_prim_path_valid("/lula/ground_plane"))

    async def test_rmpflow_on_franka(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        rmp_flow_motion_policy.set_ignore_state_updates(False)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        ground_truths = {
            "no_target": np.array(
                [
                    -0.004419703,
                    -0.27682272,
                    0.00093758915,
                    0.03678956,
                    0.00020130954,
                    -0.43393415,
                    0.0042535076,
                    None,
                    None,
                ]
            ),
            "target_no_obstacle": np.array(
                [0.2210225, -0.27587825, 0.20517401, 0.017939407, -0.031398155, -0.4379847, 0.004918524, None, None]
            ),
            "target_with_obstacle": np.array(
                [
                    -0.016580075,
                    -0.23463811,
                    -0.2108157,
                    -0.06434276,
                    -0.15900946,
                    -0.16524467,
                    -0.0048651816,
                    None,
                    None,
                ]
            ),
            "target_pos": np.array([40.0, 20.0, 40.0]),
            "obs_pos": np.array([30.0, 20.0, 50.0]),
        }
        await self.verify_policy_outputs(self._robot, ground_truths, dbg=False)

        timeout = 10

        await self.reset_robot(self._robot)

        target_pos = np.array([50.0, 0.0, 50.0])
        obstacle_pos = np.array([50.0, 0.0, 65.0])

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=np.array([0.0, 0.0, 0.0, 1.0]), obs_pos=obstacle_pos
        )

        self._robot.set_world_pose(np.array([10.0, 60.0, 0]))

        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        self._robot.set_world_pose(gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.1, 0.0, 1.0), 45).GetQuat())
        trans = np.array([10.0, -50.0, 0.0])
        self._robot.set_world_pose(trans, gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def test_rmpflow_on_franka_ignore_state(self):
        # Perform an internal rollout of robot state, ignoring simulated robot state updates

        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        rmp_flow_motion_policy.set_ignore_state_updates(True)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        """
        verify_policy_outputs() is not used here because
            1: The policy would not pass because it rolls out robot state internally rather than seeing
                that the robot is not moving, so the outputs become inconsistent.
            2: It is sufficient to confirm that the world state is updated correctly in
                test_rmpflow_on_franka_velocity_control().
        """
        await self.reset_robot(self._robot)
        timeout = 10

        target_pos = np.array([50.0, 0.0, 50.0])
        obstacle_pos = np.array([50.0, 0.0, 65.0])

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=np.array([0.0, 0.0, 0.0, 1.0]), obs_pos=obstacle_pos
        )

        self._robot.set_world_pose(np.array([10.0, 70.0, 0]))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        self._robot.set_world_pose(gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.1, 0.0, 1.0), 45).GetQuat())
        trans = np.array([10.0, -50.0, 0.0])
        self._robot.set_world_pose(trans, gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def test_rmpflow_static_obstacles_franka(self):
        # Perform an internal rollout of robot state, ignoring simulated robot state updates

        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("Franka", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        rmp_flow_motion_policy.set_ignore_state_updates(True)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()

        await self.reset_robot(self._robot)
        timeout = 10

        target_pos = np.array([50.0, 0.0, 50.0])
        obstacle_pos = np.array([50.0, 0.0, 65.0])

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=np.array([0.0, 0.0, 0.0, 1.0]), obs_pos=obstacle_pos, static=True
        )

        self._robot.set_world_pose(np.array([10.0, 70.0, 0]))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos, static=True)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        self._robot.set_world_pose(gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos, static=True)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.1, 0.0, 1.0), 45).GetQuat())
        trans = np.array([10.0, -50.0, 0.0])
        self._robot.set_world_pose(trans, gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos, static=True)

        pass

    async def test_rmpflow_on_ur10(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("UR10", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        rmp_flow_motion_policy.set_ignore_state_updates(False)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/ur10"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        ground_truths = {
            "no_target": np.array([-0.07553946, -0.036325723, -0.14323905, -0.24764434, 0.25067416, 8.164587e-09]),
            "target_no_obstacle": np.array([-0.43113947, 0.18771206, 0.3323818, 0.466794, -0.3631456, 1.5684996e-08]),
            "target_with_obstacle": np.array(
                [-0.41081357, 0.08700448, 0.37750724, 0.4768555, -0.37124863, 1.569822e-08]
            ),
            "target_pos": np.array([50.0, 0.0, 0.0]),
            "obs_pos": np.array([50.0, 0.0, -20.0]),
        }
        await self.verify_policy_outputs(self._robot, ground_truths, dbg=False)

        await self.reset_robot(self._robot)
        timeout = 10

        target_pos = np.array([50.0, 0.0, 70.0])
        obstacle_pos = np.array([80.0, 10.0, 80.0])

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=np.array([0.0, 0.0, 0.0, 1.0]), obs_pos=obstacle_pos
        )

        self._robot.set_world_pose(np.array([10.0, 70.0, 0]))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        self._robot.set_world_pose(gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.2, 0.0, 1.0), 90).GetQuat())
        trans = np.array([10.0, -50.0, 0.0])
        self._robot.set_world_pose(trans, gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def test_rmpflow_on_ur10_ignore_state(self):
        # Perform an internal rollout of robot state, ignoring simulated robot state updates

        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline = omni.timeline.get_timeline_interface()

        rmp_flow_motion_policy_config = interface_config_loader.load_supported_motion_policy_config("UR10", "RMPflow")
        rmp_flow_motion_policy = RmpFlow(**rmp_flow_motion_policy_config)
        rmp_flow_motion_policy.set_ignore_state_updates(True)
        self._motion_policy = rmp_flow_motion_policy

        robot_prim_path = "/ur10"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._robot = Robot(robot_prim_path)
        self._robot.initialize()
        await self.reset_robot(self._robot)

        self._articulation_policy = ArticulationMotionPolicy(self._robot, self._motion_policy, self._physics_dt)

        """
        verify_policy_outputs() is not used here because
            1: The policy would not pass because it rolls out robot state internally rather than seeing
                that the robot is not moving, so the outputs become inconsistent.
            2: It is sufficient to confirm that the world state is updated correctly in
                test_rmpflow_on_franka_velocity_control().
        """
        await self.reset_robot(self._robot)
        timeout = 10

        target_pos = np.array([50.0, 0.0, 70.0])
        obstacle_pos = np.array([80.0, 10.0, 80.0])

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=np.array([0.0, 0.0, 0.0, 1.0]), obs_pos=obstacle_pos
        )

        self._robot.set_world_pose(np.array([10.0, 70.0, 0]))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        self._robot.set_world_pose(gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(0.2, 0.0, 1.0), 90).GetQuat())
        trans = np.array([10.0, -50.0, 0.0])
        self._robot.set_world_pose(trans, gf_quat_to_np_array(rot_quat))
        await update_stage_async()
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def reached_end_effector_target(self, target_trans, target_orient, trans_thresh=2, rot_thresh=0.1):
        ee_trans, ee_rot = self._motion_policy.get_end_effector_pose(
            self._articulation_policy.get_active_joints_subset().get_joint_positions()
        )  # TODO this only works for RMPflow, and will be updated in upcoming MR before there are non-RMPflow tests

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

    async def add_block(self, path, offset, size=np.array([1.0, 1.0, 1.0]), collidable=True):
        if collidable:
            cuboid = objects.cuboid.DynamicCuboid(path, size=size)
            await update_stage_async()
            cuboid.disable_rigid_body_physics()
        else:
            cuboid = objects.cuboid.VisualCuboid(path, size=size)
        await update_stage_async()
        cuboid.set_world_pose(offset, np.array([1.0, 0, 0, 0]))
        await update_stage_async()

        return cuboid

    async def assertAlmostEqual(self, a, b):
        # overriding method because it doesn't support iterables
        a = np.array(a)
        b = np.array(b)
        self.assertFalse(np.any(abs((a[a != np.array(None)] - b[b != np.array(None)])) > 1e-3))
        pass

    async def simulate_until_target_reached(self, timeout, target_trans, target_orient=None):
        for frame in range(int(1 / self._physics_dt * timeout)):
            self._motion_policy.update_world()
            self._articulation_policy.move()
            await omni.kit.app.get_app().next_update_async()
            if await self.reached_end_effector_target(target_trans, target_orient=target_orient):
                return True, frame * self._physics_dt
        return False, timeout

    async def reset_robot(self, robot):
        """
        To make motion_generation outputs more deterministic, this method may be used to
        teleport the robot to specified position targets, setting velocity to 0

        This prevents changes in dynamic_control from affecting motion_generation tests
        """
        robot.post_reset()
        await update_stage_async()
        pass

    async def verify_policy_outputs(self, robot, ground_truths, dbg=False):
        """
        The ground truths are obtained by running this method in dbg mode
        when certain that motion_generation is working as intended.

        If position_control is True, motion_generation is expected to be using position targets

        In dbg mode, the returned velocity target values will be printed
        and no assertions will be checked.
        """

        # outputs of mg in different scenarios
        no_target_truth = ground_truths["no_target"]
        target_no_obs_truth = ground_truths["target_no_obstacle"]
        target_obs_truth = ground_truths["target_with_obstacle"]

        # where to put the target and obstacle
        target_pos = ground_truths["target_pos"]
        obs_pos = ground_truths["obs_pos"]

        target = await self.add_block("/scene/target", target_pos, size=5.0 * np.ones(3), collidable=False)

        await update_stage_async()

        obs = await self.add_block("/scene/obstacle", obs_pos, size=10.0 * np.ones(3))

        await update_stage_async()

        await self.reset_robot(robot)
        await update_stage_async()

        self._motion_policy.set_end_effector_target(None)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nNo target:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(no_target_truth, mg_velocity_targets)

        # Just the target
        self._motion_policy.set_end_effector_target(target_pos)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nWith target:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_velocity_targets)

        # Add the obstacle
        self._motion_policy.add_obstacle(obs)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nWith target and obstacle:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_velocity_targets)

        # Disable the obstacle: check that it matches no obstacle at all
        self._motion_policy.disable_obstacle(obs)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nWith target and disabled obstacle:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_velocity_targets)

        # Enable the obstacle: check consistency
        self._motion_policy.enable_obstacle(obs)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nWith target and enabled obstacle:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_velocity_targets)

        # Delete the obstacle: check consistency
        self._motion_policy.remove_obstacle(obs)
        self._motion_policy.update_world()
        action = self._articulation_policy.get_next_articulation_action()
        mg_velocity_targets = action.joint_velocities

        if dbg:
            print("\nWith target and deleted obstacle:")
            for target in mg_velocity_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_velocity_targets)

        return

    async def verify_robot_convergence(self, target_pos, timeout, target_orient=None, obs_pos=None, static=False):
        # Assert that the robot can reach the target within a given timeout

        target = await self.add_block("/scene/target", target_pos, size=5.0 * np.ones(3), collidable=False)
        self._motion_policy.set_robot_base_pose(*self._robot.get_world_pose())

        await omni.kit.app.get_app().next_update_async()
        obs_prim = None
        if obs_pos is not None:
            cuboid = await self.add_block("/scene/obstacle", obs_pos, size=10 * np.array([2.0, 3.0, 1.0]))

            await update_stage_async()
            self._motion_policy.add_obstacle(cuboid, static=static)

        self._motion_policy.set_end_effector_target(target_pos, target_orient)
        success, time_to_target = await self.simulate_until_target_reached(
            timeout, target_pos, target_orient=target_orient
        )
        if not success:
            self.assertTrue(False)

        if obs_prim is not None:
            self._motion_policy.remove_obstacle(cuboid)

        return
