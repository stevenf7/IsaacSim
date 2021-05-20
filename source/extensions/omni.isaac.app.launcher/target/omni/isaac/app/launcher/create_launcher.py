# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import asyncio

import carb
import carb.settings
import carb.tokens
import carb.windowing

import omni.ext

import omni.kit.app

from .launcher_window import LauncherWindow
from .settings import AUTO_LAUNCH_SETTING, DEFAULT_APP_SETTING, PERSISTENT_LAUNCHER_SETTING, SHOW_CONSOLE_SETTING

from .launch_app import launch_app


class CreateLauncherExtension(omni.ext.IExt):
    """"""

    def __init__(self):
        self._settings = carb.settings.get_settings()
        self._launcher_window = None

    def on_startup(self, ext_id: str):
        # Initialize settings
        default_app = self._settings.get(DEFAULT_APP_SETTING)
        user_auto_launch = self._settings.get(AUTO_LAUNCH_SETTING)
        close_on_launch = not self._settings.get(PERSISTENT_LAUNCHER_SETTING)
        user_show_console = self._settings.get(SHOW_CONSOLE_SETTING)

        if default_app is None:
            default_app = self._settings.get("/ext/omni.isaac.launcher/default_app")
            self._settings.set(DEFAULT_APP_SETTING, default_app)
        if default_app is None:
            self._settings.set(DEFAULT_APP_SETTING, "isaac-sim")

        if user_auto_launch is None:
            user_auto_launch = self._settings.get("/ext/omni.isaac.launcher/auto_launch")
            self._settings.set(AUTO_LAUNCH_SETTING, user_auto_launch)
        if user_auto_launch is None:
            self._settings.set(AUTO_LAUNCH_SETTING, False)

        if close_on_launch is None:
            close_on_launch = not self._settings.get("/ext/omni.isaac.launcher/persistent_launcher")
            self._settings.set(PERSISTENT_LAUNCHER_SETTING, not close_on_launch)
        if close_on_launch is None:
            self._settings.set(PERSISTENT_LAUNCHER_SETTING, False)

        user_show_console = self._settings.get("/ext/omni.isaac.launcher/show_console")
        self._settings.set(SHOW_CONSOLE_SETTING, user_show_console)
        if user_show_console is None:
            self._settings.set(SHOW_CONSOLE_SETTING, True)

        # Auto-starting default app
        if user_auto_launch:
            default_app = self._settings.get(DEFAULT_APP_SETTING)
            if not default_app:
                default_app = self._settings.get("/ext/omni.isaac.launcher/default_app")

            launch_app(app_id=default_app, app_become_new_default=False, close_on_launch=close_on_launch)
            if close_on_launch:
                return

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
            app_launch_folder = os.path.normpath(os.path.join(app_folder, os.pardir))
            app_version = open(f"{app_launch_folder}/VERSION").read()

        if app_version:
            app_version, _ = app_version.split("+")
            app_version, _ = app_version.split("-")
            window_title.set_app_version(app_version)

        self._launcher_window = LauncherWindow(extension_path)
        self.__build_task = asyncio.ensure_future(self.__build_layout())

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
        if self._launcher_window:
            self._launcher_window.destroy()
            self._launcher_window = None
