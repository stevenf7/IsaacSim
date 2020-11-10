# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import omni.ext
import omni.ui as ui
import carb.settings
import omni.kit.commands

import omni.kit.app


class CreateSetupExtension(omni.ext.IExt):
    """Create Final Configuration"""

    def on_startup(self):
        """ setup the window layout, menu, final configuration of the extensions etc """
        self._settings = carb.settings.get_settings()

        # there is some issue with DLSS and alpha/bg color, when it is fix we can bring that back
        if False:
            # settings up default Color for Background
            self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/enabled", True)
            self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/backgroundDefaultColor", (0.2, 0.2, 0.2))
            self.__background_color = asyncio.ensure_future(self.__bg_color())

        self.__setup_window_task = asyncio.ensure_future(self.__dock_windows())

        self.__setup_property_window = asyncio.ensure_future(self.__propert_window())

    async def __bg_color(self):
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        self._settings.set(
            "/rtx/post/backgroundZeroAlpha/enabled", self._settings.get("/rtx/post/backgroundZeroAlpha/enabled")
        )
        self._settings.set(
            "/rtx/post/backgroundZeroAlpha/backgroundDefaultColor",
            self._settings.get("/rtx/post/backgroundZeroAlpha/backgroundDefaultColor"),
        )

    async def __dock_windows(self):
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        stage = ui.Workspace.get_window("Stage")
        stage.dock_order = 0
        stage.focus()

        # # setup the docking Space
        content_old = ui.Workspace.get_window("Content")
        if content_old:
            content_old.dock_order = 1

        content = ui.Workspace.get_window("Content 2.0")

        # dock with the console
        console = ui.Workspace.get_window("Console")
        if console:
            content.dock_in(console, ui.DockPosition.SAME)
        else:
            print("failed to get console")

        await omni.kit.app.get_app().next_update_async()
        content.dock_order = 0
        content.focus()

    async def __propert_window(self):
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        import omni.kit.window.property as property_window_ext

        property_window = property_window_ext.get_window()
        property_window.set_scheme_delegate_layout(
            "Create Layout", ["path_prim", "material_prim", "xformable_prim", "shade_prim", "camera_prim"]
        )

    def on_shutdown(self):
        pass
