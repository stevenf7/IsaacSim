# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# This is an example script showing how to use rosbridge to publish joint_states of an articulated robot

from pxr import Sdf, Gf, UsdGeom, UsdLux
import omni.usd
import omni
import omni.ui as ui
import omni.isaac.RosBridgeSchema as ROSSchema
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import weakref

EXTENSION_NAME = "ROS Services"


class Extension(omni.ext.IExt):
    def on_startup(self):
        # setting up the UI on the menu bar for this example

        self._window = ui.Window(EXTENSION_NAME, width=400, height=200, visible=False)
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(name="Communicating", sub_menu=[MenuItemDescription(name="ROS", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

        with self._window.frame:
            with ui.VStack():
                ui.Button("Clean Stage", tooltip="Clean the stage", clicked_fn=self._on_clean_stage)
                ui.Button("Add Cube", tooltip="Add a Cube and start its pose service", clicked_fn=self._on_add_cube)

        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_clean_stage(self):
        asyncio.ensure_future(self._load_stage())

    async def _load_stage(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = omni.usd.get_context().get_stage()
        # create some lighting
        distantLight = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        distantLight.CreateIntensityAttr(500)
        self._viewport.set_camera_position("/OmniverseKit_Persp", 103.4, 13.8, 19.8, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", -225.0, -23.78, -26.17, True)

    # add cube
    def _on_add_cube(self):
        # create a cube
        self._stage = omni.usd.get_context().get_stage()
        distantLight = UsdLux.DistantLight.Define(self._stage, Sdf.Path("/World/defaultLight"))
        distantLight.CreateIntensityAttr(3000)
        CubePath = "/Cube"
        # position in space
        cube_pos = Gf.Vec3f(0.0, 0.0, 0.0)
        size = 10  # cm
        cubeGeom = UsdGeom.Cube.Define(self._stage, CubePath)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(cube_pos)

        # start its own pose service
        omni.kit.commands.execute(
            "ROSBridgeCreateTeleport",
            path="/ROS_Teleport",
            enabled=True,
            service_topic="/teleport_pos",
            teleport_prims_rel=["/Cube"],
        )

        # make sure timeline is playing for sending and receiving ros messages
        if not self._timeline.is_playing():
            self._timeline.play()
