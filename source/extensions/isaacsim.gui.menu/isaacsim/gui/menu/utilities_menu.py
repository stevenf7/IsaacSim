# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Utilities menu layout for Isaac Sim."""
import omni.kit.menu.utils
from isaacsim.gui.components.menu import make_menu_item_description
from omni.kit.menu.utils import LayoutSourceSearch, MenuItemDescription, MenuLayout

from .asset_check import AssetCheck


class UtilitiesMenuExtension:
    """Build and manage the Utilities menu.

    Args:
        ext_id: Extension identifier provided by the extension manager.
    """

    def __init__(self, ext_id: str) -> None:
        self._asset_check = AssetCheck()

        self._menu_placeholder = [MenuItemDescription(name="placeholder", show_fn=lambda: False)]
        omni.kit.menu.utils.add_menu_items(self._menu_placeholder, "Utilities")

        self._menu_items = [
            make_menu_item_description(ext_id, "Check Default Assets Root Path", self._asset_check.check_assets),
        ]
        omni.kit.menu.utils.add_menu_items(self._menu_items, "Utilities")

        self.__menu_layout = [
            MenuLayout.Menu(
                "Utilities",
                [
                    MenuLayout.Seperator("Profilers & Debuggers"),
                    MenuLayout.Item("OmniGraph Tool Kit", source="Window/Visual Scripting/Toolkit"),
                    MenuLayout.Item("Physics Debugger", source="Window/Physics/Debug"),
                    MenuLayout.Item("Profiler", source="Window/Profiler"),
                    MenuLayout.Item("Statistics"),
                    MenuLayout.Seperator(),
                    MenuLayout.Item("Check Default Assets Root Path"),
                    MenuLayout.Item("Generate Extension Templates"),
                    MenuLayout.Item("Registered Actions", source="Window/Actions"),
                ],
            )
        ]
        omni.kit.menu.utils.add_layout(self.__menu_layout)

    def shutdown(self) -> None:
        """Remove menu layouts and placeholders.

        Example:
            .. code-block:: python

                menu = UtilitiesMenuExtension("ext.id")
                menu.shutdown()
        """
        omni.kit.menu.utils.remove_layout(self.__menu_layout)
        omni.kit.menu.utils.remove_menu_items(self._menu_items, "Utilities")
        omni.kit.menu.utils.remove_menu_items(self._menu_placeholder, "Utilities")
        self._asset_check.destroy()
        self._asset_check = None
