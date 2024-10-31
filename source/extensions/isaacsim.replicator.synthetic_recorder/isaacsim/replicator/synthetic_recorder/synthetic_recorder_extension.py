# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio

import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import MenuHelperExtension

from .synthetic_recorder_window import SyntheticRecorderWindow


class SyntheticRecorderExtension(omni.ext.IExt, MenuHelperExtension):
    WINDOW_NAME = "Synthetic Data Recorder"
    MENU_GROUP = "Replicator"

    def on_startup(self, ext_id):
        # Store the extension id, needed bu the recorder window
        self._ext_id = ext_id
        self._window = None

        # Window will be destroyed when hidden, and recreated when shown (recording will be stopped accordingly)
        ui.Workspace.set_show_window_fn(SyntheticRecorderExtension.WINDOW_NAME, self.show_window)

        # Add the menu item
        self.menu_startup(
            SyntheticRecorderExtension.WINDOW_NAME,
            SyntheticRecorderExtension.WINDOW_NAME,
            SyntheticRecorderExtension.MENU_GROUP,
        )

        # Show the window by default
        ui.Workspace.show_window(SyntheticRecorderExtension.WINDOW_NAME)

    def on_shutdown(self):
        # Destroy the window and remove the menu item on extension shutdown
        self.menu_shutdown()
        if self._window:
            self._window.destroy()
            self._window = None
        ui.Workspace.set_show_window_fn(SyntheticRecorderExtension.WINDOW_NAME, None)

    async def _destroy_window_async(self):
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _visiblity_changed_fn(self, visible):
        # Visualize the state (visible/hidden) of the window in the menu
        self.menu_refresh()
        # Window will be destroyed when hidden, and recreated when shown (recording will be stopped accordingly)
        if not visible:
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, value):
        # Request for the window to be shown; a new window will be created and the visibility changed listener will be set
        if value:
            # Extension id is needed by the window to get the extension path to find the config directory
            self._window = SyntheticRecorderWindow(SyntheticRecorderExtension.WINDOW_NAME, self._ext_id)
            self._window.set_visibility_changed_listener(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False
