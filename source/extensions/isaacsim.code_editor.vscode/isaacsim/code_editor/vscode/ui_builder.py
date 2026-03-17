# SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""UI builder for Visual Studio Code integration extension."""

from __future__ import annotations

import os
import subprocess
import sys
import weakref

import carb


class UIBuilder:
    """Manage the VS Code menu item and launcher.

    Args:
        menu_name: Name of the menu where the item will be added.
        menu_item_name: Display name for the menu item.
        host: Host address for the Python server.
        port: Port number for the Python server.
    """

    def __init__(self, menu_name: str, menu_item_name: str, host: str, port: int) -> None:
        self._menu_items: list = []
        self._host = host
        self._port = port
        self._menu_name = menu_name
        self._menu_item_name = menu_item_name

        app_folder = carb.settings.get_settings().get_as_string("/app/folder")
        if not app_folder:
            app_folder = carb.tokens.get_tokens_interface().resolve("${app}")
        self._app_folder = os.path.normpath(os.path.join(app_folder, os.pardir))

    def startup(self) -> None:
        """Create the menu item for launching VS Code."""
        try:
            from omni.kit.menu.utils import MenuItemDescription, add_menu_items

            self._menu_items = [
                MenuItemDescription(
                    name=self._menu_item_name,
                    onclick_fn=lambda p=weakref.proxy(self): p._launch(),
                )
            ]
            add_menu_items(self._menu_items, self._menu_name)
        except ImportError:
            pass

    def shutdown(self) -> None:
        """Remove the menu item."""
        try:
            from omni.kit.menu.utils import remove_menu_items

            remove_menu_items(self._menu_items, "Window")
        except ImportError:
            pass
        self._menu_items = []

    def _launch(self, *args: object, **kwargs: object) -> None:
        """Launch a new VS Code window pointed at the application directory.

        Args:
            *args: Variable length argument list (unused).
            **kwargs: Additional keyword arguments (unused).
        """
        command = ["code", "-n", self._app_folder]
        carb.log_info(f"Launching VS Code: {command}")
        result = subprocess.run(command, shell=(sys.platform == "win32"), close_fds=True)
        # check process execution
        notification = f"Serving at {self._host}:{self._port}"
        if result.returncode:
            notification += f"\n\nUnable to launch VS Code (error code: {result.returncode})"
            if result.returncode in (1, 127):
                notification += ".\nMake sure VS Code is installed and accessible on the system via the command 'code'"
            carb.log_warn(notification)

        try:
            import omni.kit.notification_manager as notification_manager
        except ImportError:
            pass
        else:
            if result.returncode:
                status = notification_manager.NotificationStatus.WARNING
            else:
                status = notification_manager.NotificationStatus.INFO
            notification_manager.post_notification(
                notification,
                hide_after_timeout=not result.returncode,
                duration=3,
                status=status,
                button_infos=[notification_manager.NotificationButtonInfo("OK", on_complete=None)],
            )
