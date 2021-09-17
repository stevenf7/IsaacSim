# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

import omni.ext
import omni.kit.commands
import omni.kit.viewport
import omni.ui as ui
from omni.kit.quicklayout import QuickLayout

import gc
import asyncio

from pathlib import Path
from omni.kit.viewport.scripts.viewport import *


DATA_PATH = Path(__file__).parent.parent.parent.parent


async def _load_layout(name: str, layout_file: str):
    # few frames delay to avoid the conflict with the layout of omni.kit.mainwindow
    for i in range(3):
        await omni.kit.app.get_app().next_update_async()

    windows = set(ui.Workspace.get_windows())
    vs_code = ui.Workspace.get_window("VS Code Link")
    vp_2 = ui.Workspace.get_window("Viewport 2")
    vp_3 = ui.Workspace.get_window("Viewport 3")

    def show_debugging():
        if vs_code in windows:
            ui.Workspace.get_window("VS Code Link").visible = True

    def hide_debugging():
        if vs_code in windows:
            ui.Workspace.get_window("VS Code Link").visible = False

    def show_multi_viewport():
        viewport_interface = omni.kit.viewport.get_viewport_interface()
        if vp_2 not in windows and vp_3 not in windows:
            for i in range(2):
                viewportHandle = viewport_interface.create_instance()
                viewport = viewport_interface.get_viewport_window(viewportHandle)
                viewport.set_window_size(350, 350)
                viewport.set_camera_target("/OmniverseKit_Top", 0, 0, 0, True)
        else:
            handle_vp_2 = viewport_interface.get_instance("Viewport 2")
            viewport_2 = viewport_interface.get_viewport_window(handle_vp_2)
            viewport_2.set_visible(True)

            handle_vp_3 = viewport_interface.get_instance("Viewport 3")
            viewport_3 = viewport_interface.get_viewport_window(handle_vp_3)
            viewport_3.set_visible(True)

    def hide_multi_viewport():
        if vp_2 in windows and vp_3 in windows:
            viewport_interface = omni.kit.viewport.get_viewport_interface()
            handle_vp_2 = viewport_interface.get_instance("Viewport 2")
            viewport_2 = viewport_interface.get_viewport_window(handle_vp_2)
            viewport_2.set_visible(False)

            handle_vp_3 = viewport_interface.get_instance("Viewport 3")
            viewport_3 = viewport_interface.get_viewport_window(handle_vp_3)
            viewport_3.set_visible(False)

    if name == "debugging":
        await omni.kit.app.get_app().next_update_async()
        show_debugging()
        await omni.kit.app.get_app().next_update_async()
    else:
        await omni.kit.app.get_app().next_update_async()
        hide_debugging()
        await omni.kit.app.get_app().next_update_async()

    if name == "multi_viewport":
        await omni.kit.app.get_app().next_update_async()
        show_multi_viewport()
        await omni.kit.app.get_app().next_update_async()
    else:
        await omni.kit.app.get_app().next_update_async()
        hide_multi_viewport()
        await omni.kit.app.get_app().next_update_async()

    QuickLayout.load_file(layout_file)


EXTENSION_NAME = "Isaac Sim Layout Manager"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._task = None
        self.menu_items = []
        self.build_menu_items()

    def build_menu_items(self):

        self._editor_menu = omni.kit.ui.get_editor_menu()
        if not self._editor_menu:
            carb.log_warn(f"editor menu not avaliable")
            return

        self._current_layout_priority = 99999

        def add_layout_menu_entry(name, path, key):
            menu_path = f"Window/Layout/{name}"
            menu = self._editor_menu.add_item(menu_path, None, False, self._current_layout_priority)
            self._current_layout_priority = self._current_layout_priority + 1
            menu_action = omni.kit.menu.utils.add_action_to_menu(
                menu_path,
                lambda *_: asyncio.ensure_future(_load_layout(path, f"{DATA_PATH}/layouts/{path}.json")),
                name,
                (carb.input.KEYBOARD_MODIFIER_FLAG_CONTROL, key),
            )

            self.menu_items.append((menu, menu_action))

        add_layout_menu_entry("Default", "default", carb.input.KeyboardInput.KEY_5)
        add_layout_menu_entry("Debugging", "debugging", carb.input.KeyboardInput.KEY_6)
        add_layout_menu_entry("Synthetic Data", "synthetic_data", carb.input.KeyboardInput.KEY_7)
        add_layout_menu_entry("Multi Viewport", "multi_viewport", carb.input.KeyboardInput.KEY_8)

        async def hide_debugging():
            await omni.kit.app.get_app().next_update_async()
            ui.Workspace.get_window("VS Code Link").visible = False
            await omni.kit.app.get_app().next_update_async()

        self._task = asyncio.ensure_future(hide_debugging())

    def get_name(self):
        """Return the name of the extension"""
        return EXTENSION_NAME

    def on_shutdown(self):
        self.menu_items = None
        gc.collect()
