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
from omni.kit.quicklayout import QuickLayout

import gc
import asyncio

from pathlib import Path


DATA_PATH = Path(__file__).parent.parent.parent.parent


async def _load_layout(layout_file: str):
    # few frames delay to avoid the conflict with the layout of omni.kit.mainwindow
    for i in range(3):
        await omni.kit.app.get_app().next_update_async()

    QuickLayout.load_file(layout_file)


EXTENSION_NAME = "Isaac Sim Layout Manager"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):

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
                lambda *_: asyncio.ensure_future(_load_layout(f"{DATA_PATH}/layouts/{path}.json")),
                name,
                (carb.input.KEYBOARD_MODIFIER_FLAG_CONTROL, key),
            )

            self.menu_items.append((menu, menu_action))

        add_layout_menu_entry("Synthetic Data", "synthetic_data", carb.input.KeyboardInput.KEY_5)
        add_layout_menu_entry("Navigation", "navigation", carb.input.KeyboardInput.KEY_6)
        add_layout_menu_entry("Manipulation", "manipulation", carb.input.KeyboardInput.KEY_7)
        add_layout_menu_entry("Debugging", "debugging", carb.input.KeyboardInput.KEY_8)

    def get_name(self):
        """Return the name of the extension"""
        return EXTENSION_NAME

    def on_shutdown(self):
        self.menu_items = None
        gc.collect()
