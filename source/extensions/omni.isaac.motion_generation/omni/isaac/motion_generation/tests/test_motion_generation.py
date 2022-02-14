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
from pxr import Usd, UsdGeom, Gf

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.motion_generation import MotionGenerator
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.utils import distance_metrics
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.stage import open_stage_async, update_stage_async
from omni.isaac.core.utils.rotations import gf_quat_to_np_array, quat_to_rot_matrix
import omni.isaac.core.objects as objects
from omni.isaac.core.robots.robot import Robot
import os
import json
import numpy as np


# Having a test class derived from omni.kit.test.AsyncTestCase declared on the root of module will
# make it auto-discoverable by omni.kit.test
class TestMotionGeneration(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._physics_rate = 60  # fps

        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.motion_generation")
        self._mg_extension_path = ext_manager.get_extension_path(ext_id)

        self._polciy_config_dir = os.path.join(self._mg_extension_path, "policy_configs")
        self.assertTrue(os.path.exists(os.path.join(self._polciy_config_dir, "policy_map.json")))
        with open(os.path.join(self._polciy_config_dir, "policy_map.json")) as policy_map:
            self._policy_map = json.load(policy_map)

        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        await omni.kit.app.get_app().next_update_async()

        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        self._mg = None
        self._dc = None
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_rmpflow_on_franka_velocity_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._timeline = omni.timeline.get_timeline_interface()

        self._mg = MotionGenerator()

        self.assertTrue("Franka" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["Franka"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["Franka"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = False

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._mg.initialize(config, robot_prim_path, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())
        self._robot = Robot(robot_prim_path)
        self._robot.initialize()

        ground_truths = {
            "no_target": np.array(
                [
                    -0.0043069986,
                    -0.26736322,
                    0.00089177204,
                    0.034041584,
                    0.00017974446,
                    -0.42201746,
                    0.0041315975,
                    None,
                    None,
                ]
            ),
            "target_no_obstacle": np.array(
                [0.21334785, -0.26832142, 0.19805957, 0.016657127, -0.030280387, -0.42940003, 0.004834217, None, None]
            ),
            "target_with_obstacle": np.array(
                [0.24528101, -0.227237, -0.3677186, -0.036989845, -0.32116067, -0.36346483, 0.05099256, None, None]
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

    async def test_rmpflow_on_franka_position_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline = omni.timeline.get_timeline_interface()

        self._mg = MotionGenerator()

        self.assertTrue("Franka" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["Franka"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["Franka"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = True  # This will make RMPflow use position control

        robot_prim_path = "/panda"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._mg.initialize(config, robot_prim_path, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())
        self._robot = Robot(robot_prim_path)
        self._robot.initialize()

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

    async def test_rmpflow_on_ur10_velocity_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline = omni.timeline.get_timeline_interface()

        self._mg = MotionGenerator()

        self.assertTrue("UR10" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["UR10"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["UR10"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = False

        robot_prim_path = "/ur10"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._mg.initialize(config, robot_prim_path, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())
        self._robot = Robot(robot_prim_path)
        self._robot.initialize()

        ground_truths = {
            "no_target": np.array([-0.07481546, -0.03572179, -0.13959081, -0.24084261, 0.24374281, 1.14902035e-08]),
            "target_no_obstacle": np.array([-0.42218196, 0.1785124, 0.33186314, 0.47452074, -0.36892414, 2.232083e-08]),
            "target_with_obstacle": np.array(
                [-0.40159395, 0.07815101, 0.3788256, 0.48301792, -0.3758465, 2.235655e-08]
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

    async def test_rmpflow_on_ur10_position_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline = omni.timeline.get_timeline_interface()

        self._mg = MotionGenerator()

        self.assertTrue("UR10" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["UR10"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["UR10"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = True  # This will cause RMPflow to use position control

        robot_prim_path = "/ur10"

        # Start Simulation and wait
        self._timeline.play()
        await update_stage_async()

        self._mg.initialize(config, robot_prim_path, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())
        self._robot = Robot(robot_prim_path)
        self._robot.initialize()

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

    async def process_policy_config(self, mp_config_file):
        """
            `mp_config_file` is expected to be an absolute path to a json file
            which provides configuration for the "MotionPolicy" being tested.
            A dictionary called "config" is created from reading this file

            Inside "config", relative paths included in "relative_asset_paths" will
            be prepended with the directory containing mp_config_file to convert to an absolute path.

            For example, if "config" constains:

            {
                "policy_type" : "RMP_Flow",
                "end_effector_frame_name": "tool",
                "relative_asset_paths": {
                    "robot_description_path" : "ur10_robot_description.yaml",
            }

            and mp_config_file is in the "path/to/config/" directory, then "config" will be converted to:

            {
                "policy_type" : "RMPflow",
                "end_effector_frame_name": "tool",
                "robot_description_path" : "/path/to/config/ur10_robot_description.yaml",
                "relative_asset_paths": {
                    "robot_description_path" : "ur10_robot_description.yaml",
                }
            }
        """

        self.assertTrue(os.path.exists(mp_config_file))
        mp_config_dir = os.path.dirname(mp_config_file)  # path to directory containing mp_config_file

        with open(mp_config_file) as config_file:
            config = json.load(config_file)

        rel_assets = config.get("relative_asset_paths", {})
        for k, v in rel_assets.items():
            config[k] = os.path.join(mp_config_dir, v)

        return config

    async def reached_end_effector_target(self, mg, target_trans, target_orient, trans_thresh=2, rot_thresh=0.1):
        ee_trans, ee_rot = mg.get_end_effector_pose()
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
        for frame in range(int(self._physics_rate * timeout)):
            self._mg.move()
            await omni.kit.app.get_app().next_update_async()
            if await self.reached_end_effector_target(self._mg, target_trans, target_orient=target_orient):
                return True, frame / self._physics_rate
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

    async def teleport_robot_to_target_pose(self, robot, position_control=False):
        self._mg._motion_policy.update()
        action = self._mg.get_next_articulation_action()
        if position_control:
            mg_targets = action.joint_positions
            # robot.set_joint_positions(mg_targets)
        else:
            mg_targets = action.joint_velocities
            # robot.set_joint_velocities(mg_targets)

        return mg_targets

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

        self._mg.set_end_effector_target(None)
        mg_targets = await self.teleport_robot_to_target_pose(robot)

        if dbg:
            print("\nNo target:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(no_target_truth, mg_targets)

        # Just the target
        self._mg.set_end_effector_target(target_pos)
        mg_targets = await self.teleport_robot_to_target_pose(robot)

        if dbg:
            print("\nWith target:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_targets)

        # Add the obstacle
        self._mg.add_obstacle(obs)
        mg_targets = await self.teleport_robot_to_target_pose(robot)
        if dbg:
            print("\nWith target and obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_targets)

        # Disable the obstacle: check that it matches no obstacle at all
        self._mg.disable_obstacle(obs)
        mg_targets = await self.teleport_robot_to_target_pose(robot)

        if dbg:
            print("\nWith target and disabled obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_targets)

        # Enable the obstacle: check consistency
        self._mg.enable_obstacle(obs)
        mg_targets = await self.teleport_robot_to_target_pose(robot)
        if dbg:
            print("\nWith target and enabled obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_targets)

        # Delete the obstacle: check consistency
        self._mg.remove_obstacle(obs)
        mg_targets = await self.teleport_robot_to_target_pose(robot)
        if dbg:
            print("\nWith target and deleted obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_targets)

        return

    async def verify_robot_convergence(self, target_pos, timeout, target_orient=None, obs_pos=None):
        # Assert that the robot can reach the target within a given timeout

        target = await self.add_block("/scene/target", target_pos, size=5.0 * np.ones(3), collidable=False)

        await omni.kit.app.get_app().next_update_async()
        obs_prim = None
        if obs_pos is not None:
            cuboid = await self.add_block("/scene/obstacle", obs_pos, size=10 * np.array([2.0, 3.0, 1.0]))

            await update_stage_async()
            self._mg.add_obstacle(cuboid)

        self._mg.set_end_effector_target(target_pos, target_orient)
        success, time_to_target = await self.simulate_until_target_reached(
            timeout, target_pos, target_orient=target_orient
        )
        if not success:
            self.assertTrue(False)

        if obs_prim is not None:
            self._mg.remove_obstacle(cuboid)

        return
