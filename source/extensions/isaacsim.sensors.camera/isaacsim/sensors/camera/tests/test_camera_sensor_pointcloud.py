# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import isaacsim.core.utils.numpy.rotations as rot_utils
import numpy as np
import omni.kit.app
import omni.kit.test
import omni.replicator.core as rep
import omni.timeline
from isaacsim.core.api.objects import FixedCuboid
from isaacsim.core.utils.stage import create_new_stage_async, update_stage_async
from isaacsim.sensors.camera import Camera
from isaacsim.sensors.camera.tests.utils import debug_draw_clear_points, debug_draw_pointcloud
from isaacsim.test.utils.image_capture import capture_rgb_data_async
from isaacsim.test.utils.image_io import save_rgb_image


class TestCameraSensorPointcloud(omni.kit.test.AsyncTestCase):
    """Test suite for Camera pointcloud functionality."""

    CAMERA_RESOLUTION = (256, 256)
    CAMERA_FREQUENCY = 60  # Hz
    NUM_WARMUP_FRAMES = 5
    GOLDEN_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "golden", "camera_pointcloud")
    TEST_OUTPUT_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "golden", "camera_pointcloud", "_out_test"
    )
    SAVE_GOLDEN_DATA = False  # WARNING: Overwrites existing golden data
    SAVE_TEST_DATA = False  # Save current test data for comparison
    SAVE_DEBUG_IMGS = False  # Save debug visualization images

    async def setUp(self):
        """Create a new stage for each test."""
        await update_stage_async()
        await create_new_stage_async()
        await update_stage_async()

    async def tearDown(self):
        """Stop the timeline and close the stage after each test."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.stop()
        omni.usd.get_context().close_stage()
        await update_stage_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await update_stage_async()

    async def _create_test_environment(self):
        """Create test environment with ground plane, cubes, and camera."""
        await create_new_stage_async()

        # Create a plane and dome light
        rep.functional.create.plane(position=(0, 0, 0), rotation=(0, 0, 0), scale=(10, 10, 10))
        rep.functional.create.dome_light(intensity=500)

        # Create cubes with different positions, scales, and orientations
        cube_1 = FixedCuboid(
            prim_path="/World/cube_1",
            name="cube_1",
            position=np.array([0.1, 0.15, 0.25]),
            scale=np.array([1.2, 0.8, 0.1]),
            orientation=rot_utils.euler_angles_to_quats(np.array([15, -10, 0]), degrees=True),
        )
        cube_2 = FixedCuboid(
            prim_path="/World/cube_2",
            name="cube_2",
            position=np.array([1, -1, 0]),
            scale=np.array([0.5, 0.6, 0.7]),
        )
        cube_3 = FixedCuboid(
            prim_path="/World/cube_3",
            name="cube_3",
            position=np.array([-1, -1, -0.25]),
        )

        # Create camera looking down at the scene
        camera = Camera(
            prim_path="/World/camera",
            name="camera",
            frequency=self.CAMERA_FREQUENCY,
            position=np.array([0.0, 0.0, 10]),
            resolution=self.CAMERA_RESOLUTION,
            orientation=rot_utils.euler_angles_to_quats(np.array([0, 90, 30]), degrees=True),
        )

        return camera, cube_1, cube_2, cube_3

    async def _start_data_capture(self, num_warm_up_frames: int = 0):
        """Start the timeline and optionally wait for valid data to be available."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()
        for _ in range(num_warm_up_frames):
            await update_stage_async()

    async def _compare_pointcloud_data_resolution(
        self, camera, resolution=(64, 64), save_golden_data=False, save_test_data=False, save_debug_imgs=False
    ):
        """Compare pointcloud data from depth and pointcloud annotators against golden data."""
        res_str = f"{resolution[0]}_{resolution[1]}"
        camera.set_resolution(resolution)
        resolution = camera.get_resolution()
        expected_shape = (resolution[0] * resolution[1], 3)

        # Get pointcloud data from depth annotator
        camera.add_distance_to_image_plane_to_frame()
        for _ in range(self.NUM_WARMUP_FRAMES):
            await update_stage_async()

        pointcloud_data_world_frame_from_depth = camera.get_pointcloud()
        pointcloud_data_camera_frame_from_depth = camera.get_pointcloud(world_frame=False)

        # Get pointcloud data from pointcloud annotator
        camera.add_pointcloud_to_frame()
        for _ in range(self.NUM_WARMUP_FRAMES):
            await update_stage_async()

        pointcloud_data_world_frame = camera.get_pointcloud()
        pointcloud_data_camera_frame = camera.get_pointcloud(world_frame=False)

        # Print debug info about the data
        print(f"\n=== Pointcloud Debug Info (resolution {res_str}) ===")
        print(f"Expected shape: {expected_shape}")
        print(f"World frame from depth: shape={pointcloud_data_world_frame_from_depth.shape}")
        print(f"Camera frame from depth: shape={pointcloud_data_camera_frame_from_depth.shape}")
        print(f"World frame from annotator: shape={pointcloud_data_world_frame.shape}")
        print(f"Camera frame from annotator: shape={pointcloud_data_camera_frame.shape}")

        # Save test data to temp directory (does NOT overwrite golden)
        if save_test_data:
            test_data_dir = os.path.join(self.TEST_OUTPUT_DIR, "test_data")
            os.makedirs(test_data_dir, exist_ok=True)
            print(f"Saving test data to {test_data_dir}")
            np.save(
                os.path.join(test_data_dir, f"pointcloud_world_frame_res_{res_str}.npy"), pointcloud_data_world_frame
            )
            np.save(
                os.path.join(test_data_dir, f"pointcloud_camera_frame_res_{res_str}.npy"), pointcloud_data_camera_frame
            )
            np.save(
                os.path.join(test_data_dir, f"pointcloud_world_from_depth_res_{res_str}.npy"),
                pointcloud_data_world_frame_from_depth,
            )
            np.save(
                os.path.join(test_data_dir, f"pointcloud_camera_from_depth_res_{res_str}.npy"),
                pointcloud_data_camera_frame_from_depth,
            )

        # Save debug images BEFORE assertions (so they're saved even if test fails)
        if save_debug_imgs:
            debug_img_dir = os.path.join(self.TEST_OUTPUT_DIR, "debug_imgs")
            os.makedirs(debug_img_dir, exist_ok=True)
            print(f"Saving debug images to {debug_img_dir}")
            green_color = (0, 1, 0, 0.75)
            green_size = 4
            red_color = (1, 0, 0, 0.5)
            red_size = 8

            # Draw world frame pointcloud data (green=annotator, red=depth)
            debug_draw_clear_points()
            debug_draw_pointcloud(pointcloud_data_world_frame, color=green_color, size=green_size)
            debug_draw_pointcloud(pointcloud_data_world_frame_from_depth, color=red_color, size=red_size)
            rgb_data = await capture_rgb_data_async(
                camera_position=(5, 5, 5), camera_look_at=(0, 0, 0), resolution=(1280, 720)
            )
            save_rgb_image(rgb_data, debug_img_dir, f"pointcloud_world_frame_res_{res_str}_rgb.png")

            # Draw camera frame pointcloud data (green=annotator, red=depth)
            debug_draw_clear_points()
            debug_draw_pointcloud(pointcloud_data_camera_frame, color=green_color, size=green_size)
            debug_draw_pointcloud(pointcloud_data_camera_frame_from_depth, color=red_color, size=red_size)
            rgb_data = await capture_rgb_data_async(
                camera_position=(5, 5, 15), camera_look_at=(0, 0, 10), resolution=(1280, 720)
            )
            save_rgb_image(rgb_data, debug_img_dir, f"pointcloud_camera_frame_res_{res_str}_rgb.png")

        # Save golden data (WARNING: overwrites existing golden data)
        if save_golden_data:
            os.makedirs(self.GOLDEN_DIR, exist_ok=True)
            print(f"WARNING: Saving/overwriting golden data to {self.GOLDEN_DIR}")
            np.save(
                os.path.join(self.GOLDEN_DIR, f"pointcloud_data_world_frame_res_{res_str}.npy"),
                pointcloud_data_world_frame,
            )
            np.save(
                os.path.join(self.GOLDEN_DIR, f"pointcloud_data_camera_frame_res_{res_str}.npy"),
                pointcloud_data_camera_frame,
            )

        # Verify shapes from depth annotator
        self.assertEqual(
            pointcloud_data_world_frame_from_depth.shape,
            expected_shape,
            f"World frame pointcloud from depth: shape {pointcloud_data_world_frame_from_depth.shape} != expected {expected_shape}",
        )
        self.assertEqual(
            pointcloud_data_camera_frame_from_depth.shape,
            expected_shape,
            f"Camera frame pointcloud from depth: shape {pointcloud_data_camera_frame_from_depth.shape} != expected {expected_shape}",
        )

        # Verify shapes from pointcloud annotator
        self.assertEqual(
            pointcloud_data_world_frame.shape,
            expected_shape,
            f"World frame pointcloud from annotator: shape {pointcloud_data_world_frame.shape} != expected {expected_shape}",
        )
        self.assertEqual(
            pointcloud_data_camera_frame.shape,
            expected_shape,
            f"Camera frame pointcloud from annotator: shape {pointcloud_data_camera_frame.shape} != expected {expected_shape}",
        )

        # Load and compare against golden data
        golden_world_frame = np.load(os.path.join(self.GOLDEN_DIR, f"pointcloud_data_world_frame_res_{res_str}.npy"))
        golden_camera_frame = np.load(os.path.join(self.GOLDEN_DIR, f"pointcloud_data_camera_frame_res_{res_str}.npy"))

        print(f"Golden world frame shape: {golden_world_frame.shape}")
        print(f"Golden camera frame shape: {golden_camera_frame.shape}")

        # Sort arrays for comparison (pointcloud order is not guaranteed)
        test_world_sorted = np.sort(pointcloud_data_world_frame, axis=0)
        golden_world_sorted = np.sort(golden_world_frame, axis=0)
        test_camera_sorted = np.sort(pointcloud_data_camera_frame, axis=0)
        golden_camera_sorted = np.sort(golden_camera_frame, axis=0)
        depth_world_sorted = np.sort(pointcloud_data_world_frame_from_depth, axis=0)
        depth_camera_sorted = np.sort(pointcloud_data_camera_frame_from_depth, axis=0)

        # Print comparison stats
        if test_world_sorted.shape == golden_world_sorted.shape:
            diff_world = np.abs(test_world_sorted - golden_world_sorted)
            print(f"World frame diff: mean={diff_world.mean():.6f}, max={diff_world.max():.6f}")
        else:
            print(f"World frame shape mismatch: test={test_world_sorted.shape} vs golden={golden_world_sorted.shape}")

        if test_camera_sorted.shape == golden_camera_sorted.shape:
            diff_camera = np.abs(test_camera_sorted - golden_camera_sorted)
            print(f"Camera frame diff: mean={diff_camera.mean():.6f}, max={diff_camera.max():.6f}")
        else:
            print(
                f"Camera frame shape mismatch: test={test_camera_sorted.shape} vs golden={golden_camera_sorted.shape}"
            )

        # Assertions
        self.assertTrue(
            np.allclose(test_world_sorted, golden_world_sorted, atol=1e-5),
            "World frame (sorted) pointcloud from annotator does not match golden data",
        )
        self.assertTrue(
            np.allclose(depth_world_sorted, golden_world_sorted, atol=1e-5),
            "World frame (sorted) pointcloud from depth does not match golden data",
        )
        self.assertTrue(
            np.allclose(test_camera_sorted, golden_camera_sorted, atol=1e-5),
            "Camera frame (sorted) pointcloud from annotator does not match golden data",
        )
        self.assertTrue(
            np.allclose(depth_camera_sorted, golden_camera_sorted, atol=1e-5),
            "Camera frame (sorted) pointcloud from depth does not match golden data",
        )

    async def test_pointcloud_data_resolution_4_4(self):
        """Test pointcloud data at 4x4 resolution."""
        camera, _, _, _ = await self._create_test_environment()
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()
        camera.initialize()
        await self._compare_pointcloud_data_resolution(
            camera,
            resolution=(4, 4),
            save_golden_data=self.SAVE_GOLDEN_DATA,
            save_test_data=self.SAVE_TEST_DATA,
            save_debug_imgs=self.SAVE_DEBUG_IMGS,
        )

    async def test_pointcloud_data_resolution_64_64(self):
        """Test pointcloud data at 64x64 resolution."""
        camera, _, _, _ = await self._create_test_environment()
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()
        camera.initialize()
        await self._compare_pointcloud_data_resolution(
            camera,
            resolution=(64, 64),
            save_golden_data=self.SAVE_GOLDEN_DATA,
            save_test_data=self.SAVE_TEST_DATA,
            save_debug_imgs=self.SAVE_DEBUG_IMGS,
        )

    async def test_pointcloud_data_resolution_67_137(self):
        """Test pointcloud data at 67x137 non-square resolution."""
        camera, _, _, _ = await self._create_test_environment()
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()
        camera.initialize()
        await self._compare_pointcloud_data_resolution(
            camera,
            resolution=(67, 137),
            save_golden_data=self.SAVE_GOLDEN_DATA,
            save_test_data=self.SAVE_TEST_DATA,
            save_debug_imgs=self.SAVE_DEBUG_IMGS,
        )

    async def test_pointcloud_data_resolution_211_99(self):
        """Test pointcloud data at 211x99 non-square resolution."""
        camera, _, _, _ = await self._create_test_environment()
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()
        camera.initialize()
        await self._compare_pointcloud_data_resolution(
            camera,
            resolution=(211, 99),
            save_golden_data=self.SAVE_GOLDEN_DATA,
            save_test_data=self.SAVE_TEST_DATA,
            save_debug_imgs=self.SAVE_DEBUG_IMGS,
        )
