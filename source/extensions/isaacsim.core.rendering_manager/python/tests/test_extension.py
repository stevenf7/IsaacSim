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

import asyncio

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.test
from isaacsim.core.rendering_manager import RenderingEvent, RenderingManager
from pxr import Usd, UsdGeom, UsdRender

_SETTING_RATE_LIMIT_ENABLED = "/app/runLoops/main/rateLimitEnabled"


class TestExtension(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # ---------------
        self._callback_call = [0, 0]
        self._callback_call_stack = []
        self._rate_limit_enabled = carb.settings.get_settings().get_as_bool(_SETTING_RATE_LIMIT_ENABLED)
        await stage_utils.create_new_stage_async()
        # ---------------

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        # ------------------
        carb.settings.get_settings().set_bool(_SETTING_RATE_LIMIT_ENABLED, self._rate_limit_enabled)
        stage_utils.close_stage()
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------

    def _callback(self, *args, **kwargs):
        self._callback_call[0] += 1
        self._callback_call_stack.append(self._callback_call[:])

    # --------------------------------------------------------------------

    async def test_render(self):
        for _ in range(10):
            await RenderingManager.render_async()

    async def test_dt(self):
        # get default vale
        for enabled in [False, True]:
            carb.settings.get_settings().set_bool(_SETTING_RATE_LIMIT_ENABLED, enabled)
            expected_dt = 1 / 120 if enabled else 1 / 60
            current_dt = RenderingManager.get_dt()
            self.assertAlmostEqual(
                expected_dt,
                current_dt,
                msg=f"Expected {1 / expected_dt} Hz. Got {1 / current_dt} Hz (rateLimitEnabled: {enabled})",
            )
        # set custom value
        for i, enabled in enumerate([False, True]):
            custom_dt = 1 / (99 + 10 * i)
            RenderingManager.set_dt(custom_dt)
            current_dt = RenderingManager.get_dt()
            self.assertAlmostEqual(
                custom_dt,
                current_dt,
                msg=f"Expected {1 / custom_dt} Hz. Got {1 / current_dt} Hz (rateLimitEnabled: {enabled})",
            )

    async def test_00_wait_for_viewport(self):  # 00 ensures that this test is run first
        # test cases
        # - no frames are waited for
        result = await RenderingManager.wait_for_viewport_async(max_frames=0)
        self.assertTupleEqual(result, (False, 0), f"Viewport should not be ready if no frames are waited for")
        # - 1 frame is waited for (without sleep time)
        result = await RenderingManager.wait_for_viewport_async(max_frames=1, sleep_time=0.0)
        self.assertTupleEqual(result, (False, 1), f"Viewport should not be ready after 1 frame (without sleep time)")
        # - wait for the default number of frames (with default sleep time)
        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")

    async def test_callback(self):
        def callback(*args, **kwargs):
            self._callback_call[1] += 1
            self._callback_call_stack.append(self._callback_call[:])

        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        self.assertListEqual(self._callback_call, [0, 0])
        await asyncio.sleep(0.5)  # let previous (unregistered) events pass, since we are not waiting idly
        # test cases
        # - register local function callback and step rendering
        local_function_callback_id = RenderingManager.register_callback(RenderingEvent.NEW_FRAME, callback=callback)
        await RenderingManager.render_async()
        self.assertEqual(local_function_callback_id, 0)
        # - register class method callback and step rendering
        class_method_callback_id = RenderingManager.register_callback(RenderingEvent.NEW_FRAME, callback=self._callback)
        await RenderingManager.render_async()
        self.assertEqual(class_method_callback_id, 1)
        # - step rendering
        await RenderingManager.render_async()
        # - deregister local function callback
        RenderingManager.deregister_callback(local_function_callback_id)
        await RenderingManager.render_async()
        # - deregister class method callback
        RenderingManager.deregister_callback(class_method_callback_id)
        await RenderingManager.render_async()
        # - register a new class method callback and step rendering
        class_method_callback_id = RenderingManager.register_callback(RenderingEvent.NEW_FRAME, callback=self._callback)
        await RenderingManager.render_async()
        self.assertEqual(class_method_callback_id, 2)
        # - deregister all callbacks
        RenderingManager.deregister_all_callbacks()
        await RenderingManager.render_async()
        # - deregister the already deregistered callback and check for warning
        RenderingManager.deregister_callback(local_function_callback_id)
        RenderingManager.deregister_callback(class_method_callback_id)
        await RenderingManager.render_async()
        # check the callback call stack
        await asyncio.sleep(0.5)  # wait for triggered events to occur, since we are not waiting idly
        self.assertListEqual(self._callback_call_stack, [[0, 1], [0, 2], [1, 2], [1, 3], [2, 3], [3, 3], [4, 3]])

    async def test_set_camera(self):
        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        # test conditions
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        sources = [
            None,
            viewport_api,
            viewport_api.render_product_path,
            "Viewport",
            stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path),
            UsdRender.Product(stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path)),
        ]
        cameras = [
            "/OmniverseKit_Persp",
            "/OmniverseKit_Top",
            "/OmniverseKit_Front",
            "/OmniverseKit_Right",
            stage_utils.define_prim("/CustomCamera", "Camera"),
        ]
        for source in sources:
            for camera in cameras:
                RenderingManager.set_camera(camera, render_product_or_viewport=source)
        # exception
        with self.assertRaisesRegex(ValueError, "not a valid USD Camera prim"):
            RenderingManager.set_camera("/Invalid/Source")

    async def test_get_camera(self):
        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        # test conditions
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        sources = [
            None,
            viewport_api,
            viewport_api.render_product_path,
            "Viewport",
            stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path),
            UsdRender.Product(stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path)),
        ]
        for source in sources:
            camera = RenderingManager.get_camera(source)
            self.assertIsInstance(camera, UsdGeom.Camera)

    async def test_get_viewport_and_render_product(self):
        def _check_viewport(source):
            self.assertIn("ViewportAPI", RenderingManager.get_viewport_api(source).__class__.__name__)

        def _check_render_product(source):
            self.assertIsInstance(RenderingManager.get_render_product(source), UsdRender.Product)

        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        # test cases
        # - unspecified source
        _check_viewport(None)
        _check_render_product(None)
        # - viewport API
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        _check_viewport(viewport_api)
        _check_render_product(viewport_api)
        # - str
        # -- render product path
        render_product_path = viewport_api.render_product_path
        self.assertIsInstance(render_product_path, str)
        self.assertIsNone(RenderingManager.get_viewport_api(render_product_path))
        _check_render_product(render_product_path)
        # -- viewport name
        _check_viewport("Viewport")
        _check_render_product("Viewport")
        # - USD prim
        # -- render product
        render_product_prim = stage_utils.get_current_stage().GetPrimAtPath(render_product_path)
        self.assertIsInstance(render_product_prim, Usd.Prim)
        self.assertIsNone(RenderingManager.get_viewport_api(render_product_prim))
        _check_render_product(render_product_prim)
        _check_render_product(UsdRender.Product(render_product_prim))
        # - unknown source
        self.assertIsNone(RenderingManager.get_viewport_api("/Invalid/Source"))
        self.assertIsNone(RenderingManager.get_render_product("/Invalid/Source"))

    async def test_get_resolution(self):
        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        # test cases
        expected_resolution = (1280, 720)
        # - unspecified source
        resolution = RenderingManager.get_resolution()
        self.assertTupleEqual(resolution, expected_resolution)
        # - viewport API
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        resolution = RenderingManager.get_resolution(viewport_api)
        self.assertTupleEqual(resolution, expected_resolution)
        # - str
        # -- render product path
        render_product_path = viewport_api.render_product_path
        self.assertIsInstance(render_product_path, str)
        resolution = RenderingManager.get_resolution(render_product_path)
        self.assertTupleEqual(resolution, expected_resolution)
        # -- viewport name
        resolution = RenderingManager.get_resolution("Viewport")
        self.assertTupleEqual(resolution, expected_resolution)
        # - USD prim
        # -- render product
        render_product_prim = stage_utils.get_current_stage().GetPrimAtPath(render_product_path)
        self.assertIsInstance(render_product_prim, Usd.Prim)
        resolution = RenderingManager.get_resolution(render_product_prim)
        self.assertTupleEqual(resolution, expected_resolution)
        resolution = RenderingManager.get_resolution(UsdRender.Product(render_product_prim))
        self.assertTupleEqual(resolution, expected_resolution)
        # exception
        with self.assertRaisesRegex(ValueError, "Unable to get resolution: unknown"):
            resolution = RenderingManager.get_resolution("/Invalid/Source")

    async def test_set_resolution(self):
        status, frames = await RenderingManager.wait_for_viewport_async()
        self.assertTrue(status, f"Viewport not ready after {frames} frames")
        # test conditions
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        sources = [
            None,
            viewport_api,
            viewport_api.render_product_path,
            "Viewport",
            stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path),
            UsdRender.Product(stage_utils.get_current_stage().GetPrimAtPath(viewport_api.render_product_path)),
        ]
        resolutions = [(640, 480), (1280, 720)]
        # test cases
        for source in sources:
            for resolution in resolutions:
                RenderingManager.set_resolution(resolution, render_product_or_viewport=source)
                self.assertTupleEqual(
                    RenderingManager.get_resolution(source),
                    resolution,
                    (
                        f"Source: {source} (type: {type(source)},"
                        f" viewport: {RenderingManager.get_viewport_api(source)},"
                        f" render product: {RenderingManager.get_render_product(source)})"
                    ),
                )
        # exception
        with self.assertRaisesRegex(ValueError, "Unable to set resolution: unknown"):
            RenderingManager.set_resolution(resolution, render_product_or_viewport="/Invalid/Source")

    async def test_viewport_windows(self):
        # test cases
        # - default window
        windows = RenderingManager.get_viewport_windows()
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].title, "Viewport")
        # - create viewport windows
        for i, camera in enumerate(
            [
                None,
                "/OmniverseKit_Persp",
                "/OmniverseKit_Top",
                "/OmniverseKit_Front",
                "/OmniverseKit_Right",
                stage_utils.define_prim("/CustomCamera", "Camera"),
            ]
        ):
            if camera is None:
                window = RenderingManager.create_viewport_window(title="Custom Title")
            else:
                window = RenderingManager.create_viewport_window(camera=camera)
            self.assertEqual(window.title, f"Viewport {i + 1}" if camera is not None else "Custom Title")
            self.assertEqual(
                window.viewport_api.camera_path,
                prim_utils.get_prim_path(camera) if camera is not None else "/OmniverseKit_Persp",
            )
        # - get viewport windows
        # -- all
        windows = RenderingManager.get_viewport_windows()
        self.assertEqual(len(windows), 7)
        self.assertListEqual(
            sorted([window.title for window in windows]),
            [
                "Custom Title",
                "Viewport",
                "Viewport 2",
                "Viewport 3",
                "Viewport 4",
                "Viewport 5",
                "Viewport 6",
            ],
        )
        # -- using regex
        windows = RenderingManager.get_viewport_windows(include=[".*[2-5]", "Custom Title"], exclude=["Viewport 4"])
        self.assertListEqual(
            [window.title for window in windows], ["Custom Title", "Viewport 2", "Viewport 3", "Viewport 5"]
        )
        # - destroy windows
        # -- using regex
        destroyed_window_titles = RenderingManager.destroy_viewport_windows(
            include=["Viewport", "Custom.*", "Viewport 5"], exclude=["Viewport 5"]
        )
        self.assertListEqual(destroyed_window_titles, ["Viewport", "Custom Title"])
        self.assertListEqual(
            [window.title for window in RenderingManager.get_viewport_windows()],
            ["Viewport 2", "Viewport 3", "Viewport 4", "Viewport 5", "Viewport 6"],
        )
        # -- all
        destroyed_window_titles = RenderingManager.destroy_viewport_windows()
        self.assertEqual(len(RenderingManager.get_viewport_windows()), 0)
