# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for the world interface / scene interaction example GUI."""

import omni.kit.app
import omni.kit.test
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.robot_motion.cumotion.examples.world_interface.ui_builder import UIBuilder

from .gui_test_support import wait_until

_OBSTACLE_CUBE_PATH = "/World/obstacle"


def _obstacle_cube_prim_valid() -> bool:
    stage = stage_utils.get_current_stage()
    return stage is not None and stage.GetPrimAtPath(_OBSTACLE_CUBE_PATH).IsValid()


class TestWorldInterfaceGui(omni.kit.test.AsyncTestCase):
    """Test suite for the world interface example GUI."""

    async def setUp(self):
        """Set up the UI builder before each test."""
        await omni.kit.app.get_app().next_update_async()
        self.ui_builder = UIBuilder()
        self.ui_builder.build_ui()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        """Clean up the UI builder after each test."""
        self.ui_builder.cleanup()
        await omni.kit.app.get_app().next_update_async()

    async def test_widgets_built(self):
        """Verify that all expected widgets are created."""
        self.assertIsNotNone(self.ui_builder._load_btn)
        self.assertIsNotNone(self.ui_builder._update_style_combo)

    async def test_load_initializes_world_binding(self):
        """Load completes world binding and places the obstacle cube on the stage."""
        self.ui_builder._load_btn.trigger_click()
        ok = await wait_until(
            lambda: self.ui_builder._scenario._world_binding is not None and _obstacle_cube_prim_valid(),
            timeout_sec=120.0,
        )
        self.assertTrue(ok, "Timed out waiting for world binding and obstacle cube after load")

    async def test_reset_stops_timeline(self):
        """RESET calls timeline.stop() so simulation is stopped after reset."""
        self.ui_builder._load_btn.trigger_click()
        ok = await wait_until(
            lambda: self.ui_builder._scenario._world_binding is not None,
            timeout_sec=120.0,
        )
        self.assertTrue(ok)

        self.ui_builder._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertFalse(
            app_utils.is_stopped(),
            "Timeline should be playing before RESET so we verify stop() runs",
        )

        self.ui_builder._reset_btn.trigger_click()
        ok_stop = await wait_until(app_utils.is_stopped, timeout_sec=10.0)
        self.assertTrue(ok_stop, "Timed out waiting for timeline to stop after RESET")

    async def test_update_style_combo_switches_world_sync_mode(self):
        """Update Style drives world-binding sync mode: ``synchronize``, ``synchronize_transforms``,.

        or ``synchronize_properties`` (via ``set_update_style`` on the scenario).
        """
        ui = self.ui_builder
        labels = ui._update_style_items
        index_model = ui._update_style_combo.model.get_item_value_model()

        for idx in (0, 2, 1):
            index_model.set_value(idx)
            await omni.kit.app.get_app().next_update_async()
            self.assertEqual(ui._scenario._update_style, labels[idx])
            self.assertEqual(index_model.as_int, idx)
