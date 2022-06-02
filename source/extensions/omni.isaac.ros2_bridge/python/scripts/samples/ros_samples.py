# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni.usd
import omni.ext
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.core.utils.nucleus import get_assets_root_path
import weakref
import carb
import asyncio


class Extension(omni.ext.IExt):
    def on_startup(self):

        self._menu_items = [
            MenuItemDescription(
                name="ROS",
                sub_menu=[
                    MenuItemDescription(
                        name="Navigation",
                        onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                            "/Isaac/Samples/ROS2/Scenario/carter_warehouse_navigation.usd"
                        ),
                    )
                ],
            ),
            MenuItemDescription(
                name="ROS",
                sub_menu=[
                    MenuItemDescription(
                        name="Multiple Robot Navigation",
                        sub_menu=[
                            MenuItemDescription(
                                name="Hospital Scene",
                                onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                                    "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_hospital_navigation.usd"
                                ),
                            ),
                            MenuItemDescription(
                                name="Office Scene",
                                onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                                    "/Isaac/Samples/ROS2/Scenario/multiple_robot_carter_office_navigation.usd"
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ]

        add_menu_items(self._menu_items, "Isaac Examples")

    def _menu_callback(self):
        self._build_ui()

    def _on_environment_setup(self, stage_path):
        async def load_stage(path):
            await omni.usd.get_context().open_stage_async(path)

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        scenario_path = self._assets_root_path + stage_path

        asyncio.ensure_future(load_stage(scenario_path))

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
