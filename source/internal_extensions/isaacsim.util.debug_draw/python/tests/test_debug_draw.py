# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Verifies debug draw point, line, spline, empty-input, and validation-error behavior, including count tracking and clearing. Captures rendered debug geometry and compares it against a golden image."""

import io
import os
import random
import tempfile
from unittest.mock import patch

import omni.kit.app
import omni.kit.test
import omni.usd
from isaacsim.test.utils.image_capture import capture_rgb_data_async
from isaacsim.test.utils.image_comparison import compare_images_within_tolerances
from isaacsim.test.utils.image_io import save_rgb_image
from isaacsim.util.debug_draw import _debug_draw


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestDebugDraw(omni.kit.test.AsyncTestCase):
    """Async tests for debug draw API behavior and rendering."""

    # Before running each test
    async def setUp(self) -> None:
        """Set up the test by acquiring the debug draw interface."""
        self._draw = _debug_draw.acquire_debug_draw_interface()
        self.test_dir = tempfile.mkdtemp()

    # After running each test
    async def tearDown(self) -> None:
        """Tear down the test by waiting for the next update."""
        await omni.kit.app.get_app().next_update_async()
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_draw_points(self) -> None:
        """Test drawing points with various colors and sizes."""
        N = 10000
        point_list_1 = [
            (random.uniform(-1000, 1000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_2 = [
            (random.uniform(-1000, 1000), random.uniform(1000, 3000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_3 = [
            (random.uniform(-1000, 1000), random.uniform(-3000, -1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 50) for _ in range(N)]
        self._draw.draw_points(point_list_1, [(1, 0, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_2, [(0, 1, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_3, colors, sizes)
        self.assertEqual(self._draw.get_num_points(), 3 * N)
        self._draw.clear_points()
        self.assertEqual(self._draw.get_num_points(), 0)

    async def test_draw_points_error_handling(self) -> None:
        """Test error handling for mismatched list sizes in draw_points."""
        # These should not crash, and ideally should not add points
        # Case 1: fewer colors than points
        self._draw.draw_points([(0, 0, 0), (1, 1, 1)], [(1, 0, 0, 1)], [10, 10])
        # Case 2: fewer sizes than points
        self._draw.draw_points([(0, 0, 0), (1, 1, 1)], [(1, 0, 0, 1), (0, 1, 0, 1)], [10])

        # If validation works, we expect 0 points. If it fails (current behavior),
        # it might crash or produce undefined behavior.
        # After we fix the C++ code, this assertion should pass.
        self.assertEqual(self._draw.get_num_points(), 0)

    async def test_draw_lines(self) -> None:
        """Test drawing lines with various colors and widths."""
        N = 10000
        point_list_1 = [
            (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        point_list_2 = [
            (random.uniform(1000, 3000), random.uniform(-1000, 1000), random.uniform(-1000, 1000)) for _ in range(N)
        ]
        colors = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 25) for _ in range(N)]
        self._draw.draw_lines(point_list_1, point_list_2, colors, sizes)
        self.assertEqual(self._draw.get_num_lines(), N)
        self._draw.clear_lines()
        self.assertEqual(self._draw.get_num_lines(), 0)

    async def test_draw_spline(self) -> None:
        """Test drawing spline curves with control points."""
        point_list_1 = [
            (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
        ]
        self._draw.draw_lines_spline(point_list_1, (1, 1, 1, 1), 10, False)
        point_list_2 = [
            (random.uniform(-300, -100), random.uniform(-100, 100), random.uniform(-100, 100)) for _ in range(10)
        ]
        self._draw.draw_lines_spline(point_list_2, (1, 1, 1, 1), 5, True)

        self.assertGreater(self._draw.get_num_lines(), 0)
        self._draw.clear_lines()
        self.assertEqual(self._draw.get_num_lines(), 0)

    async def test_empty_input(self) -> None:
        """Test drawing with empty lists."""
        self._draw.draw_points([], [], [])
        self.assertEqual(self._draw.get_num_points(), 0)

        self._draw.draw_lines([], [], [], [])
        self.assertEqual(self._draw.get_num_lines(), 0)

    async def test_visual_regression(self) -> None:
        """Test visual regression by capturing an image and comparing to golden."""
        # Setup a new stage
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

        # Draw some deterministic points and lines
        # Points: Red, Green, Blue at visible locations
        import random

        random.seed(1234)
        N = 10000
        point_list_1 = [
            (
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
            )
            for _ in range(N)
        ]
        point_list_2 = [
            (
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(1000, 3000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
            )
            for _ in range(N)
        ]
        point_list_3 = [
            (
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(-3000, -1000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
            )
            for _ in range(N)
        ]
        colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.5, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 50) for _ in range(N)]
        self._draw.draw_points(point_list_1, [(1, 0, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_2, [(0, 1, 0, 1)] * N, [10] * N)
        self._draw.draw_points(point_list_3, colors, sizes)

        # Lines: White line from origin to (50, 50, 50)
        point_list_1 = [
            (
                random.uniform(1000, 3000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
            )
            for _ in range(N)
        ]
        point_list_2 = [
            (
                random.uniform(1000, 3000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
                random.uniform(-1000, 1000) / 1000.0,
            )
            for _ in range(N)
        ]
        colors = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1), 1) for _ in range(N)]
        sizes = [random.randint(1, 25) for _ in range(N)]
        self._draw.draw_lines(point_list_1, point_list_2, colors, sizes)

        # Wait for updates
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()

        # Capture RGB data
        rgb_resolution = (640, 480)
        rgb_data = await capture_rgb_data_async(resolution=rgb_resolution)

        self.assertIsNotNone(rgb_data)
        self.assertEqual(rgb_data.shape, (rgb_resolution[1], rgb_resolution[0], 4))

        # Define golden image path
        # Assuming standard extension structure, we put golden images in data/golden_img
        # We need to find the extension path.
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        # The extension id is usually the folder name in source/internal_extensions
        ext_id = ext_manager.get_enabled_extension_id("isaacsim.util.debug_draw")
        if not ext_id:
            # Fallback if extension name is different or not found (e.g. running in test harness)
            # For now, we can try to construct path relative to this file
            # Go up 3 levels: tests -> python -> isaacsim.util.debug_draw
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            golden_dir = os.path.join(base_dir, "data", "golden_img")
        else:
            ext_path = ext_manager.get_extension_path(ext_id)
            golden_dir = os.path.join(ext_path, "data", "golden_img")

        golden_image_path = os.path.join(golden_dir, "debug_draw_test.png")

        # Set this to True to save the captured image to the golden directory instead of temp dir
        save_to_golden = False

        # Save captured image
        if save_to_golden:
            captured_image_path = os.path.join(golden_dir, "new_debug_draw_test.png")
            save_rgb_image(rgb_data, golden_dir, "new_debug_draw_test.png")
        else:
            captured_image_path = os.path.join(self.test_dir, "debug_draw_test.png")
            save_rgb_image(rgb_data, self.test_dir, "debug_draw_test.png")

        # Compare
        if not os.path.exists(golden_image_path):
            # Fail but print where the new image is so it can be added
            self.fail(f"Golden image not found at {golden_image_path}. Saved captured image to {captured_image_path}")

        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            res = compare_images_within_tolerances(
                golden_file_path=golden_image_path,
                test_file_path=captured_image_path,
                allclose_rtol=0.0,
                allclose_atol=255,  # Loose tolerance as we might not have exact rendering
                mean_tolerance=5.0,
                print_all_stats=True,
            )

        is_similar = bool(res["passed"])
        captured_stdout = stdout_capture.getvalue()
        self.assertTrue(
            is_similar,
            f"Captured image does not match golden.\nstdout: {captured_stdout}\nCaptured: {captured_image_path}",
        )
