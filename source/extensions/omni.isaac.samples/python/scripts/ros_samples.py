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
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
import weakref
import carb
import asyncio


class Extension(omni.ext.IExt):
    def on_startup(self):

        self._menu_items = [
            MenuItemDescription(
                name="Communicating",
                sub_menu=[
                    MenuItemDescription(
                        name="ROS",
                        sub_menu=[
                            MenuItemDescription(
                                name="Navigation",
                                onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                                    "/Isaac/Samples/ROS/Scenario/carter_warehouse_navigation.usd"
                                ),
                            )
                        ],
                    )
                ],
            ),
            MenuItemDescription(
                name="Communicating",
                sub_menu=[
                    MenuItemDescription(
                        name="ROS",
                        sub_menu=[
                            MenuItemDescription(
                                name="Stereo",
                                onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                                    "/Isaac/Samples/ROS/Scenario/carter_warehouse_navigation.usd"
                                ),
                            )
                        ],
                    )
                ],
            ),
            MenuItemDescription(
                name="Communicating",
                sub_menu=[
                    MenuItemDescription(
                        name="ROS",
                        sub_menu=[
                            MenuItemDescription(
                                name="April Tag",
                                onclick_fn=lambda a=weakref.proxy(self): a._on_environment_setup(
                                    "/Isaac/Samples/ROS/Scenario/april_tag.usd"
                                ),
                            )
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

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server
        scenario_path = self._nucleus_path + stage_path

        asyncio.ensure_future(load_stage(scenario_path))

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
