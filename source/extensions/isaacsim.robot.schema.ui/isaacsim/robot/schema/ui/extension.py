# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Extension entry point for the robot schema UI."""

__all__ = ["SchemaUIExtension"]

import asyncio

import carb.settings
import omni.ext
import omni.kit.app
import omni.ui as ui
from omni.kit.menu.utils import MenuHelperExtension
from omni.kit.viewport.registry import RegisterScene

from .robot_hierarchy_window import RobotHierarchyWindow
from .scene import ConnectionScene


class SchemaUIExtension(omni.ext.IExt, MenuHelperExtension):
    """Extension providing the Robot Hierarchy window and viewport visualization.

    Registers a dockable window showing the robot joint hierarchy and
    a viewport scene for visualizing joint connections.
    """

    WINDOW_NAME = "Robot Hierarchy"
    MENU_GROUP = "Window"

    def on_startup(self, extension_id: str) -> None:
        """Handle extension startup.

        Registers the window, menu entry, and viewport scene.

        Args:
            extension_id: The extension identifier.
        """
        self._window: RobotHierarchyWindow | None = None
        self._viewport_scene: ConnectionScene | None = None
        ui.Workspace.set_show_window_fn(SchemaUIExtension.WINDOW_NAME, self.show_window)
        ui.Workspace.show_window(SchemaUIExtension.WINDOW_NAME)
        self.menu_startup(
            SchemaUIExtension.WINDOW_NAME,
            SchemaUIExtension.WINDOW_NAME,
            SchemaUIExtension.MENU_GROUP,
        )
        original_joints_vusual = carb.settings.get_settings().get("/persistent/physics/visualizationDisplayJoints")
        carb.settings.get_settings().set("/persistent/physics/visualizationDisplayJoints", True)
        self._viewport_scene = RegisterScene(ConnectionScene, extension_id)
        carb.settings.get_settings().set("/persistent/physics/visualizationDisplayJoints", original_joints_vusual)

    def on_shutdown(self) -> None:
        """Handle extension shutdown.

        Cleans up the window, menu entry, and viewport scene.
        """
        self.menu_shutdown()
        if self._window:
            self._window.destroy()
            self._window = None

        ui.Workspace.set_show_window_fn(SchemaUIExtension.WINDOW_NAME, None)
        if self._viewport_scene:
            self._viewport_scene.destroy()
            self._viewport_scene = None

    async def _destroy_window_async(self) -> None:
        """Destroy the window asynchronously.

        Waits one frame to handle window movement deferral.
        """
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _on_visibility_changed(self, visible: bool) -> None:
        """Handle window visibility changes.

        Args:
            visible: True if visible, False if hidden.
        """
        self.menu_refresh()
        if not visible:
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, value: bool) -> None:
        """Show or hide the Robot Hierarchy window.

        Args:
            value: True to show, False to hide.

        Example:

        .. code-block:: python

            extension.show_window(True)
        """
        if value:
            window = RobotHierarchyWindow()
            window.set_visibility_changed_listener(self._on_visibility_changed)
            self._window = window
        elif self._window:
            self._window.visible = False
