# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import gc
import weakref
from functools import partial
from pathlib import Path

import omni.ext
import omni.kit.commands
from isaacsim.robot.surface_gripper.ui.widgets.SurfaceGripperPropertiesWidget import SurfaceGripperPropertiesWidget
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:

        self._ext_id = ext_id
        self._ext_name = omni.ext.get_extension_name(ext_id)
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.register_action(
            self._ext_name,
            "isaac_create_surface_gripper",
            partial(self.menu_click),
            display_name="Create Surface Gripper",
            description="Create a physics based gripper for simulating suction/surface type grippers",
            tag="Create Surface Gripper",
        )
        menu_entry = [
            MenuItemDescription(
                name="Surface Gripper",
                # glyph="plug.svg",
                onclick_action=(self._ext_name, "isaac_create_surface_gripper"),
            )
        ]

        self._menu_items = [MenuItemDescription("Robots", sub_menu=menu_entry)]
        add_menu_items(self._menu_items, "Create")
        icon_dir = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module("isaacsim.gui.menu")
        robot_icon_path = str(Path(icon_dir).joinpath("data/robot.svg"))
        context_menu_dict = {
            "name": {
                "Isaac": [
                    {
                        "name": {
                            "Robots": [
                                {
                                    "name": "Surface Gripper",
                                    "onclick_fn": lambda *_: self.menu_click(),
                                },
                            ],
                        },
                        "glyph": robot_icon_path,
                    },
                ],
            },
        }

        self._viewport_create_menu = omni.kit.context_menu.add_menu(context_menu_dict, "CREATE")

        self._register_widget()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self._unregister_widget()
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.deregister_action(
            self._ext_name,
            "isaac_create_surface_gripper",
        )
        self._viewport_create_menu = None
        gc.collect()

    def menu_click(self):
        _, prim = omni.kit.commands.execute("CreateSurfaceGripper")

    def _register_widget(self):
        import omni.kit.window.property as p

        w = p.get_window()
        w.register_widget(
            "prim",
            "surface_gripper",
            SurfaceGripperPropertiesWidget(title="Surface Gripper", collapsed=False),
            False,
        )

    def _unregister_widget(self):
        import omni.kit.window.property as p

        w = p.get_window()
        if w:
            w.unregister_widget("prim", "surface_gripper")
