# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import asyncio
import platform
import subprocess

import fastapi

import carb
import carb.settings
import carb.windowing

import omni.ext
import omni.appwindow
import omni.kit.app
import omni.ui as ui


class CreateSplashExtension(omni.ext.IExt):
    """"""

    def __init__(self):
        self._settings = carb.settings.get_settings()

    def _updateLog(self, data=fastapi.Body(...)):
        self._log.text = data

    def on_startup(self, ext_id):
        extension_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)

        self._window = ui.Window("Splash", style={"Window": {"padding": 0}})
        with self._window.frame:
            with ui.VStack(style={"padding": 0}):
                splash_path = f"{extension_path}/data/create_splash_screen@1x.png"
                print("SPLASH PATH", splash_path)
                ui.Image(splash_path, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT, alignment=ui.Alignment.CENTER)

        self.__build_task = asyncio.ensure_future(self.__build_layout())

    async def __build_layout(self):
        async def wait():
            await omni.kit.app.get_app().next_update_async()

        asyncio.ensure_future(wait())

        splash_handle = ui.Workspace.get_window("Splash")
        if splash_handle is None:
            return

        # setup the docking Space
        main_dockspace = ui.Workspace.get_window("DockSpace")

        splash_handle.dock_in(main_dockspace, ui.DockPosition.SAME)
        splash_handle.dock_tab_bar_visible = False

        asyncio.ensure_future(wait())

        # load the control port to enable communication from the make Kit Application
        import omni.services.core.main as controlport

        controlport.register_endpoint("post", "/update-log", self._updateLog)

    def on_shutdown(self):
        self._window = None
