# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import math

import isaacsim.core.utils.numpy.rotations as rot_utils
import numpy as np
import omni.kit.test
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.prims import SingleXFormPrim
from isaacsim.core.utils.semantics import add_update_semantics
from isaacsim.core.utils.stage import create_new_stage_async, update_stage_async
from isaacsim.sensors.camera import Camera
from omni.kit.viewport.utility import get_active_viewport

GOLDEN_POINTCLOUD_WORLD_FRAME = np.array(
    [
        [3.4925, 3.4925, 0.0],
        [3.4925, 0.0, -0.0],
        [3.4925, -3.4925, 0.0],
        [0.0, 3.4925, -0.0],
        [0.0, 0.0, 0.0],
        [0.0, -3.4925, -0.0],
        [-3.4925, 3.4925, 0.0],
        [-3.4925, 0.0, -0.0],
        [-3.4925, -3.4925, 0.0],
    ]
)

GOLDEN_POINTCLOUD_CAMERA_FRAME = np.array(
    [
        [-3.4925, -3.4925, 25.0],
        [0.0, -3.4925, 25.0],
        [3.4925, -3.4925, 25.0],
        [-3.4925, 0.0, 25.0],
        [0.0, 0.0, 25.0],
        [3.4925, 0.0, 25.0],
        [-3.4925, 3.4925, 25.0],
        [0.0, 3.4925, 25.0],
        [3.4925, 3.4925, 25.0],
    ]
)


class TestCameraSensor(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await create_new_stage_async()
        self.my_world = World(stage_units_in_meters=1.0)
        await self.my_world.initialize_simulation_context_async()
        await update_stage_async()
        self.my_world.scene.add_default_ground_plane()
        self.cube_2 = self.my_world.scene.add(
            DynamicCuboid(
                prim_path="/new_cube_2",
                name="cube_1",
                position=np.array([5.0, 3, 1.0]),
                scale=np.array([0.6, 0.5, 0.2]),
                size=1.0,
                color=np.array([255, 0, 0]),
            )
        )

        self.cube_3 = self.my_world.scene.add(
            DynamicCuboid(
                prim_path="/new_cube_3",
                name="cube_2",
                position=np.array([-5, 1, 3.0]),
                scale=np.array([0.1, 0.1, 0.1]),
                size=1.0,
                color=np.array([0, 0, 255]),
                linear_velocity=np.array([0, 0, 0.4]),
            )
        )
        self.xform = self.my_world.scene.add(
            SingleXFormPrim(
                prim_path="/World/rig",
                name="rig",
                position=np.array([5.0, 0.0, 5.0]),
                orientation=rot_utils.euler_angles_to_quats(np.array([0, -90, 0]), degrees=True),
            )
        )
        self.camera = self.my_world.scene.add(
            Camera(
                prim_path="/World/rig/camera",
                name="camera",
                position=np.array([0.0, 0.0, 25.0]),
                frequency=20,
                resolution=(256, 256),
                orientation=rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True),
            )
        )
        add_update_semantics(self.cube_2.prim, "cube")
        add_update_semantics(self.cube_3.prim, "cube")
        await update_stage_async()
        await update_stage_async()
        await self.my_world.reset_async()
        await update_stage_async()
        await update_stage_async()
        return

    # After running each test
    async def tearDown(self):
        self.my_world.stop()
        await omni.kit.app.get_app().next_update_async()
        self.camera = None
        self.viewport_camera = None
        self.my_world.clear_instance()
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            # print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        return

    async def test_world_poses(self):
        position, orientation = self.camera.get_world_pose()
        self.assertTrue(np.isclose(position, [0, 0, 25], atol=1e-05).all())
        self.assertTrue(
            np.isclose(
                orientation, rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True), atol=1e-05
            ).all()
        )
        translation, orientation = self.camera.get_local_pose()
        self.assertTrue(np.isclose(translation, [20, 0, 5], atol=1e-05).all())
        self.assertTrue(
            np.isclose(
                orientation, rot_utils.euler_angles_to_quats(np.array([0, 180, 0]), degrees=True), atol=1e-05
            ).all()
        )
        self.camera.set_local_pose(
            translation=[0, 0, 25], orientation=rot_utils.euler_angles_to_quats(np.array([0, 180, 0]), degrees=True)
        )
        return

    async def test_local_poses(self):
        return

    async def test_projection(self):
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 100)
        points_2d = self.camera.get_image_coords_from_world_points(
            np.array([self.cube_3.get_world_pose()[0], self.cube_2.get_world_pose()[0]])
        )
        # visual inspection golden values
        ## print(points_2d)
        self.assertTrue(np.isclose(points_2d[0], [103.51783101, 250.41131911]).all())
        self.assertTrue(np.isclose(points_2d[1], [54.40569416, 5.34284676]).all())
        points_3d = self.camera.get_world_points_from_image_coords(points_2d, np.array([24.94, 24.9]))
        self.assertTrue(np.isclose(points_3d[0], [-4.99799372, 0.99959505, 0.06]).all())
        self.assertTrue(np.isclose(points_3d[1], [4.99999901, 2.99999974, 0.1]).all())
        return

    async def test_data_acquisition(self):
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 1)
        self.camera.resume()
        for annotator in self.camera.supported_annotators:
            getattr(self.camera, "add_{}_to_frame".format(annotator))()
            # frequency is set to 20, rendering rate is set to 120, so do 6 updates to make sure always have a frame
            await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)
            data = self.camera.get_current_frame()
            self.assertTrue(len(data[annotator]) > 0, f"{annotator}")
            if isinstance(data[annotator], dict) and "data" in data[annotator]:
                self.assertTrue(len(data[annotator]["data"]) > 0, f"check for data in {annotator}")
            getattr(self.camera, "remove_{}_from_frame".format(annotator))()
            await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 1)
            data = self.camera.get_current_frame()
            self.assertTrue(annotator not in data.keys(), f"{annotator}")
        return

    async def test_properties(self):
        self.camera.set_focal_length(5.0)
        self.assertTrue(self.camera.get_focal_length() == 5.0)
        self.camera.set_focus_distance(0.01)
        self.assertTrue(math.isclose(self.camera.get_focus_distance(), 0.01, abs_tol=0.005))
        self.camera.set_lens_aperture(0.01)
        self.assertTrue(math.isclose(self.camera.get_lens_aperture(), 0.01, abs_tol=0.005))
        self.camera.set_horizontal_aperture(1.2)
        self.assertTrue(math.isclose(self.camera.get_horizontal_aperture(), 1.2, abs_tol=0.1))
        self.camera.set_vertical_aperture(1.2)
        self.assertTrue(math.isclose(self.camera.get_vertical_aperture(), 1.2, abs_tol=0.1))
        self.camera.set_clipping_range(1.0, 1.0e5)
        clipping_range = self.camera.get_clipping_range()
        self.assertTrue(math.isclose(clipping_range[0], 1.0, abs_tol=0.1))
        self.assertTrue(math.isclose(clipping_range[1], 1.0e5, abs_tol=0.1))
        self.camera.set_projection_type("fisheyeOrthographic")
        self.assertTrue(self.camera.get_projection_type() == "fisheyeOrthographic")
        # TODO: this causes a segfault
        # self.camera.set_projection_mode("orthographic")
        # self.assertTrue(self.camera.get_projection_mode() == "orthographic")
        self.camera.set_stereo_role("left")
        self.assertTrue(self.camera.get_stereo_role() == "left")
        self.camera.set_fisheye_polynomial_properties(
            nominal_width=120,
            nominal_height=240,
            optical_centre_x=24,
            optical_centre_y=25,
            max_fov=560,
            polynomial=[1, 2, 3, 4, 5],
        )
        (
            nominal_width,
            nominal_height,
            optical_centre_x,
            optical_centre_y,
            max_fov,
            polynomial,
        ) = self.camera.get_fisheye_polynomial_properties()
        self.assertTrue(math.isclose(nominal_width, 120, abs_tol=2))
        self.assertTrue(math.isclose(nominal_height, 240, abs_tol=2))
        self.assertTrue(math.isclose(optical_centre_x, 24, abs_tol=2))
        self.assertTrue(math.isclose(optical_centre_y, 25, abs_tol=2))
        self.assertTrue(math.isclose(max_fov, 560, abs_tol=2))
        self.assertTrue(np.isclose(polynomial, [1, 2, 3, 4, 5]).all())

        self.camera.set_rational_polynomial_properties(
            nominal_width=120,
            nominal_height=240,
            optical_centre_x=65,
            optical_centre_y=121,
            max_fov=180,
            distortion_model=[7, 5, -0.0002, -0.0001, 0, 7, 8, 2],
        )
        (cx, cy, fx, fy, pinhole) = self.camera.get_opencv_pinhole_properties()
        self.assertTrue(np.isclose(pinhole[:8], [7, 5, -0.0002, -0.0001, 0, 7, 8, 2], atol=0.00001).all())

        self.camera.set_kannala_brandt_properties(
            nominal_width=120,
            nominal_height=240,
            optical_centre_x=65,
            optical_centre_y=121,
            max_fov=180,
            distortion_model=[0.05, 0.01, -0.003, -0.0005],
        )
        (
            cx,
            cy,
            fx,
            fy,
            fisheye,
        ) = self.camera.get_opencv_fisheye_properties()
        self.assertTrue(np.isclose(fisheye, [0.05, 0.01, -0.003, -0.0005], atol=0.00001).all())

        self.camera.set_shutter_properties(delay_open=2.0, delay_close=3.0)
        delay_open, delay_close = self.camera.get_shutter_properties()
        self.assertTrue(math.isclose(delay_open, 2.0, abs_tol=0.1))
        self.assertTrue(math.isclose(delay_close, 3.0, abs_tol=0.1))
        self.camera.set_resolution((300, 300))
        resolution = self.camera.get_resolution()
        self.assertTrue(math.isclose(resolution[0], 300, abs_tol=0.1))
        self.assertTrue(math.isclose(resolution[1], 300, abs_tol=0.1))
        self.camera.get_aspect_ratio()
        self.camera.get_horizontal_fov()
        self.camera.get_vertical_fov()
        return

    async def test_viewport_camera(self):
        viewport_api = get_active_viewport()
        render_product_path = viewport_api.get_render_product_path()

        self.viewport_camera = Camera(
            prim_path="/World/rig/viewport_camera",
            name="viewport_camera",
            position=np.array([0.0, 0.0, 25.0]),
            resolution=(256, 256),
            orientation=rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True),
            render_product_path=render_product_path,
        )
        self.viewport_camera.initialize()
        self.viewport_camera.add_distance_to_image_plane_to_frame()
        self.viewport_camera.add_pointcloud_to_frame()

        await omni.syntheticdata.sensors.next_render_simulation_async(self.viewport_camera.get_render_product_path(), 1)
        self.assertEqual(self.viewport_camera.get_rgba().size, 256 * 256 * 4)
        self.assertEqual(self.viewport_camera.get_rgb().size, 256 * 256 * 3)
        self.assertEqual(self.viewport_camera.get_depth().size, 256 * 256 * 1)
        self.assertEqual(self.viewport_camera.get_pointcloud().size, 256 * 256 * 3)
        self.assertEqual(self.viewport_camera.get_render_product_path(), render_product_path)

    async def test_get_current_frame(self):
        current_frame_1 = self.camera.get_current_frame()
        current_frame_2 = self.camera.get_current_frame()

        # Make sure that the two frames refer to the same object
        self.assertIs(current_frame_1, current_frame_2)

        current_frame_3 = self.camera.get_current_frame()
        current_frame_4 = self.camera.get_current_frame(clone=True)

        # Make sure that the two frames refer to different objects
        self.assertIsNot(current_frame_3, current_frame_4)

    async def test_annotators_data(self):
        # Add all annotators to the camera
        self.camera.add_normals_to_frame()
        self.camera.add_motion_vectors_to_frame()
        self.camera.add_occlusion_to_frame()
        self.camera.add_distance_to_image_plane_to_frame()
        self.camera.add_distance_to_camera_to_frame()
        self.camera.add_bounding_box_2d_tight_to_frame()
        self.camera.add_bounding_box_2d_loose_to_frame()
        self.camera.add_bounding_box_3d_to_frame()
        self.camera.add_semantic_segmentation_to_frame()
        self.camera.add_instance_id_segmentation_to_frame()
        self.camera.add_instance_segmentation_to_frame()
        self.camera.add_pointcloud_to_frame()

        # Wait for the data to be available in the frame
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)
        current_frame = self.camera.get_current_frame()

        # Check the annotators data, shape, type and dtype
        normals_data = current_frame.get("normals")
        self.assertIsNotNone(normals_data)
        self.assertTrue(normals_data.shape == (256, 256, 4))
        self.assertTrue(isinstance(normals_data, np.ndarray))
        self.assertTrue(normals_data.dtype == np.float32)

        motion_vectors_data = current_frame.get("motion_vectors")
        self.assertIsNotNone(motion_vectors_data)
        self.assertTrue(motion_vectors_data.shape == (256, 256, 4))
        self.assertTrue(isinstance(motion_vectors_data, np.ndarray))
        self.assertTrue(motion_vectors_data.dtype == np.float32)

        occlusion_data = current_frame.get("occlusion")
        self.assertIsNotNone(occlusion_data)
        self.assertTrue(occlusion_data.shape == (4,))
        self.assertTrue(isinstance(occlusion_data, np.ndarray))
        self.assertTrue(
            occlusion_data.dtype
            == np.dtype([("instanceId", np.uint32), ("semanticId", np.uint32), ("occlusionRatio", np.float32)])
        )

        distance_to_image_plane_data = current_frame.get("distance_to_image_plane")
        self.assertIsNotNone(distance_to_image_plane_data)
        self.assertTrue(distance_to_image_plane_data.shape == (256, 256))
        self.assertTrue(isinstance(distance_to_image_plane_data, np.ndarray))
        self.assertTrue(distance_to_image_plane_data.dtype == np.float32)

        distance_to_camera_data = current_frame.get("distance_to_camera")
        self.assertIsNotNone(distance_to_camera_data)
        self.assertTrue(distance_to_camera_data.shape == (256, 256))
        self.assertTrue(isinstance(distance_to_camera_data, np.ndarray))
        self.assertTrue(distance_to_camera_data.dtype == np.float32)

        bounding_box_2d_tight_data = current_frame.get("bounding_box_2d_tight")
        self.assertIsNotNone(bounding_box_2d_tight_data)
        self.assertTrue(bounding_box_2d_tight_data["data"].shape == (1,))
        self.assertTrue(isinstance(bounding_box_2d_tight_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_2d_tight_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.int32),
                    ("y_min", np.int32),
                    ("x_max", np.int32),
                    ("y_max", np.int32),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        bounding_box_2d_loose_data = current_frame.get("bounding_box_2d_loose")
        self.assertIsNotNone(bounding_box_2d_loose_data)
        self.assertTrue(bounding_box_2d_loose_data["data"].shape == (1,))
        self.assertTrue(isinstance(bounding_box_2d_loose_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_2d_loose_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.int32),
                    ("y_min", np.int32),
                    ("x_max", np.int32),
                    ("y_max", np.int32),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        bounding_box_3d_data = current_frame.get("bounding_box_3d")
        self.assertIsNotNone(bounding_box_3d_data)
        self.assertTrue(bounding_box_3d_data["data"].shape == (1,))
        self.assertTrue(isinstance(bounding_box_3d_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_3d_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.float32),
                    ("y_min", np.float32),
                    ("z_min", np.float32),
                    ("x_max", np.float32),
                    ("y_max", np.float32),
                    ("z_max", np.float32),
                    ("transform", np.float32, (4, 4)),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        semantic_segmentation_data = current_frame.get("semantic_segmentation")
        self.assertIsNotNone(semantic_segmentation_data)
        self.assertTrue(semantic_segmentation_data["data"].shape == (256, 256))
        self.assertTrue(isinstance(semantic_segmentation_data["data"], np.ndarray))
        self.assertTrue(semantic_segmentation_data["data"].dtype == np.uint32)

        instance_id_segmentation_data = current_frame.get("instance_id_segmentation")
        self.assertIsNotNone(instance_id_segmentation_data)
        self.assertTrue(instance_id_segmentation_data["data"].shape == (256, 256))
        self.assertTrue(isinstance(instance_id_segmentation_data["data"], np.ndarray))
        self.assertTrue(instance_id_segmentation_data["data"].dtype == np.uint32)

        instance_segmentation_data = current_frame.get("instance_segmentation")
        self.assertIsNotNone(instance_segmentation_data)
        self.assertTrue(instance_segmentation_data["data"].shape == (256, 256))
        self.assertTrue(isinstance(instance_segmentation_data["data"], np.ndarray))
        self.assertTrue(instance_segmentation_data["data"].dtype == np.uint32)

        pointcloud_data = current_frame.get("pointcloud")
        self.assertIsNotNone(pointcloud_data)
        self.assertTrue(pointcloud_data["data"].shape == (65536, 3))
        self.assertTrue(isinstance(pointcloud_data["data"], np.ndarray))
        self.assertTrue(pointcloud_data["data"].dtype == np.float32)

    async def test_annotators_data_with_init_params(self):
        # Add all annotators to the camera with dummy and known init_params entries
        self.camera.add_bounding_box_2d_tight_to_frame(init_params={"semanticTypes": ["dummy"]})
        self.camera.add_bounding_box_2d_loose_to_frame(init_params={"semanticTypes": ["dummy"]})
        self.camera.add_bounding_box_3d_to_frame(init_params={"semanticTypes": ["dummy"]})
        self.camera.add_semantic_segmentation_to_frame(init_params={"colorize": True})
        self.camera.add_instance_id_segmentation_to_frame(init_params={"colorize": True})
        self.camera.add_instance_segmentation_to_frame(init_params={"colorize": True})

        # Get the current frame
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)
        current_frame = self.camera.get_current_frame()

        bounding_box_2d_tight_data = current_frame.get("bounding_box_2d_tight")
        self.assertIsNotNone(bounding_box_2d_tight_data)
        self.assertTrue(bounding_box_2d_tight_data["data"].shape == (0,))  # No data since semanticTypes is dummy
        self.assertTrue(isinstance(bounding_box_2d_tight_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_2d_tight_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.int32),
                    ("y_min", np.int32),
                    ("x_max", np.int32),
                    ("y_max", np.int32),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        bounding_box_2d_loose_data = current_frame.get("bounding_box_2d_loose")
        self.assertIsNotNone(bounding_box_2d_loose_data)
        self.assertTrue(bounding_box_2d_loose_data["data"].shape == (0,))  # No data since semanticTypes is dummy
        self.assertTrue(isinstance(bounding_box_2d_loose_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_2d_loose_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.int32),
                    ("y_min", np.int32),
                    ("x_max", np.int32),
                    ("y_max", np.int32),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        bounding_box_3d_data = current_frame.get("bounding_box_3d")
        self.assertIsNotNone(bounding_box_3d_data)
        self.assertTrue(bounding_box_3d_data["data"].shape == (0,))  # No data since semanticTypes is dummy
        self.assertTrue(isinstance(bounding_box_3d_data["data"], np.ndarray))
        self.assertTrue(
            bounding_box_3d_data["data"].dtype
            == np.dtype(
                [
                    ("semanticId", np.uint32),
                    ("x_min", np.float32),
                    ("y_min", np.float32),
                    ("z_min", np.float32),
                    ("x_max", np.float32),
                    ("y_max", np.float32),
                    ("z_max", np.float32),
                    ("transform", np.float32, (4, 4)),
                    ("occlusionRatio", np.float32),
                ]
            )
        )

        semantic_segmentation_data = current_frame.get("semantic_segmentation")
        self.assertIsNotNone(semantic_segmentation_data)
        self.assertTrue(
            semantic_segmentation_data["data"].shape == (256, 256, 4)
        )  # Colorize is True, so 4 uint8 channels
        self.assertTrue(isinstance(semantic_segmentation_data["data"], np.ndarray))
        self.assertTrue(semantic_segmentation_data["data"].dtype == np.uint8)

        instance_id_segmentation_data = current_frame.get("instance_id_segmentation")
        self.assertIsNotNone(instance_id_segmentation_data)
        self.assertTrue(instance_id_segmentation_data["data"].shape == (256, 256, 4))
        self.assertTrue(isinstance(instance_id_segmentation_data["data"], np.ndarray))
        self.assertTrue(instance_id_segmentation_data["data"].dtype == np.uint8)

        instance_segmentation_data = current_frame.get("instance_segmentation")
        self.assertIsNotNone(instance_segmentation_data)
        self.assertTrue(instance_segmentation_data["data"].shape == (256, 256, 4))
        self.assertTrue(isinstance(instance_segmentation_data["data"], np.ndarray))
        self.assertTrue(instance_segmentation_data["data"].dtype == np.uint8)

    async def test_pointcloud_data(self):
        self.camera.set_resolution((3, 3))
        self.camera.add_pointcloud_to_frame()
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)

        pointcloud_data_world_frame = self.camera.get_pointcloud()
        self.assertTrue(
            np.allclose(pointcloud_data_world_frame.flatten(), GOLDEN_POINTCLOUD_WORLD_FRAME.flatten(), atol=1e-5)
        )

        pointcloud_data_camera_frame = self.camera.get_pointcloud(world_frame=False)
        self.assertTrue(
            np.allclose(pointcloud_data_camera_frame.flatten(), GOLDEN_POINTCLOUD_CAMERA_FRAME.flatten(), atol=1e-5)
        )

    async def test_pointcloud_data_with_depth_fallback(self):
        self.camera.set_resolution((3, 3))
        self.camera.add_distance_to_image_plane_to_frame()
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)

        pointcloud_data_world_frame = self.camera.get_pointcloud()
        self.assertTrue(
            np.allclose(pointcloud_data_world_frame.flatten(), GOLDEN_POINTCLOUD_WORLD_FRAME.flatten(), atol=1e-5)
        )

        pointcloud_data_camera_frame = self.camera.get_pointcloud(world_frame=False)
        self.assertTrue(
            np.allclose(pointcloud_data_camera_frame.flatten(), GOLDEN_POINTCLOUD_CAMERA_FRAME.flatten(), atol=1e-5)
        )

    async def test_pointcloud_data_only_labelled(self):
        self.camera.add_pointcloud_to_frame(include_unlabelled=False)
        await omni.syntheticdata.sensors.next_render_simulation_async(self.camera.get_render_product_path(), 10)
        pointcloud_data = self.camera.get_pointcloud()
        self.assertIsNotNone(pointcloud_data)
        # NOTE: 130 instead of 256*256 because only semantically labelled points are included
        self.assertTrue(pointcloud_data.shape == (130, 3))
        self.assertFalse(np.isnan(pointcloud_data).any())
        self.assertFalse(np.isinf(pointcloud_data).any())

        pointcloud_data_camera_frame = self.camera.get_pointcloud(world_frame=False)
        # NOTE: 130 instead of 256*256 because only semantically labelled points are included
        self.assertTrue(pointcloud_data_camera_frame.shape == (130, 3))
        self.assertFalse(np.isnan(pointcloud_data_camera_frame).any())
        self.assertFalse(np.isinf(pointcloud_data_camera_frame).any())
