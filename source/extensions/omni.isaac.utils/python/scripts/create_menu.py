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
from omni.isaac.core.utils.nucleus import get_assets_root_path
import carb
import gc
import weakref


class Extension(omni.ext.IExt):
    def on_startup(self):

        robot_menu = []

        menu_universal_robots = [
            MenuItemDescription(
                name="UR3",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur3/ur3.usd", "/UR3"
                ),
            ),
            MenuItemDescription(
                name="UR5",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur5/ur5.usd", "/UR5"
                ),
            ),
            MenuItemDescription(
                name="UR10",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur10/ur10.usd", "/UR10"
                ),
            ),
            MenuItemDescription(
                name="UR3e",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur3e/ur3e.usd", "/UR3e"
                ),
            ),
            MenuItemDescription(
                name="UR5e",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur5e/ur5e.usd", "/UR5e"
                ),
            ),
            MenuItemDescription(
                name="UR10e",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd", "/UR10e"
                ),
            ),
            MenuItemDescription(
                name="UR16e",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/UniversalRobots/ur16e/ur16e.usd", "/UR16e"
                ),
            ),
        ]

        menu_denso = [
            MenuItemDescription(
                name="Cobotta Pro 900",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Denso/cobotta_pro_900.usd", "/Cobotta_Pro_900"
                ),
            ),
            MenuItemDescription(
                name="Cobotta Pro 1300",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Denso/cobotta_pro_1300.usd", "/Cobotta_Pro_1300"
                ),
            ),
        ]

        menu_manipulators = [
            MenuItemDescription(header="Manipulators"),
            MenuItemDescription(
                name="Dofbot",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Dofbot/dofbot.usd", "/Dofbot"),
            ),
            MenuItemDescription(name="Denso", sub_menu=menu_denso),
            MenuItemDescription(
                name="Franka",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Franka/franka_alt_fingers.usd", "/Franka"
                ),
            ),
            MenuItemDescription(name="Univeral Robots", sub_menu=menu_universal_robots),
        ]

        menu_unitree = [
            MenuItemDescription(
                name="A1",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Unitree/a1.usd", "/A1"),
            ),
            MenuItemDescription(
                name="Go1",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Unitree/go1.usd", "/Go1"),
            ),
        ]

        menu_anybotics = [
            MenuItemDescription(
                name="ANYmal C",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Unitree/anymal_c.usd", "/ANYmal_C"
                ),
            )
        ]

        menu_quadrupeds = [
            MenuItemDescription(header="Quadrupeds"),
            MenuItemDescription(
                name="ANYmal C",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Unitree/anymal_c.usd", "/ANYmal_C"
                ),
            ),
            MenuItemDescription(name="Unitree", sub_menu=menu_unitree),
            # MenuItemDescription(name="ANYbotics", sub_menu=menu_anybotics), # for some reason, the header needed to be above a item, not submenu, to show up
        ]

        menu_quadrotors = [
            MenuItemDescription(header="Quadcopters"),
            MenuItemDescription(
                name="Crazyflie",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Crazyflie/cf2x.usd", "/Crazyflie"
                ),
            ),
            MenuItemDescription(
                name="Quadcopter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Quadcopter/quadcopter.usd", "/Quadcopter"
                ),
            ),
        ]

        menu_nvidia = [
            MenuItemDescription(
                name="Carter V1",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Carter/carter_v1.usd", "/Carter"
                ),
            ),
            MenuItemDescription(
                name="Carter V2",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Carter/carter_v2.usd", "/Carter"
                ),
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
            MenuItemDescription(
                name="Kaya",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Kaya/kaya.usd", "/Kaya"),
            ),
        ]

        menu_mobile = [
            MenuItemDescription(header="Wheeled Robots"),
            MenuItemDescription(name="NVIDIA", sub_menu=menu_nvidia),
            MenuItemDescription(
                name="Transporter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Transporter/transporter_sensors.usd", "/Transporter"
                ),
            ),
        ]

        robot_menu += menu_manipulators
        robot_menu += menu_quadrupeds
        robot_menu += menu_quadrotors
        robot_menu += menu_mobile

        env_menu = [
            MenuItemDescription(header="Basic"),
            MenuItemDescription(
                name="Flat Grid",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Grid/default_environment.usd", "/FlatGrid"
                ),
            ),
            MenuItemDescription(header="Rooms"),
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
            MenuItemDescription(header="Warehouse"),
            MenuItemDescription(
                name="Small Warehouse",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(
                name="Small Warehouse With Multiple Shelves",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(
                name="Full Warehouse",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(header="Architectural"),
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
                    "/Materials/AprilTag/AprilTag.mdl",
                    "AprilTag",
                    "/Looks/AprilTag",
                    "/Materials/AprilTag/Textures/tag36h11.png",
                ),
            )
        ]

        menu_end_effectors = [
            MenuItemDescription(header="Hands"),
            MenuItemDescription(
                name="Allegro Hand",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/AllegroHand/allegro_hand.usd", "/AllegroHand"
                ),
            ),
            MenuItemDescription(
                name="Shadow Hand",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/ShadowHand/shadow_hand.usd", "/ShadowHand"
                ),
            ),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                glyph="plug.svg",
                sub_menu=[
                    MenuItemDescription(name="Robots", sub_menu=robot_menu),
                    MenuItemDescription(name="End Effectors", sub_menu=menu_end_effectors),
                    MenuItemDescription(name="Environments", sub_menu=env_menu),
                    MenuItemDescription(name="April Tag", sub_menu=apriltag_menu),
                ],
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def create_asset(self, usd_path, stage_path):

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        omni.kit.commands.execute(
            "CreateReferenceCommand",
            usd_context=omni.usd.get_context(),
            path_to=stage_path,
            asset_path=self._assets_root_path + usd_path,
            instanceable=False,
        )

        pass

    def create_apriltag(self, usd_path, shader_name, stage_path, tag_path):
        from pxr import Sdf

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        stage = omni.usd.get_context().get_stage()
        stage_path = omni.usd.get_stage_next_free_path(stage, stage_path, False)

        async def create_tag():
            omni.kit.commands.execute(
                "CreateMdlMaterialPrim",
                mtl_url=self._assets_root_path + usd_path,
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
                    value=Sdf.AssetPath(self._assets_root_path + tag_path),
                    prev=None,
                )

        asyncio.ensure_future(create_tag())

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        gc.collect()
