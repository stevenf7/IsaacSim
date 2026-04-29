# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for the Teleop UI window."""

import os
import tempfile

import omni.kit.app
import omni.kit.ui_test as ui_test
import omni.ui as ui
import omni.usd
from isaacsim.replicator.teleop.ui.teleop_ui_extension import TeleopUIExtension
from isaacsim.test.utils.menu_utils import menu_click_with_retry
from omni.ui.tests.test_base import OmniUiTest

WINDOW_TITLE = TeleopUIExtension.WINDOW_NAME
MENU_PATH = f"{TeleopUIExtension.MENU_GROUP}/{TeleopUIExtension.WINDOW_NAME}"


class TestTeleopUIWindow(OmniUiTest):
    """Test the Teleop UI window lifecycle."""

    async def setUp(self) -> None:
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self) -> None:
        omni.usd.get_context().close_stage()
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

    async def test_window_open_close(self) -> None:
        """Window can be opened via the menu and closed without errors."""
        window = None
        with tempfile.TemporaryDirectory(prefix="teleop_ui_window_") as tmp_dir:
            try:
                await menu_click_with_retry(MENU_PATH, window_name=WINDOW_TITLE)
                for _ in range(5):
                    await omni.kit.app.get_app().next_update_async()

                window = ui.Workspace.get_window(WINDOW_TITLE)
                self.assertIsNotNone(window, "Teleop window should exist after opening via the menu")
                if hasattr(window, "_last_profile_path"):
                    window._last_profile_path = os.path.join(tmp_dir, "last_profile.yaml")

                widget = ui_test.find(WINDOW_TITLE)
                self.assertIsNotNone(widget, "Teleop window widget should be findable after opening")

                await menu_click_with_retry(MENU_PATH)
                window = None
                for _ in range(5):
                    await omni.kit.app.get_app().next_update_async()
            finally:
                if window is not None and hasattr(window, "_last_profile_path"):
                    window._last_profile_path = os.path.join(tmp_dir, "last_profile.yaml")
                    window.destroy()
