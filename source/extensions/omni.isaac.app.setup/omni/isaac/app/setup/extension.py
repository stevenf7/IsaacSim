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
import carb.imgui as _imgui

import omni.kit.app

from omni.kit.window.title import get_main_window_title


class CreateSetupExtension(omni.ext.IExt):
    """Create Final Configuration"""

    def on_startup(self):
        """ setup the window layout, menu, final configuration of the extensions etc """
        self._settings = carb.settings.get_settings()

        # Adjust the Window Title to show the Create Version
        window_title = get_main_window_title()
        base_title = self._settings.get("/app/window/title")

        # I don't think "/app/version" should include all the build info
        # here because we use - in the version it will not be predicatable especially there can be - in the branch name
        app_version = self._settings.get("/app/version")
        app_version = "2020.3"
        window_title.set_app_name(f"{base_title} {app_version}   | Kit")

        # set omnu.ui Help Menu
        app_menu = omni.kit.ui.get_editor_menu()
        self._ui_doc_menu_path = f"Help/Omni UI Docs"
        self._ui_doc_menu_item = app_menu.add_item(self._ui_doc_menu_path, lambda *_: self._show_ui_docs())
        omni.kit.ui.get_editor_menu().set_priority(self._ui_doc_menu_path, -10)

        # setup some imgui Style overide
        imgui = _imgui.acquire_imgui()
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrab, carb.Float4(0.4, 0.4, 0.4, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabHovered, carb.Float4(0.6, 0.6, 0.6, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabActive, carb.Float4(0.8, 0.8, 0.8, 1))

        # there is some issue with DLSS and alpha/bg color, when it is fix we can bring that back
        if False:
            # settings up default Color for Background
            self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/enabled", True)
            self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/backgroundDefaultColor", (0.2, 0.2, 0.2))
            self.__background_color = asyncio.ensure_future(self.__bg_color())

        self.__setup_window_task = asyncio.ensure_future(self.__dock_windows())
        self.__setup_property_window = asyncio.ensure_future(self.__property_window())
        self.__setup_menu = asyncio.ensure_future(self.__menu_update())

    def _show_ui_docs(self):
        """ show the omniverse ui documentation as an external Application """
        import sys
        import subprocess
        import platform

        launch_args = [sys.argv[0]]
        launch_args.append("omni.app.uidoc.kit")

        # Pass all exts folders
        exts_folders = self._settings.get("/app/exts/folders")
        if exts_folders:
            for folder in exts_folders:
                launch_args.extend(["--ext-folder", folder])

        kwargs = {"close_fds": False}
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(launch_args, **kwargs)

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

        stage = ui.Workspace.get_window("Stage")
        stage.dock_order = 0
        stage.focus()

        # # setup the docking Space
        content_old = ui.Workspace.get_window("Content")
        if content_old:
            content_old.dock_order = 1
            content_old.visible = False

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

    async def __property_window(self):
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        import omni.kit.window.property as property_window_ext

        property_window = property_window_ext.get_window()
        property_window.set_scheme_delegate_layout(
            "Create Layout", ["path_prim", "material_prim", "xformable_prim", "shade_prim", "camera_prim"]
        )

    async def __menu_update(self):
        # need to awit (More)
        await omni.kit.app.get_app().next_update_async()

        # Remove some Menu Items
        import omni.kit.ui

        editor_menu = omni.kit.ui.get_editor_menu()
        editor_menu.remove_item("Window/New Viewport Window")

    def on_shutdown(self):
        pass
