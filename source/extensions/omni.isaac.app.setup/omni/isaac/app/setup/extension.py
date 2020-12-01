# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
from os import terminal_size, path
import omni.ext
import omni.ui as ui
import carb.settings
import omni.kit.commands
import carb.imgui as _imgui
import carb.tokens

import omni.kit.app
import omni.kit.ui

from omni.kit.window.title import get_main_window_title


class CreateSetupExtension(omni.ext.IExt):
    """Create Final Configuration"""

    def on_startup(self):
        """ setup the window layout, menu, final configuration of the extensions etc """
        self._settings = carb.settings.get_settings()

        # this is a work around as some Extensions don't properly setup their default setting in time
        self._set_defaults()

        # Adjust the Window Title to show the Isaac Sim Version
        window_title = get_main_window_title()

        app_version = self._settings.get("/app/version")
        if not app_version:
            app_version = open(path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../VERSION"))).read()

        if app_version:
            app_version, _ = app_version.split("+")
            window_title.set_app_version(app_version)

        # setup some imgui Style overide
        imgui = _imgui.acquire_imgui()
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrab, carb.Float4(0.4, 0.4, 0.4, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabHovered, carb.Float4(0.6, 0.6, 0.6, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabActive, carb.Float4(0.8, 0.8, 0.8, 1))

        self.__menu_update()

        self.__setup_window_task = asyncio.ensure_future(self.__dock_windows())
        self.__setup_property_window = asyncio.ensure_future(self.__property_window())

    def _set_defaults(self):
        """ this is trying to setup some defaults for extensions to avoid warning """
        self._settings.set_default("/persistent/app/omniverse/bookmarks", {})
        self._settings.set_default("/persistent/app/stage/timeCodeRange", [0, 100])

        self._settings.set_default("/persistent/audio/context/closeAudioPlayerOnStop", False)

        self._settings.set_default("/persistent/app/primCreation/PrimCreationWithDefaultXformOps", True)
        self._settings.set_default("/persistent/app/primCreation/DefaultXformOpType", "Scale, Rotate, Translate")
        self._settings.set_default("/persistent/app/primCreation/DefaultRotationOrder", "ZYX")
        self._settings.set_default("/persistent/app/primCreation/DefaultXformOpPrecision", "Double")

        # omni.kit.property.tagging
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/showAdvancedTagView", False)
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/showHiddenTags", False)
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/modifyHiddenTags", False)

    def _launch_app(self, app_id, console=True, custom_args=None):
        """launch an other Kit app with the same settings"""
        import sys
        import subprocess
        import platform

        launch_args = [sys.argv[0]]
        launch_args.append(app_id)
        if custom_args:
            launch_args.extend(custom_args)

        # Pass all exts folders
        exts_folders = self._settings.get("/app/exts/folders")
        if exts_folders:
            for folder in exts_folders:
                launch_args.extend(["--ext-folder", folder])

        # subprocess don't get the ${app} token somehow we push it into a settings
        app_path = carb.tokens.get_tokens_interface().resolve("${app}")
        launch_args.append(f"--/app/folder='{app_path}'")

        kwargs = {"close_fds": False}
        if platform.system().lower() == "windows":
            if console:
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(launch_args, **kwargs)

    def _show_ui_docs(self):
        """ show the omniverse ui documentation as an external Application """
        self._launch_app("omni.app.uidoc.kit")

    def _show_launcher(self):
        """ show the omniverse ui documentation as an external Application """
        self._launch_app("omni.isaac.launcher.kit", console=False, custom_args={"--/app/auto_launch=false"})

    def __set_background_color(self):
        # there is some issue with DLSS and alpha/bg color, when it is fix we can bring that back
        # settings up default Color for Background
        self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/enabled", True)
        self._settings.set("/rtx-defaults/post/backgroundZeroAlpha/backgroundDefaultColor", (0.2, 0.2, 0.2))
        self.__background_color = asyncio.ensure_future(self.__bg_color())

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
        """ setup all the docking properly for create """
        content = ui.Workspace.get_window("Content 2.0")
        stage = ui.Workspace.get_window("Stage")
        console = ui.Workspace.get_window("Console")
        layer = ui.Workspace.get_window("Layer")
        toolbar = ui.Workspace.get_window("Toolbar")
        property = ui.Workspace.get_window("Property")

        hide_while_wait = False
        if hide_while_wait:
            content.visible = False
            stage.visible = False
            console.visible = False
            layer.visible = False
            property.visible = False
            toolbar.visible = False

            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()

            content.visible = True
            stage.visible = True
            console.visible = True
            layer.visible = True
            property.visible = True
            toolbar.visible = True

        stage.dock_order = 0
        stage.focus()

        # # setup the docking Space
        content_old = ui.Workspace.get_window("Content")
        if content_old:
            content_old.dock_order = 1
            content_old.visible = False

        # dock with the console
        if console:
            content.dock_in(console, ui.DockPosition.SAME)
        else:
            print("failed to get console")

        # we need some way to better predict when this is gonna be possible
        for i in range(5):
            await omni.kit.app.get_app().next_update_async()

        render_settings = ui.Workspace.get_window("RTX Settings")
        if render_settings:
            render_settings.visible = True
            await omni.kit.app.get_app().next_update_async()
            render_settings.dock_in(stage, ui.DockPosition.SAME)
            await omni.kit.app.get_app().next_update_async()
            stage.focus()

        content.dock_order = 0
        content.focus()

    async def __property_window(self):
        await omni.kit.app.get_app().next_update_async()
        import omni.kit.window.property as property_window_ext

        property_window = property_window_ext.get_window()
        property_window.set_scheme_delegate_layout(
            "Create Layout", ["path_prim", "material_prim", "xformable_prim", "shade_prim", "camera_prim"]
        )

    def __menu_update(self):
        # Remove some Menu Items
        editor_menu = omni.kit.ui.get_editor_menu()
        editor_menu.remove_item("Window/New Viewport Window")

        editor_menu.set_priority("Rendering/Render Settings 2.0", -100)
        editor_menu.set_priority("Rendering/Movie Capture", 100)

        # set omnu.ui Help Menu
        self._ui_doc_menu_path = "Help/Omni UI Docs"
        self._ui_doc_menu_item = editor_menu.add_item(self._ui_doc_menu_path, lambda *_: self._show_ui_docs())
        editor_menu.set_priority(self._ui_doc_menu_path, -10)

        launcher_menu_path = "Help/App Launcher"
        self._launcher_menu = editor_menu.add_item(launcher_menu_path, lambda *_: self._show_launcher())
        editor_menu.set_priority(launcher_menu_path, -5)

    def on_shutdown(self):
        pass
