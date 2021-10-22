# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import omni.ext
import omni.kit.commands
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.core.utils.nucleus import find_nucleus_server
import carb
import gc
import weakref


class Extension(omni.ext.IExt):
    def on_startup(self):

        manip_menu = [
            MenuItemDescription(
                name="Franka",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Franka/franka_alt_fingers.usd", "/Franka"
                ),
            ),
            MenuItemDescription(
                name="UR10",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UR10/ur10.usd", "/UR10"),
            ),
            MenuItemDescription(
                name="Dofbot",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Dofbot/dofbot.usd", "/Dofbot"),
            ),
        ]

        mobile_menu = [
            MenuItemDescription(
                name="Carter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Carter/carter_sphere_wheels_lidar.usd", "/Carter"
                ),
            ),
            MenuItemDescription(
                name="Transporter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Transporter/transporter_sensors.usd", "/Transporter"
                ),
            ),
            MenuItemDescription(
                name="Kaya",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Kaya/kaya.usd", "/Kaya"),
            ),
            MenuItemDescription(
                name="Jetbot",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Jetbot/jetbot.usd", "/Jetbot"),
            ),
            MenuItemDescription(
                name="Jetracer",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Jetracer/jetracer.usd", "/Jetracer"
                ),
            ),
        ]

        robot_menu = [
            MenuItemDescription(name="Manipulators", sub_menu=manip_menu),
            MenuItemDescription(name="Mobile Bases", sub_menu=mobile_menu),
        ]
        from_menu = [MenuItemDescription(name="From Library", sub_menu=robot_menu)]

        env_menu = [
            MenuItemDescription(
                name="Grid Room",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Grid/gridroom_curved.usd", "/GridRoom"
                ),
            ),
            MenuItemDescription(
                name="Simple Room",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Room/simple_room.usd", "/SimpleRoom"
                ),
            ),
            MenuItemDescription(
                name="Warehouse",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(
                name="Warehouse Multiple Shelves",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(
                name="Hospital",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Hospital/hospital.usd", "/Hospital"
                ),
            ),
            MenuItemDescription(
                name="Office",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Office/office.usd", "/Office"
                ),
            ),
        ]
        apriltag_menu = [
            MenuItemDescription(
                name="tag36h11",
                onclick_fn=lambda a=weakref.proxy(self): a.create_apriltag(
                    "/Isaac/Materials/AprilTag/AprilTag.mdl",
                    "AprilTag",
                    "/Looks/AprilTag",
                    "/Isaac/Materials/AprilTag/Textures/tag36h11.png",
                ),
            )
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                glyph="plug.svg",
                sub_menu=[
                    MenuItemDescription(name="Robots", sub_menu=from_menu),
                    MenuItemDescription(name="Environments", sub_menu=env_menu),
                    MenuItemDescription(name="April Tag", sub_menu=apriltag_menu),
                ],
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def create_asset(self, usd_path, stage_path):

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server

        omni.kit.commands.execute(
            "CreateReferenceCommand",
            usd_context=omni.usd.get_context(),
            path_to=stage_path,
            asset_path=self._nucleus_path + usd_path,
            instanceable=False,
        )

        pass

    def create_apriltag(self, usd_path, shader_name, stage_path, tag_path):
        result, nucleus_server = find_nucleus_server()
        from pxr import Sdf

        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server

        stage = omni.usd.get_context().get_stage()
        stage_path = omni.usd.get_stage_next_free_path(stage, stage_path, False)

        async def create_tag():
            omni.kit.commands.execute(
                "CreateMdlMaterialPrim",
                mtl_url=self._nucleus_path + usd_path,
                mtl_name=shader_name,
                mtl_path=stage_path,
                select_new_prim=True,
            )
            mtl = stage.GetPrimAtPath(stage_path + "/Shader")
            # it can take multiple frames after mdl is created to be able to set a property
            while mtl.GetAttribute("inputs:tag_mosaic").Get() is None:
                await omni.kit.app.get_app().next_update_async()
                omni.kit.commands.execute(
                    "ChangeProperty",
                    prop_path=Sdf.Path(stage_path + "/Shader.inputs:tag_mosaic"),
                    value=Sdf.AssetPath(self._nucleus_path + tag_path),
                    prev=None,
                )

        asyncio.ensure_future(create_tag())

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        gc.collect()
