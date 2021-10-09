# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.commands
import carb
import carb.tokens
import copy
import os
import asyncio
import numpy as np
from pxr import Gf, UsdGeom, UsdPhysics
import random

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.syntheticdata as syn
from ..scripts import SyntheticDataHelper
from ..scripts.writers import NumpyWriter
from omni.syntheticdata.tests.utils import add_semantics


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestSyntheticUtils(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._physics_rate = 60
        self._time_step = 1.0 / self._physics_rate
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        carb.settings.get_settings().set("/app/asyncRendering", False)
        carb.settings.get_settings().set("/app/hydraEngine/waitIdle", True)
        await omni.kit.app.get_app().next_update_async()

        # Start Simulation and wait
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._sd_helper = SyntheticDataHelper()
        self._writer_helper = NumpyWriter
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(self._time_step)
        await omni.kit.app.get_app().next_update_async()
        pass

    def is_loading(self):
        message, loaded, loading = omni.usd.get_context().get_stage_loading_status()
        return loading > 0

    async def simulate(self, seconds, steps_per_sec=60):
        for frame in range(int(steps_per_sec * seconds)):
            await omni.kit.app.get_app().next_update_async()

    async def load_robot_scene(self):
        from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics
        from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
        from omni.physx.scripts.physicsUtils import add_ground_plane

        self._stage = self._usd_context.get_stage()
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        robot_usd = nucleus_server + "/Isaac/Robots/Carter/carter_sphere_wheels_lidar.usd"

        set_up_z_axis(self._stage)
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0, 0, -25), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        # setup high-level robot prim
        self.prim = self._stage.DefinePrim("/robot", "Xform")
        self.prim.GetReferences().AddReference(robot_usd)
        add_semantics(self.prim, "robot")
        rot_mat = Gf.Matrix3d(Gf.Rotation((0, 0, 1), 90))
        omni.kit.commands.execute(
            "TransformPrimCommand",
            path=self.prim.GetPath(),
            old_transform_matrix=None,
            new_transform_matrix=Gf.Matrix4d().SetRotate(rot_mat).SetTranslateOnly(Gf.Vec3d(0, -64, 0)),
        )

        # setup scene camera
        camera_path = "/Camera"
        camera = self._stage.DefinePrim(camera_path, "Camera")
        self.viewport_window = omni.kit.viewport.get_default_viewport_window()
        self.viewport_window.set_active_camera(camera_path)
        self.viewport_window.set_camera_position(camera_path, 300, 300, 300, True)
        self.viewport_window.set_camera_target(camera_path, 0, -64, 0, True)

        # Initialize syntheticdata sensors
        await omni.kit.app.get_app().next_update_async()
        sensor_type = syn._syntheticdata.SensorType
        await syn.sensors.initialize_async(
            self._viewport,
            [
                sensor_type.Rgb,
                sensor_type.DepthLinear,
                sensor_type.InstanceSegmentation,
                sensor_type.SemanticSegmentation,
                sensor_type.BoundingBox2DLoose,
                sensor_type.BoundingBox2DTight,
                sensor_type.BoundingBox3D,
            ],
            timeout=200,
        )
        await omni.kit.app.get_app().next_update_async()

    # Unit test for sensor groundtruth
    async def test_groundtruth(self):
        await self.load_robot_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.simulate(1.0)
        await omni.kit.app.get_app().next_update_async()
        gt = self._sd_helper.get_groundtruth(
            [
                "rgb",
                "depthLinear",
                "boundingBox2DTight",
                "boundingBox2DLoose",
                "instanceSegmentation",
                "semanticSegmentation",
                "boundingBox3D",
                "camera",
                "pose",
            ],
            self.viewport_window,
            verify_sensor_init=False,
        )
        # Validate Depth groundtruth
        gt_depth = gt["depthLinear"]
        self.assertAlmostEqual(np.min(gt_depth), 5.11157, delta=0.1)
        self.assertAlmostEqual(np.max(gt_depth), 7.4310575, delta=0.1)
        # Validate 2D BBox groundtruth
        gt_bbox2d = gt["boundingBox2DTight"]
        self.assertEqual(len(gt_bbox2d), 1)
        self.assertAlmostEqual(gt_bbox2d[0][6], 432, delta=2)
        self.assertAlmostEqual(gt_bbox2d[0][7], 138, delta=2)
        self.assertAlmostEqual(gt_bbox2d[0][8], 844, delta=2)
        self.assertAlmostEqual(gt_bbox2d[0][9], 542, delta=2)
        # Validate semantic segmentation groundtruth - 0 (unlabeled) and 1 (robot)
        gt_semantic = gt["semanticSegmentation"]
        self.assertEqual(len(np.unique(gt_semantic)), 2)
        # Validate 3D BBox groundtruth
        gt_bbox3d = gt["boundingBox3D"]
        self.assertEqual(len(gt_bbox3d), 1)
        self.assertAlmostEqual(gt_bbox3d[0][6], -43.021126, delta=0.01)
        self.assertAlmostEqual(gt_bbox3d[0][7], -31.312422, delta=0.01)
        self.assertAlmostEqual(gt_bbox3d[0][8], -25.154814, delta=0.01)
        self.assertAlmostEqual(gt_bbox3d[0][9], 24.200943, delta=0.01)
        self.assertAlmostEqual(gt_bbox3d[0][10], 31.31649, delta=0.01)
        self.assertAlmostEqual(gt_bbox3d[0][11], 41.19104, delta=0.01)
        # Validate camera groundtruth - position, fov, focal length, aperature
        gt_camera = gt["camera"]
        gt_camera_trans = gt_camera["pose"][3, :3]
        self.assertAlmostEqual(gt_camera_trans[0], 300.0, delta=0.001)
        self.assertAlmostEqual(gt_camera_trans[1], 300.0, delta=0.001)
        self.assertAlmostEqual(gt_camera_trans[2], 300.0, delta=0.001)
        self.assertEqual(gt_camera["resolution"]["width"], 1280)
        self.assertEqual(gt_camera["resolution"]["height"], 720)
        self.assertAlmostEqual(gt_camera["fov"], 0.4131223226073451, 1e-5)
        self.assertAlmostEqual(gt_camera["focal_length"], 50.0, 1e-5)
        self.assertAlmostEqual(gt_camera["horizontal_aperture"], 20.954999923706055, 1e-2)
        # Validate pose groundtruth - prim path, semantic label, position
        gt_pose = gt["pose"]
        self.assertEqual(len(gt_pose), 1)
        self.assertEqual(gt_pose[0][0], "/robot")
        self.assertEqual(gt_pose[0][2], "robot")
        gt_pose_trans = (gt_pose[0])[3][3, :3]
        self.assertAlmostEqual(gt_pose_trans[0], 0.0, delta=0.001)
        self.assertAlmostEqual(gt_pose_trans[1], -64.0, delta=0.001)
        self.assertAlmostEqual(gt_pose_trans[2], 0.0, delta=0.001)
        pass

    # Unit test for data writer
    async def test_writer(self):
        await self.load_robot_scene()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await self.simulate(1.0)
        await omni.kit.app.get_app().next_update_async()
        # Setting up config for writer
        sensor_settings = {}
        sensor_settings_viewport = {"rgb": {"enabled": True}}
        viewport_name = "Viewport"
        sensor_settings[viewport_name] = copy.deepcopy(sensor_settings_viewport)
        # Initialize data writer
        output_folder = os.getcwd() + "/output"
        data_writer = self._writer_helper(output_folder, 4, 100, sensor_settings)
        data_writer.start_threads()
        # Get rgb groundtruth
        gt = self._sd_helper.get_groundtruth(["rgb"], self.viewport_window, verify_sensor_init=False)
        # Write rgb groundtruth
        image_id = 1
        groundtruth = {"METADATA": {"image_id": str(image_id), "viewport_name": viewport_name}, "DATA": {}}
        groundtruth["DATA"]["RGB"] = gt["rgb"]
        data_writer.q.put(groundtruth)
        # Validate output file
        output_file_path = os.path.join(output_folder, viewport_name, "rgb", str(image_id) + ".png")
        await asyncio.sleep(0.1)
        self.assertEqual(os.path.isfile(output_file_path), True)
        pass

    # create a cube.
    async def add_cube(self, path, size, offset):
        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)

        # use add_semantics to set its class to Cube
        add_semantics(cubePrim, "cube")

        cubeGeom.CreateSizeAttr(size)

        cubeGeom.ClearXformOpOrder()
        cubeGeom.AddTranslateOp().Set(offset)

        await omni.kit.app.get_app().next_update_async()
        UsdPhysics.CollisionAPI.Apply(cubePrim)
        return cubePrim, cubeGeom

    # create a scene with a cube.
    async def load_cube_scene(self):
        from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics
        from omni.physx.scripts.physicsUtils import add_ground_plane

        # ensure we are done with all of scene setup.
        await omni.kit.app.get_app().next_update_async()

        self._stage = self._usd_context.get_stage()

        # check units
        meters_per_unit = UsdGeom.GetStageMetersPerUnit(self._stage)

        set_up_z_axis(self._stage)
        add_ground_plane(self._stage, "/physics/groundPlane", "Z", 1000.0, Gf.Vec3f(0.0, 0, -25), Gf.Vec3f(1.0))
        setup_physics(self._stage)

        # Add a cube at a "close" location
        self.cube_location = Gf.Vec3f(-300.0, 0.0, 50.0)
        self.cube, self.cube_geom = await self.add_cube("/World/Cube", 100.0, self.cube_location)

        # setup scene camera
        camera_path = "/Camera"
        camera = self._stage.DefinePrim(camera_path, "Camera")
        self.viewport_window = omni.kit.viewport.get_default_viewport_window()
        self.viewport_window.set_active_camera(camera_path)
        self.viewport_window.set_camera_position(camera_path, 200, 200, 200, True)
        self.viewport_window.set_camera_target(
            camera_path, self.cube_location[0], self.cube_location[1], self.cube_location[2], True
        )

        # Initialize syntheticdata sensors
        await omni.kit.app.get_app().next_update_async()
        sensor_type = syn._syntheticdata.SensorType
        await syn.sensors.initialize_async(
            self._viewport,
            [
                sensor_type.Rgb,
                sensor_type.DepthLinear,
                sensor_type.InstanceSegmentation,
                sensor_type.SemanticSegmentation,
                sensor_type.BoundingBox2DLoose,
                sensor_type.BoundingBox2DTight,
                sensor_type.BoundingBox3D,
            ],
            timeout=200,
        )
        await omni.kit.app.get_app().next_update_async()

    # Acquire a copy of the ground truth.
    def get_groundtruth(self):
        gt = self._sd_helper.get_groundtruth(
            [
                "rgb",
                "depthLinear",
                "boundingBox2DTight",
                "boundingBox2DLoose",
                "instanceSegmentation",
                "semanticSegmentation",
                "boundingBox3D",
                "camera",
                "pose",
            ],
            self.viewport_window,
            verify_sensor_init=False,
            wait_for_sensor_data=0.0,
        )
        return copy.deepcopy(gt)

    # Unit test for sensor groundtruth
    async def frame_lag_test(self, move):
        # start the scene

        # wait for update
        move(Gf.Vec3f(random.random() * 100, random.random() * 100, random.random() * 100))
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        # grab ground truth
        gt1 = self.get_groundtruth()

        # move the cube
        move(Gf.Vec3f(random.random() * 100, random.random() * 100, random.random() * 100))

        # wait for update
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        # grab ground truth
        gt2 = self.get_groundtruth()
        await omni.kit.app.get_app().next_update_async()
        gt3 = self.get_groundtruth()

        # ensure segmentation is identical
        gt_seg1 = gt1["semanticSegmentation"]
        gt_seg2 = gt2["semanticSegmentation"]
        self.assertEqual(len(np.unique(gt_seg1)), len(np.unique(gt_seg2)))

        # the cube 3d bboxes should be different after update
        gt_box3d1 = gt1["boundingBox3D"]
        gt_box3d2 = gt2["boundingBox3D"]
        gt_box3d3 = gt3["boundingBox3D"]

        # check the list size
        self.assertEqual(len(gt_box3d1), len(gt_box3d2))

        # check the corners, they should/must move to pass the test.
        self.assertNotEqual(gt_box3d1["corners"].tolist(), gt_box3d2["corners"].tolist())
        # Should be no change between these two frames
        self.assertEqual(gt_box3d2["corners"].tolist(), gt_box3d3["corners"].tolist())
        await omni.kit.app.get_app().next_update_async()
        # stop the scene

        pass

    # Test lag by executing a command
    async def test_oneframelag_kitcommand(self):
        await self.load_cube_scene()

        def set_prim_pose(location):
            omni.kit.commands.execute(
                "TransformPrimCommand",
                path=self.cube.GetPath(),
                old_transform_matrix=None,
                new_transform_matrix=Gf.Matrix4d()
                .SetRotate(Gf.Matrix3d(Gf.Rotation((0, 0, 1), 90)))
                .SetTranslateOnly(Gf.Vec3d(location)),
            )

        for frame in range(50):
            await self.frame_lag_test(set_prim_pose)
        pass

    # Test lag using a USD prim.
    async def test_oneframelag_usdprim(self):
        await self.load_cube_scene()

        def set_prim_pose(location):
            properties = self.cube.GetPropertyNames()
            if "xformOp:translate" in properties:
                translate_attr = self.cube.GetAttribute("xformOp:translate")
                translate_attr.Set(location)

        for frame in range(50):
            await self.frame_lag_test(set_prim_pose)
        pass
