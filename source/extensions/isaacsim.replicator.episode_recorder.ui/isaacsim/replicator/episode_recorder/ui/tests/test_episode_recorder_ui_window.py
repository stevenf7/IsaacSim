# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Episode Recorder UI window lifecycle."""

import omni.kit.app
import omni.kit.ui_test as ui_test
import omni.ui as ui
import omni.usd
from isaacsim.replicator.episode_recorder.ui.episode_recorder_extension import EpisodeRecorderUIExtension
from isaacsim.test.utils.menu_utils import menu_click_with_retry
from omni.ui.tests.test_base import OmniUiTest

WINDOW_TITLE = EpisodeRecorderUIExtension.WINDOW_NAME
MENU_PATH = f"{EpisodeRecorderUIExtension.MENU_GROUP}/{EpisodeRecorderUIExtension.WINDOW_NAME}"


class TestEpisodeRecorderUIWindow(OmniUiTest):
    """Test the Episode Recorder UI window lifecycle."""

    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        omni.usd.get_context().close_stage()
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

    async def test_window_open_close(self):
        """Window can be opened via the menu and closed without errors."""
        window = None
        try:
            await menu_click_with_retry(MENU_PATH, window_name=WINDOW_TITLE)
            for _ in range(5):
                await omni.kit.app.get_app().next_update_async()

            window = ui.Workspace.get_window(WINDOW_TITLE)
            self.assertIsNotNone(window, "Episode Recorder window should exist after opening via the menu")

            widget = ui_test.find(WINDOW_TITLE)
            self.assertIsNotNone(widget, "Episode Recorder window widget should be findable after opening")

            await menu_click_with_retry(MENU_PATH)
            window = None
            for _ in range(5):
                await omni.kit.app.get_app().next_update_async()
        finally:
            if window is not None:
                window.destroy()
