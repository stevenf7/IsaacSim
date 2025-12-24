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

import asyncio
from typing import Any

import carb
import omni.kit.app
import omni.kit.ui_test as ui_test
import omni.timeline
import omni.usd
from isaacsim.core.experimental.utils import stage as stage_utils
from omni.kit.ui_test import menu_click
from omni.ui.tests.test_base import OmniUiTest


class MenuUITestCase(OmniUiTest):
    """Base test class for Isaac Sim menu UI tests.

    This class provides common setup, teardown, and utility methods for testing
    menu-related UI components including menus and context menus.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import MenuUITestCase
        >>>
        >>> class TestMyMenu(MenuUITestCase):
        ...     async def test_menu(self):
        ...         menu = await self.get_viewport_context_menu()
        ...         self.assertIn("Create", menu)
    """

    async def setUp(self):
        """Set up test environment before each test method.

        Creates a new stage, initializes the timeline interface, and waits for
        stage loading to complete.
        """
        await super().setUp()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = await stage_utils.create_new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        await self.wait_for_stage_loading()

    async def tearDown(self):
        """Clean up test environment after each test method.

        Waits for any pending stage loading operations to complete before
        calling the parent tearDown method.
        """
        await omni.kit.app.get_app().next_update_async()
        await self.wait_for_stage_loading()
        await super().tearDown()

    async def wait_for_stage_loading(self):
        """Wait until the stage has finished loading.

        Polls the stage loading status and waits until all files have been loaded.
        """
        while stage_utils.is_stage_loading():
            await omni.kit.app.get_app().next_update_async()

    async def wait_n_frames(self, n: int = 10):
        """Wait for N app update frames.

        Args:
            n: Number of frames to wait.
        """
        for _ in range(n):
            await omni.kit.app.get_app().next_update_async()

    async def get_viewport_context_menu(self, max_attempts: int = 5) -> dict[str, Any]:
        """Get the viewport context menu with retry and exponential backoff.

        Args:
            max_attempts: Maximum number of retry attempts.

        Returns:
            The context menu dictionary structure.

        Raises:
            Exception: If unable to get context menu after all attempts.
        """
        retry_delay = 0.5

        for attempt in range(max_attempts):
            try:
                viewport_window = ui_test.find("Viewport")
                await viewport_window.right_click()
                return await ui_test.get_context_menu()
            except Exception as e:
                if attempt < max_attempts - 1:
                    carb.log_warn(f"Attempt {attempt + 1} failed to get context menu: {e}. Retrying...")
                    await self.wait_n_frames(1)
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    carb.log_error(f"Failed to get context menu after {max_attempts} attempts: {e}")
                    raise

    async def click_menu_with_retry(self, menu_path: str, delays: list[int] = None):
        """Click a menu item with retry at different delay speeds.

        Some menu items require different timing to be clicked successfully.
        This method tries multiple delay values before giving up.

        Args:
            menu_path: The menu path to click (e.g., "Create/Sensors/Contact Sensor").
            delays: List of delay values to try in milliseconds.
        """
        delays = delays or [5, 50, 100]
        for delay in delays:
            try:
                await menu_click(menu_path, human_delay_speed=delay)
                await self.wait_n_frames(10)
                return
            except AttributeError as e:
                if "NoneType" in str(e) and delay != delays[-1]:
                    continue
                raise

    def count_prims_by_type(self, prim_type: str) -> int:
        """Count the number of prims of a given type on the stage.

        Args:
            prim_type: The USD prim type name to count (e.g., "IsaacContactSensor").

        Returns:
            The number of prims matching the given type.
        """
        count = 0
        for prim in self._stage.Traverse():
            if prim.GetTypeName() == prim_type:
                count += 1
        return count

    async def run_timeline_frames(self, n: int = 50):
        """Play the timeline for N frames then stop.

        Useful for tests that need physics or sensor processing to occur.

        Args:
            n: Number of frames to run the timeline.
        """
        self._timeline.play()
        await self.wait_n_frames(n)
        self._timeline.stop()

    def select_prim(self, prim_path: str):
        """Select a prim by its path.

        Args:
            prim_path: The USD path of the prim to select.
        """
        omni.usd.get_context().get_selection().set_selected_prim_paths([prim_path], False)
