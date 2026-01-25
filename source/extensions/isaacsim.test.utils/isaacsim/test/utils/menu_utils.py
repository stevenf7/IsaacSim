# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import omni.kit.app
import omni.kit.ui_test as ui_test
from omni.kit.ui_test import menu_click


async def menu_click_with_retry(
    menu_path: str, delays: list[int] = None, window_name: str = None, wait_n_frames: int = 10
):
    """Click a menu item with retry at different delay speeds.

    Some menu items require different timing to be clicked successfully.
    This function tries multiple delay values before giving up.

    Args:
        menu_path: The menu path to click (e.g., "Create/Sensors/Contact Sensor").
        delays: List of delay values to try in milliseconds. Defaults to [5, 50, 100].
        window_name: Optional window name to check for after clicking.
            If provided, the function returns early when the window is found
            and returns the window widget.

    Returns:
        The found window widget if window_name is provided and found, else None.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import menu_click_with_retry
        >>>
        >>> # Simple menu click
        >>> await menu_click_with_retry("Create/Sensors/Contact Sensor")
        >>>
        >>> # Menu click that waits for a window to appear
        >>> window = await menu_click_with_retry(
        ...     "Tools/Robotics/OmniGraph Controllers/Differential Controller",
        ...     window_name="Differential Controller"
        ... )
    """
    delays = delays or [5, 50, 100]
    for delay in delays:
        try:
            await menu_click(menu_path, human_delay_speed=delay)
            if window_name:
                if (window := ui_test.find(window_name)) is not None:
                    return window
            else:
                for _ in range(wait_n_frames):
                    await omni.kit.app.get_app().next_update_async()
                return None
        except AttributeError as e:
            if "NoneType" in str(e) and delay != delays[-1]:
                continue
            raise
    return None


def get_all_menu_paths(menu_dict: dict, current_path: str = "", root_path: str = "") -> list[str]:
    """Extract all leaf menu paths from a menu dictionary structure.

    This function recursively traverses a menu dictionary (as returned by
    `omni.kit.ui_test.get_context_menu()`) and extracts all leaf menu item paths.

    Args:
        menu_dict: The menu dictionary structure from get_context_menu.
        current_path: The current path prefix (used for recursion).
        root_path: Optional prefix to prepend to all returned paths.

    Returns:
        A list of all menu paths as strings joined by forward slashes.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import get_all_menu_paths
        >>>
        >>> menu_dict = {"Lidar": {"_": ["Sensor A", "Sensor B"]}}
        >>> paths = get_all_menu_paths(menu_dict, root_path="Create/Sensors")
        >>> paths
        ['Create/Sensors/Lidar/Sensor A', 'Create/Sensors/Lidar/Sensor B']
    """
    paths = []
    for key, value in menu_dict.items():
        # The "_" key contains leaf items at the current level
        if key == "_":
            if isinstance(value, list):
                for item in value:
                    path = f"{current_path}/{item}" if current_path else item
                    paths.append(f"{root_path}/{path}" if root_path else path)
            elif isinstance(value, str):
                path = f"{current_path}/{value}" if current_path else value
                paths.append(f"{root_path}/{path}" if root_path else path)
        elif isinstance(value, dict):
            new_path = f"{current_path}/{key}" if current_path else key
            paths.extend(get_all_menu_paths(value, new_path, root_path))
        elif isinstance(value, list):
            for item in value:
                path = f"{current_path}/{key}/{item}" if current_path else f"{key}/{item}"
                paths.append(f"{root_path}/{path}" if root_path else path)
        elif isinstance(value, str):
            path = f"{current_path}/{key}/{value}" if current_path else f"{key}/{value}"
            paths.append(f"{root_path}/{path}" if root_path else path)
    return paths


def count_menu_items(menu_dict: dict) -> int:
    """Recursively count the total number of leaf items in a menu dictionary.

    Args:
        menu_dict: The menu dictionary structure from get_context_menu.

    Returns:
        The total number of leaf menu items.

    Example:

    .. code-block:: python

        >>> from isaacsim.test.utils import count_menu_items
        >>>
        >>> menu_dict = {"Sensors": {"_": ["Contact", "IMU"]}, "Robots": {"_": ["Franka"]}}
        >>> count_menu_items(menu_dict)
        3
    """
    count = 0
    for key, item in menu_dict.items():
        if isinstance(item, dict):
            count += count_menu_items(item)
        elif isinstance(item, list):
            count += len(item)
    return count
