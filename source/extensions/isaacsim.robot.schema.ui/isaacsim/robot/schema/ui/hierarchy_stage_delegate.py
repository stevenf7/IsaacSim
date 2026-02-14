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
"""Stage delegate customization for the hierarchy widget."""

from typing import Any

import carb
import omni.usd
from omni.kit.widget.stage import ContextMenu
from omni.kit.widget.stage.stage_delegate import StageDelegate


class HierarchyContextMenu(ContextMenu):
    """Custom context menu for the robot hierarchy stage widget.

    Provides expand/collapse functionality for navigating the robot
    joint hierarchy tree structure.
    """

    def on_mouse_event(self, event: Any) -> None:
        """Handle mouse events to show the context menu.

        Args:
            event: The mouse event with payload containing stage and prim info.

        Returns:
            None.
        """
        import omni.kit.menu.core

        if event.type != int(omni.kit.menu.core.MenuEventType.ACTIVATE):
            return

        context_menu = self._get_context_menu_instance()
        if context_menu is None:
            carb.log_error("context_menu is disabled!")
            return

        stage = event.payload.get("stage", None)
        if stage is None:
            carb.log_error("stage not available")
            return

        objects = self._build_menu_objects(event, stage)
        menu_dict = self._build_menu_dict()

        try:
            context_menu.show_context_menu("robot_stage_window", objects, menu_dict)
        except Exception as e:
            carb.log_error(f"Error showing context menu: {str(e)}")

    def _get_context_menu_instance(self) -> Any | None:
        """Get the context menu instance if available.

        Returns:
            The context menu instance, or None if unavailable.
        """
        try:
            import omni.kit.context_menu

            return omni.kit.context_menu.get_instance()
        except ModuleNotFoundError:
            return None

    def _build_menu_objects(self, event: Any, stage: Any) -> dict[str, Any]:
        """Build the objects dictionary for the context menu.

        Args:
            event: The triggering event.
            stage: The USD stage.

        Returns:
            Dictionary of context objects for menu functions.
        """
        prim_path = event.payload["prim_path"]

        objects = {
            "use_hovered": True if prim_path else False,
            "stage_win": self._stage_win,
            "node_open": event.payload["node_open"],
            "stage": stage,
            "function_list": self.function_list,
            "stage_model": self._stage_model,
        }

        prim_list = self._collect_selected_prims(stage, prim_path)
        hovered_prim = self._get_hovered_prim(stage, prim_path, prim_list)

        if prim_list:
            objects["prim_list"] = prim_list
        if hovered_prim:
            objects["hovered_prim"] = hovered_prim

        return objects

    def _collect_selected_prims(self, stage: Any, prim_path: Any) -> list[Any]:
        """Collect currently selected prims.

        Args:
            stage: The USD stage.
            prim_path: The hovered prim path.

        Returns:
            List of selected prim objects.
        """
        prim_list = []
        paths = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if paths:
            for path in paths:
                prim = stage.GetPrimAtPath(path)
                if prim:
                    prim_list.append(prim)
        elif prim_path is not None:
            prim = stage.GetPrimAtPath(prim_path)
            if prim:
                prim_list.append(prim)

        return prim_list

    def _get_hovered_prim(self, stage: Any, prim_path: Any, prim_list: list[Any]) -> Any | None:
        """Get the hovered prim if not already in the selection.

        Args:
            stage: The USD stage.
            prim_path: The hovered prim path.
            prim_list: List of selected prims.

        Returns:
            The hovered prim if not in selection, or None.
        """
        if prim_path is None:
            return None

        for prim in prim_list:
            if prim.GetPath() == prim_path:
                return None

        return stage.GetPrimAtPath(prim_path)

    def _build_menu_dict(self) -> list[dict[str, Any]]:
        """Build the context menu dictionary with expand/collapse options.

        Returns:
            List of menu entry dictionaries.
        """
        return [
            self._build_expand_menu(),
            self._build_collapse_menu(),
        ]

    def _build_expand_menu(self) -> dict[str, Any]:
        """Build the expand submenu entries.

        Returns:
            Dictionary defining the expand menu structure.
        """
        return {
            "name": {
                "Expand": [
                    {"name": "Expand To:", "show_fn": [ContextMenu.show_open_tree]},
                    {
                        "name": "All",
                        "onclick_fn": ContextMenu.expand_all,
                        "show_fn": [ContextMenu.show_open_tree],
                    },
                    {
                        "name": "Component",
                        "onclick_fn": lambda o, k="component": ContextMenu.expand_to(o, k),
                        "show_fn": [ContextMenu.show_open_tree],
                    },
                    {
                        "name": "Group",
                        "onclick_fn": lambda o, k="group": ContextMenu.expand_to(o, k),
                        "show_fn": [ContextMenu.show_open_tree],
                    },
                    {
                        "name": "Assembly",
                        "onclick_fn": lambda o, k="assembly": ContextMenu.expand_to(o, k),
                        "show_fn": [ContextMenu.show_open_tree],
                    },
                    {
                        "name": "SubComponent",
                        "onclick_fn": lambda o, k="subcomponent": ContextMenu.expand_to(o, k),
                        "show_fn": [ContextMenu.show_open_tree],
                    },
                ]
            },
            "glyph": "menu_plus.svg",
            "show_fn": [ContextMenu.show_open_tree],
        }

    def _build_collapse_menu(self) -> dict[str, Any]:
        """Build the collapse submenu entries.

        Returns:
            Dictionary defining the collapse menu structure.
        """
        return {
            "name": {
                "Collapse": [
                    {"name": "Collapse To:", "show_fn": [ContextMenu.show_close_tree]},
                    {
                        "name": "All",
                        "onclick_fn": ContextMenu.collapse_all,
                        "show_fn": [ContextMenu.show_close_tree],
                    },
                    {
                        "name": "Component",
                        "onclick_fn": lambda o, k="component": ContextMenu.collapse_to(o, k),
                        "show_fn": [ContextMenu.show_close_tree],
                    },
                    {
                        "name": "Group",
                        "onclick_fn": lambda o, k="group": ContextMenu.collapse_to(o, k),
                        "show_fn": [ContextMenu.show_close_tree],
                    },
                    {
                        "name": "Assembly",
                        "onclick_fn": lambda o, k="assembly": ContextMenu.collapse_to(o, k),
                        "show_fn": [ContextMenu.show_close_tree],
                    },
                    {
                        "name": "SubComponent",
                        "onclick_fn": lambda o, k="subcomponent": ContextMenu.collapse_to(o, k),
                        "show_fn": [ContextMenu.show_close_tree],
                    },
                ]
            },
            "glyph": "menu_minus.svg",
            "show_fn": [ContextMenu.show_close_tree],
        }


class HierarchyStageDelegate(StageDelegate):
    """Custom stage delegate for the robot hierarchy widget.

    Uses the hierarchy context menu for right-click functionality.
    """

    def __init__(self) -> None:
        super().__init__(context_menu=HierarchyContextMenu())
