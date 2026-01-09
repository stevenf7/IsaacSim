# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Menu setup utilities for Isaac Sim application.

This module provides functions for configuring application menus including
layout shortcuts and help menu items.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Union

import carb.input
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, build_submenu_dict

from .layout import LAYOUTS_PATH, load_layout


def create_layout_menu_item(
    name: str,
    layout_name_or_func: Union[str, Callable[[], Any]],
    hotkey: carb.input.KeyboardInput,
) -> MenuItemDescription:
    """Create a menu item for layout operations.

    Creates a menu item that either loads a layout file or executes
    an async function when clicked.

    Args:
        name: Display name for the menu item.
        layout_name_or_func: Either a layout filename (without extension) or an async function.
        hotkey: Keyboard shortcut key (will be combined with Ctrl modifier).

    Returns:
        Configured menu item descriptor for use with the menu system.
    """
    menu_path = f"Layouts/{name}"

    if inspect.isfunction(layout_name_or_func):
        onclick_fn = lambda *_: asyncio.ensure_future(layout_name_or_func())
    else:
        layout_file = str(LAYOUTS_PATH / f"{layout_name_or_func}.json")
        onclick_fn = lambda *_: asyncio.ensure_future(load_layout(layout_file))

    return MenuItemDescription(
        name=menu_path,
        onclick_fn=onclick_fn,
        hotkey=(carb.input.KEYBOARD_MODIFIER_FLAG_CONTROL, hotkey),
    )


def setup_menus(show_ui_docs_callback: Callable[[], None]) -> None:
    """Configure application menus including layouts and help items.

    Sets up the Help menu with UI documentation link and the Layouts menu
    with predefined layout options and quick save/load functionality.

    Args:
        show_ui_docs_callback: Callback function to launch the UI documentation app.
    """
    from omni.kit.quicklayout import QuickLayout

    async def quick_save() -> None:
        QuickLayout.quick_save(None, None)

    async def quick_load() -> None:
        QuickLayout.quick_load(None, None)

    menu_items = [
        MenuItemDescription(name="Help/Omni UI Docs", onclick_fn=lambda *_: show_ui_docs_callback()),
        create_layout_menu_item("Default", "default", carb.input.KeyboardInput.KEY_1),
        create_layout_menu_item("Visual Scripting", "visualScripting", carb.input.KeyboardInput.KEY_4),
        create_layout_menu_item("Replicator", "sdg", carb.input.KeyboardInput.KEY_5),
        create_layout_menu_item("Quick Save", quick_save, carb.input.KeyboardInput.KEY_7),
        create_layout_menu_item("Quick Load", quick_load, carb.input.KeyboardInput.KEY_8),
    ]

    menu_dict = build_submenu_dict(menu_items)
    for group in menu_dict:
        add_menu_items(menu_dict[group], group)
