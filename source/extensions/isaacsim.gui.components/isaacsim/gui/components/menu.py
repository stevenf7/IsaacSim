# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import omni.ext
from omni.kit.menu.utils import MenuItemDescription


def make_menu_item_description(ext_id: str, name: str, onclick_fun, action_name: str = "") -> None:
    """Easily replace the onclick_fn with onclick_action when creating a menu description

    Args:
        ext_id (str): The extension you are adding the menu item to.
        name (str): Name of the menu item displayed in UI.
        onclick_fun (Function): The function to run when clicking the menu item.
        action_name (str): name for the action, in case ext_id+name don't make a unique string

    Note:
        ext_id + name + action_name must concatenate to a unique identifier.

    """
    action_unique = f'{ext_id.replace(" ", "_")}{name.replace(" ", "_")}{action_name.replace(" ", "_")}'
    action_registry = omni.kit.actions.core.get_action_registry()
    action_registry.deregister_action(ext_id, action_unique)
    action_registry.register_action(ext_id, action_unique, onclick_fun)
    return MenuItemDescription(name=name, onclick_action=(ext_id, action_unique))


def create_submenu(menu_dict: dict) -> list:
    """Create a list of MenuItemDescription objects from a dictionary definition.

    Recursively converts a nested dictionary structure into menu items. Supports both
    flat menu items and nested submenus of arbitrary depth.

    Args:
        menu_dict: A dictionary defining the menu structure. For leaf items, use
            ``{"name": "Item Name", "onclick_fn": callable, "glyph": "icon.svg"}``.
            For submenus, use ``{"name": {"Submenu Title": [list of item dicts]}}``.

    Returns:
        A list containing one or more MenuItemDescription objects.

    Example:

    .. code-block:: python

        >>> from isaacsim.gui.components.menu import create_submenu
        >>>
        >>> menu_def = {
        ...     "name": {"Sensors": [
        ...         {"name": "Contact Sensor", "onclick_fn": lambda: print("clicked")},
        ...         {"name": "IMU Sensor", "onclick_fn": lambda: print("clicked")},
        ...     ]},
        ...     "glyph": "sensor_icon.svg",
        ... }
        >>> items = create_submenu(menu_def)
        >>> len(items)
        1
    """
    if "name" in menu_dict and isinstance(menu_dict["name"], str):
        return [
            MenuItemDescription(
                name=menu_dict["name"],
                onclick_fn=menu_dict.get("onclick_fn"),
                onclick_action=menu_dict.get("onclick_action"),
                glyph=menu_dict.get("glyph"),
            )
        ]

    submenu_name = next(iter(menu_dict["name"]))
    items = menu_dict["name"][submenu_name]
    sub_menu_items = []
    for item in items:
        if isinstance(item.get("name"), dict):
            sub_menu_items.extend(create_submenu(item))
        else:
            sub_menu_items.append(
                MenuItemDescription(
                    name=item["name"],
                    onclick_fn=item.get("onclick_fn"),
                    onclick_action=item.get("onclick_action"),
                )
            )

    return [MenuItemDescription(name=submenu_name, sub_menu=sub_menu_items, glyph=menu_dict.get("glyph"))]
