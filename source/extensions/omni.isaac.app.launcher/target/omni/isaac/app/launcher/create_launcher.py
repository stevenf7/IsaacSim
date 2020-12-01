# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import asyncio
import sys
import os
import platform
import subprocess

import carb
import carb.settings
import carb.tokens
import carb.windowing

import omni.ext

import omni.kit.app

from .launcher_window import LauncherWindow
from typing import List, Dict, Any


class CreateLauncherExtension(omni.ext.IExt):
    """"""

    def __init__(self):
        self._settings = carb.settings.get_settings()

    def on_startup(self, ext_id: str):
        # if we are in auto_launch mode and the extensions is also setup we start immediatly the default app
        # this avoid going to the App Window
        user_auto_launch = self._settings.get("/persistent/ext/omni.isaac.launcher/auto_launch")
        # first startup
        if user_auto_launch is None:
            self._settings.set("/persistent/ext/omni.isaac.launcher/auto_launch", True)

        # if user_auto_launch is still None ( not set ) then we are auto-starting
        if self._settings.get("/app/auto_launch") and (user_auto_launch or user_auto_launch is None):
            default_app = self._settings.get("/persistent/ext/omni.isaac.launcher/default_app")
            if not default_app:
                default_app = self._settings.get("/ext/omni.isaac.launcher/default_app")

            self._launch_app(default_app)
            os._exit(os.F_OK)

        # We only load the UI App if we have not auto-started
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        if not ext_manager.is_extension_enabled("omni.kit.uiapp"):
            ext_manager.set_extension_enabled_immediate("omni.kit.uiapp", True)
            ext_manager.set_extension_enabled_immediate("omni.kit.window.title", True)

        from omni.kit.window.title import get_main_window_title

        extension_path = ext_manager.get_extension_path(ext_id)

        # setup title
        window_title = get_main_window_title()
        app_version = self._settings.get("/app/version")
        app_folder = self._settings.get_as_string("/app/folder")
        if not app_folder:
            app_folder = carb.tokens.get_tokens_interface().resolve("${app}")
        if not app_version:
            app_version = open(f"{app_folder}/../VERSION").read()

        if app_version:
            app_version, _ = app_version.split("+")
            window_title.set_app_version(app_version)

        self._launcher_window = LauncherWindow(extension_path)
        self.__build_task = asyncio.ensure_future(self.__build_layout())

    def _launch_app(self, app_id: str):
        """ show the omniverse ui documentation as an external Application """
        app_folder = carb.tokens.get_tokens_interface().resolve("${app}")
        launch_args = [f"{app_folder}/../{app_id}.bat"]

        kwargs: Dict[str, Any] = {"close_fds": False}
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(launch_args, **kwargs)

    async def __build_layout(self):
        await omni.kit.app.get_app().next_update_async()
        import omni.ui as ui

        launcher_handle = ui.Workspace.get_window("Launcher")
        if launcher_handle is None:
            return

        # setup the docking Space
        main_dockspace = ui.Workspace.get_window("DockSpace")

        launcher_handle.dock_in(main_dockspace, ui.DockPosition.SAME)
        launcher_handle.dock_tab_bar_visible = False

        await omni.kit.app.get_app().next_update_async()

    def on_shutdown(self):
        self._launcher_window.destroy()
        self._launcher_window = None
