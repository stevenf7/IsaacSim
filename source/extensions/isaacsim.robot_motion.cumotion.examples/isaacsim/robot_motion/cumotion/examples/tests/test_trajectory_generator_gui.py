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

"""Tests for the UR10 trajectory generator example GUI."""

from unittest.mock import patch

import omni.kit.app
import omni.kit.test
from isaacsim.core.experimental.utils import app as app_utils
from isaacsim.robot_motion.cumotion.examples.trajectory_generator.ui_builder import UIBuilder

from .gui_test_support import wait_until


class TestTrajectoryGeneratorGui(omni.kit.test.AsyncTestCase):
    """Test suite for trajectory generator GUI."""

    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        self.ui_builder = UIBuilder()
        self.ui_builder.build_ui()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        self.ui_builder.cleanup()
        await omni.kit.app.get_app().next_update_async()

    async def _load_until_articulation(self) -> None:
        self.ui_builder._load_btn.trigger_click()
        ok = await wait_until(
            lambda: self.ui_builder._scenario._articulation is not None,
            timeout_sec=120.0,
        )
        self.assertTrue(ok, "Timed out waiting for UR10 articulation after load")

    async def test_widgets_built(self):
        self.assertIsNotNone(self.ui_builder._load_btn)
        self.assertIsNotNone(self.ui_builder._reset_btn)
        self.assertIsNotNone(self.ui_builder._cspace_trajectory_btn)
        self.assertIsNotNone(self.ui_builder._taskspace_trajectory_btn)
        self.assertIsNotNone(self.ui_builder._hybrid_trajectory_btn)

    async def test_load_enables_articulation(self):
        await self._load_until_articulation()

    async def test_reset_triggers_scenario_reset(self):
        await self._load_until_articulation()
        with patch.object(self.ui_builder._scenario, "reset") as mock_reset:
            self.ui_builder._reset_btn.trigger_click()
            ok = await wait_until(lambda: mock_reset.call_count >= 1, timeout_sec=30.0)
            self.assertTrue(ok, "Timed out waiting for scenario reset after RESET")

    async def test_run_cspace_button_calls_setup(self):
        await self._load_until_articulation()
        with patch.object(self.ui_builder._scenario, "setup_cspace_trajectory") as mock_setup:
            self.ui_builder._cspace_trajectory_btn.trigger_click_if_a_state()
            mock_setup.assert_called_once()

    async def test_run_taskspace_button_calls_setup(self):
        await self._load_until_articulation()
        with patch.object(self.ui_builder._scenario, "setup_taskspace_trajectory") as mock_setup:
            self.ui_builder._taskspace_trajectory_btn.trigger_click_if_a_state()
            mock_setup.assert_called_once()

    async def test_run_hybrid_button_calls_setup(self):
        await self._load_until_articulation()
        with patch.object(self.ui_builder._scenario, "setup_hybrid_trajectory") as mock_setup:
            self.ui_builder._hybrid_trajectory_btn.trigger_click_if_a_state()
            mock_setup.assert_called_once()

    async def test_stop_button_pauses_timeline(self):
        """STOP (state B click) on a trajectory button should pause the timeline."""
        await self._load_until_articulation()
        with patch.object(self.ui_builder._scenario, "setup_cspace_trajectory"):
            self.ui_builder._cspace_trajectory_btn.trigger_click_if_a_state()
            await omni.kit.app.get_app().next_update_async()
            self.assertTrue(app_utils.is_playing())
            self.assertFalse(self.ui_builder._cspace_trajectory_btn.is_in_a_state())

            self.ui_builder._cspace_trajectory_btn.trigger_click_if_b_state()
            ok_pause = await wait_until(lambda: not app_utils.is_playing(), timeout_sec=10.0)
            self.assertTrue(ok_pause, "Timed out waiting for timeline to pause")
