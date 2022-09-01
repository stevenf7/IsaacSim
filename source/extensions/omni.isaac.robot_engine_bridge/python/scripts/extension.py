# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import carb
import omni.ext
import omni.ui
import omni.kit.menu
import weakref
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import asyncio


EXTENSION_NAME = "Robot Engine Bridge"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._settings = carb.settings.get_settings()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        json_path_input = self._settings.get("/isaac/robot_engine_bridge/json")

        # The default app json is copied to the resources folder as part of the build process
        # exec_folder resolves automatically to the folder containing the kit binary
        json_path = self._reb_extension_path + "/resources/isaac_engine/json/isaacsim.app.json"

        if json_path_input is not None:
            json_path = json_path_input

        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.dock_order = 3

        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")

        self._scene_loader = {}
        with self._window.frame:
            with omni.ui.VStack(style={"margin": 1}):
                with omni.ui.VStack(height=0):
                    with omni.ui.VStack(
                        height=0,
                        tooltip='Can specify with: --carb/isaac/robot_engine_bridge/json="path/to/app.json" \n Or by entering in this text box',
                    ):
                        omni.ui.Label("Application JSON Path: ")
                        self._scene_loader["json_path"] = omni.ui.StringField().model
                        self._scene_loader["json_path"].set_value(json_path)
                        self._scene_loader["create_sdk"] = omni.ui.Button(
                            "Create Application", height=0, clicked_fn=self._on_create_destroy_sdk_app_fn
                        )

        self._is_created = False
        self._bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Utils")

        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _robot_engine_bridge.release_robot_engine_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._bridge))

    def _on_create_destroy_sdk_app_fn(self):
        if self._is_created is False:
            result, status = omni.kit.commands.execute(
                "RobotEngineBridgeCreateApplication",
                asset_path=self._reb_extension_path,
                app_file=self._scene_loader["json_path"].get_value_as_string(),
                module_paths=[],
                json_files=[],
            )

            self._is_created = True
            self._scene_loader["create_sdk"].text = "Destroy Application"
        else:
            result, status = omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")
            self._is_created = False
            self._scene_loader["create_sdk"].text = "Create Application"
