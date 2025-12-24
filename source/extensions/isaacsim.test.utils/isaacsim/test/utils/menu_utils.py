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
