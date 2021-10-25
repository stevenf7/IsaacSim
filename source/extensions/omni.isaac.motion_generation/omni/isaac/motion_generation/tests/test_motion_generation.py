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
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.rotations import gf_quatf_to_np_array
import os
import json
import numpy as np


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will
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
        self._stage = omni.usd.get_context().get_stage()

        self._mg = MotionGenerator(self._stage)

        self.assertTrue("Franka" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["Franka"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["Franka"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = False

        robot_prim = self._stage.GetPrimAtPath("/panda")
        self.assertNotEqual(str(robot_prim.GetPath()), "")
        robot_geom = UsdGeom.Xform(robot_prim)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        self._art = self._dc.get_articulation("/panda")
        self.assertNotEqual(self._art, _dynamic_control.INVALID_HANDLE)

        self._mg.initialize(config, robot_prim, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())

        ground_truths = {
            "no_target": np.array(
                [
                    -0.00430752981895331,
                    -0.26727750341947537,
                    0.0008925738953648821,
                    0.03391302608767643,
                    0.00018004217857774634,
                    -0.42209955365745083,
                    0.004131720391633547,
                    0.0,
                    0.0,
                ]
            ),
            "target_no_obstacle": np.array(
                [
                    -0.01369895117365492,
                    -0.45094218430151306,
                    -0.00809666220652486,
                    -0.13677513307254918,
                    0.002352942930441275,
                    -0.510548022016821,
                    0.004776766595109004,
                    0.0,
                    0.0,
                ]
            ),
            "target_with_obstacle": np.array(
                [
                    0.05568620226157044,
                    -0.10873858405852888,
                    0.10435665705897278,
                    0.3097002497119422,
                    0.18799232525791543,
                    -0.41981174174802216,
                    -0.008583941233254446,
                    0.0,
                    0.0,
                ]
            ),
            "target_pos": Gf.Vec3d(40.0, 0.0, 40.0),
            "obs_pos": Gf.Vec3d(30.0, 0.0, 40.0),
        }
        await self.verify_policy_outputs(ground_truths)

        pos_targets = self._dc.get_articulation_dof_position_targets(self._art)
        timeout = 10

        target_pos = Gf.Vec3d(50.0, 0.0, 50.0)
        obstacle_pos = Gf.Vec3d(50.0, 0.0, 65.0)

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=Gf.Quatf(0.0, 0.0, 0.0, 1.0), obs_pos=obstacle_pos
        )
        xform_robot = XFormPrim(prim_path="/panda", position=np.array([10.0, 70.0, 0.0]))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        xform_robot.set_local_pose(orientation=gf_quatf_to_np_array(rot_quat))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot = Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(0.1, 0.0, 1.0), 45))
        trans = Gf.Vec3d(10.0, -50.0, 0.0)
        transform = Gf.Matrix4d()
        transform.SetTranslate(trans)
        transform.SetRotateOnly(rot)

        robot_geom.AddTransformOp().Set(transform)
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def test_rmpflow_on_franka_position_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()

        self._mg = MotionGenerator(self._stage)

        self.assertTrue("Franka" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["Franka"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["Franka"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = True  # This will make RMPflow use position control

        robot_prim = self._stage.GetPrimAtPath("/panda")
        self.assertNotEqual(str(robot_prim.GetPath()), "")
        robot_geom = UsdGeom.Xform(robot_prim)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        self._art = self._dc.get_articulation("/panda")
        self.assertNotEqual(self._art, _dynamic_control.INVALID_HANDLE)

        self._mg.initialize(config, robot_prim, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())

        """
        verify_policy_outputs() is not used here because 
            1: The policy would not pass because it rolls out robot state internally rather than seeing 
                that the robot is not moving, so the outputs become inconsistent.
            2: It is sufficient to confirm that the world state is updated correctly in 
                test_rmpflow_on_franka_velocity_control().
        """
        await self.teleport_robot_to_dc_pos_targets()
        timeout = 10

        target_pos = Gf.Vec3d(50.0, 0.0, 50.0)
        obstacle_pos = Gf.Vec3d(50.0, 0.0, 65.0)

        await self.verify_robot_convergence(
            target_pos, timeout, target_orient=Gf.Quatf(0.0, 0.0, 0.0, 1.0), obs_pos=obstacle_pos
        )

        xform_robot = XFormPrim(prim_path="/panda", position=np.array([10.0, 70.0, 0.0]))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        xform_robot.set_local_pose(orientation=gf_quatf_to_np_array(rot_quat))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        rot = Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(0.1, 0.0, 1.0), 45))
        trans = Gf.Vec3d(10.0, -50.0, 0.0)
        transform = Gf.Matrix4d()
        transform.SetTranslate(trans)
        transform.SetRotateOnly(rot)

        robot_geom.AddTransformOp().Set(transform)
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obstacle_pos)

        pass

    async def test_rmpflow_on_ur10_velocity_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()

        self._mg = MotionGenerator(self._stage)

        self.assertTrue("UR10" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["UR10"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["UR10"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = False

        robot_prim = self._stage.GetPrimAtPath("/ur10")
        self.assertNotEqual(str(robot_prim.GetPath()), "")
        robot_geom = UsdGeom.Xform(robot_prim)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        self._art = self._dc.get_articulation("/ur10")
        self.assertNotEqual(self._art, _dynamic_control.INVALID_HANDLE)

        self._mg.initialize(config, robot_prim, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())

        ground_truths = {
            "no_target": np.array([-0.07482819, -0.03575732, -0.13965198, -0.24087109, 0.2437708, 3.5758836e-18]),
            "target_no_obstacle": np.array(
                [-0.4218098, 0.17964546, 0.3320944, 0.47430024, -0.36874405, -6.0895833e-18]
            ),
            "target_with_obstacle": np.array(
                [-0.40133855, 0.0791791, 0.37916863, 0.48281658, -0.37568298, 2.1197544e-19]
            ),
            "target_pos": Gf.Vec3d(50.0, 0.0, 0.0),
            "obs_pos": Gf.Vec3d(50.0, 0.0, -20.0),
        }
        await self.verify_policy_outputs(ground_truths, dbg=False)

        target_pos = Gf.Vec3d(50.0, 0.0, 50.0)
        obs_pos = Gf.Vec3d(60.0, 10.0, 60.0)
        timeout = 5
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        xform_robot = XFormPrim(prim_path="/ur10", position=np.array([10.0, 70.0, 0.0]))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -np.pi / 4).GetQuat())
        xform_robot.set_local_pose(orientation=gf_quatf_to_np_array(rot_quat))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        robot_prim.GetAttribute("xformOp:orient").Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        robot_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, 0.0))
        rot = Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(0.0, 0.0, 1.0), np.pi / 2))
        trans = Gf.Vec3d(10.0, -50.0, 0.0)
        transform = Gf.Matrix4d()
        transform.SetTranslate(trans)
        transform.SetRotateOnly(rot)

        robot_geom.AddTransformOp().Set(transform)
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        pass

    async def test_rmpflow_on_ur10_position_control(self):
        (result, error) = await open_stage_async(self._dc_extension_path + "/data/usd/robots/ur10/ur10.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()

        self._mg = MotionGenerator(self._stage)

        self.assertTrue("UR10" in self._policy_map)
        self.assertTrue("RMPflow" in self._policy_map["UR10"])

        config_file = os.path.join(self._polciy_config_dir, self._policy_map["UR10"]["RMPflow"])
        config = await self.process_policy_config(config_file)
        config["ignore_robot_state_updates"] = True  # This will cause RMPflow to use position control

        robot_prim = self._stage.GetPrimAtPath("/ur10")
        self.assertNotEqual(str(robot_prim.GetPath()), "")
        robot_geom = UsdGeom.Xform(robot_prim)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        self._art = self._dc.get_articulation("/ur10")
        self.assertNotEqual(self._art, _dynamic_control.INVALID_HANDLE)

        self._mg.initialize(config, robot_prim, self._physics_rate)
        self.assertTrue(self._mg.is_initialized())

        target_pos = Gf.Vec3d(50.0, 0.0, 50.0)
        obs_pos = Gf.Vec3d(60.0, 10.0, 60.0)
        timeout = 5
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        xform_robot = XFormPrim(prim_path="/ur10", position=np.array([10.0, 70.0, 0.0]))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        rot_quat = Gf.Quatf(Gf.Rotation(Gf.Vec3d(1.0, 0.0, 0.0), -15).GetQuat())
        xform_robot.set_local_pose(orientation=gf_quatf_to_np_array(rot_quat))
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

        robot_prim.GetAttribute("xformOp:orient").Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        robot_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, 0.0))
        rot = Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(0.2, 0.0, 1.0), 90))
        trans = Gf.Vec3d(10.0, -50.0, 0.0)
        transform = Gf.Matrix4d()
        transform.SetTranslate(trans)
        transform.SetRotateOnly(rot)

        robot_geom.AddTransformOp().Set(transform)
        await self.verify_robot_convergence(target_pos, timeout, obs_pos=obs_pos)

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

    async def reached_end_effector_target(self, mg, target_prim, trans_thresh=0.02, rot_thresh=0.1):
        ee_trans, ee_rot = mg.get_end_effector_pose()

        target_trans, target_rot = mg.get_prim_pose(target_prim, default_trans=None, default_rot=None)

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

    async def add_block(self, path, size, offset, scale=Gf.Vec3d(1.0, 1.0, 1.0)):
        if not self._stage.GetPrimAtPath(path):
            cubeGeom = UsdGeom.Cube.Define(self._stage, path)
            cubePrim = self._stage.GetPrimAtPath(path)
            cubeGeom.CreateSizeAttr(size)
            cubeGeom.AddTranslateOp().Set(offset)
            cubeGeom.AddScaleOp().Set(scale)
        else:
            cubePrim = self._stage.GetPrimAtPath(path)
            cubeGeom = UsdGeom.Xformable(cubePrim)
            cubeGeom.ClearXformOpOrder()
            cubeGeom.AddTranslateOp().Set(offset)
            cubeGeom.AddScaleOp().Set(scale)
        # Need this to avoid flatcache errors
        await omni.kit.app.get_app().next_update_async()

        return cubePrim

    async def assertAlmostEqual(self, a, b):
        # overriding method because it doesn't support iterables

        self.assertFalse(np.any(abs((np.array(a) - np.array(b))) > 10e-4))
        pass

    async def simulate_until_target_reached(self, timeout, target_prim):
        for frame in range(int(self._physics_rate * timeout)):
            self._mg.move()
            await omni.kit.app.get_app().next_update_async()
            if await self.reached_end_effector_target(self._mg, target_prim):
                return True, frame / self._physics_rate
        return False, timeout

    async def teleport_robot_to_dc_pos_targets(self, pos_targets=None):
        """
        To make motion_generation outputs more deterministic, this method may be used to
        teleport the robot to the position and velocity targets of dynamic_control

        This prevents changes in dynamic_control from affecting motion_generation tests
        """
        dof_states = self._dc.get_articulation_dof_states(self._art, _dynamic_control.STATE_POS)
        if pos_targets is None:
            pos_targets = self._dc.get_articulation_dof_position_targets(self._art)
        dof_states["pos"] = pos_targets
        self._dc.set_articulation_dof_states(self._art, dof_states, _dynamic_control.STATE_ALL)
        await omni.kit.app.get_app().next_update_async()

    async def verify_policy_outputs(self, ground_truths, position_control=False, dbg=False):
        """
        The ground truths are obtained by running this method in dbg mode
        when certain that motion_generation is working as intended.

        If position_control is True, motion_generation is expected to be using position targets

        In dbg mode, the returned velocity target values will be printed
        and no assertions will be checked.
        """
        body_count = self._dc.get_articulation_body_count(self._art)
        for bodyIdx in range(body_count):
            body = self._dc.get_articulation_body(self._art, bodyIdx)
            self._dc.set_rigid_body_disable_gravity(body, True)

        # outputs of mg in different scenarios
        no_target_truth = ground_truths["no_target"]
        target_no_obs_truth = ground_truths["target_no_obstacle"]
        target_obs_truth = ground_truths["target_with_obstacle"]

        # where to put the target and obstacle
        target_pos = ground_truths["target_pos"]
        obs_pos = ground_truths["obs_pos"]

        await self.teleport_robot_to_dc_pos_targets()

        self._mg.set_end_effector_target(None)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
        if dbg:
            print("\nNo target:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(no_target_truth, mg_targets)

        target_prim = await self.add_block("/scene/target", 5, target_pos)
        await omni.kit.app.get_app().next_update_async()
        obs_prim = await self.add_block("/scene/obstacle", 10, obs_pos)
        await omni.kit.app.get_app().next_update_async()

        await self.teleport_robot_to_dc_pos_targets()

        # Just the target
        self._mg.set_end_effector_target(target_prim)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
        if dbg:
            print("\nWith target:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_targets)

        # Add the obstacle
        self._mg.create_cube(obs_prim)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
        if dbg:
            print("\nWith target and obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_targets)

        # Disable the obstacle: check that it matches no obstacle at all
        self._mg.disable_obstacle(obs_prim)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
        if dbg:
            print("\nWith target and disabled obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_no_obs_truth, mg_targets)

        # Enable the obstacle: check consistency
        self._mg.enable_obstacle(obs_prim)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
        if dbg:
            print("\nWith target and enabled obstacle:")
            for target in mg_targets:
                print(target, end=",")
            print()
        else:
            await self.assertAlmostEqual(target_obs_truth, mg_targets)

        # Delete the obstacle: check consistency
        self._mg.remove_obstacle(obs_prim)
        self._mg._motion_policy.update()
        if position_control:
            mg_targets = self._mg.get_joint_position_targets()
        else:
            mg_targets = self._mg.get_joint_velocity_targets()
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

        target_prim = await self.add_block("/scene/target", 5, target_pos)
        target_geom = UsdGeom.Xformable(target_prim)
        if target_orient:
            target_geom.AddOrientOp().Set(target_orient)
        await omni.kit.app.get_app().next_update_async()
        obs_prim = None
        if obs_pos is not None:
            obs_prim = await self.add_block("/scene/obstacle", 10, obs_pos, scale=Gf.Vec3d(2.0, 3.0, 1.0))
            await omni.kit.app.get_app().next_update_async()
            self._mg.create_block(obs_prim)

        self._mg.set_end_effector_target(target_prim)
        success, time_to_target = await self.simulate_until_target_reached(timeout, target_prim)
        if not success:
            self.assertTrue(False)

        if obs_prim is not None:
            self._mg.remove_obstacle(obs_prim)

        return
