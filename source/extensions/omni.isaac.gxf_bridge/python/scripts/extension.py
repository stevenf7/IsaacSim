# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import asyncio
import carb
import omni.ext
import omni.ui
import omni.kit.menu
import weakref
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from .. import _gxf_bridge


EXTENSION_NAME = "GXF Bridge"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._settings = carb.settings.get_settings()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=True, dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
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
                with omni.ui.CollapsableFrame("GXF Bridge", height=0, collapsed=False):
                    with omni.ui.VStack(height=0):
                        with omni.ui.HStack():
                            omni.ui.Label("Graph Path ", width=0)
                            self._scene_loader["gxf_graph"] = omni.ui.StringField().model
                            self._scene_loader["gxf_graph"].set_value(
                                self._reb_extension_path + "/data/config/tcp_server.yaml"
                            )
                        self._scene_loader["create_gxf"] = omni.ui.Button(
                            "Create Application", height=0, clicked_fn=self._on_create_destroy_gxf_app_fn
                        )

        self._is_gxf_created = False
        self._gxf_bridge = _gxf_bridge.acquire_gxf_bridge_interface()

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        async def safe_shutdown(bridge):
            omni.timeline.get_timeline_interface().stop()
            await omni.kit.app.get_app().next_update_async()
            if bridge is not None:
                _gxf_bridge.release_gxf_bridge_interface(bridge)

        asyncio.ensure_future(safe_shutdown(self._gxf_bridge))

        remove_menu_items(self._menu_items, "Isaac Utils")

    def _on_create_destroy_gxf_app_fn(self):
        if self._is_gxf_created is False:

            result, status = omni.kit.commands.execute(
                "RobotEngineBridgeGxfCreateApplication",
                base_path=self._reb_extension_path + "/lib",
                manifest_file="manifest.yaml",
                graph_files=[
                    self._scene_loader["gxf_graph"].get_value_as_string(),
                    self._reb_extension_path + "/data/config/isaac_sim_allocator.yaml",
                ],
            )

            self._is_gxf_created = True
            self._scene_loader["create_gxf"].text = "Destroy Application"
        else:
            result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")

            self._is_gxf_created = False
            self._scene_loader["create_gxf"].text = "Create Application"
