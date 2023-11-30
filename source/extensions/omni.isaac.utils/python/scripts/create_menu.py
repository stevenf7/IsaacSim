# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import gc
import weakref

import carb
import omni.ext
import omni.kit.commands
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):

        robot_menu = []

        menu_universal_robots = [
            make_menu_item_description(
                ext_id,
                "UR3",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur3/ur3.usd", "/UR3"),
            ),
            make_menu_item_description(
                ext_id,
                "UR5",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur5/ur5.usd", "/UR5"),
            ),
            make_menu_item_description(
                ext_id,
                "UR10",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur10/ur10.usd", "/UR10"),
            ),
            make_menu_item_description(
                ext_id,
                "UR3e",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur3e/ur3e.usd", "/UR3e"),
            ),
            make_menu_item_description(
                ext_id,
                "UR5e",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur5e/ur5e.usd", "/UR5e"),
            ),
            make_menu_item_description(
                ext_id,
                "UR10e",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd", "/UR10e"),
            ),
            make_menu_item_description(
                ext_id,
                "UR16e",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/UniversalRobots/ur16e/ur16e.usd", "/UR16e"),
            ),
        ]

        menu_denso = [
            make_menu_item_description(
                ext_id,
                "Cobotta Pro 900",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Denso/cobotta_pro_900.usd", "/Cobotta_Pro_900"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Cobotta Pro 1300",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Denso/cobotta_pro_1300.usd", "/Cobotta_Pro_1300"
                ),
            ),
        ]

        menu_kawasaki = [
            make_menu_item_description(
                ext_id,
                "RS007L",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kawasaki/RS007L/rs007l_onrobot_rg2.usd", "/RS007L"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RS007N",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kawasaki/RS007N/rs007n_onrobot_rg2.usd", "/RS007N"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RS013N",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kawasaki/RS013N/rs013n_onrobot_rg2.usd", "/RS013N"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RS025N",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kawasaki/RS025N/rs025n_onrobot_rg2.usd", "/RS025N"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RS080N",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kawasaki/RS080N/rs080n_onrobot_rg2.usd", "/RS080N"
                ),
            ),
        ]

        menu_kinova = [
            make_menu_item_description(
                ext_id,
                "Gen3",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kinova/Gen3/gen3n7_instanceable.usd", "/Gen3"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "J2N6S300",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kinova/Jaco2/J2N6S300/j2n6s300_instanceable.usd", "/J2N6S300"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "J2N7S300",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kinova/Jaco2/J2N7S300/j2n7s300_instanceable.usd", "/J2N7S300"
                ),
            ),
        ]

        menu_franka = [
            # make_menu_item_description(
            #     ext_id,
            #     "FactoryFranka",
            #     lambda a=weakref.proxy(self): a.create_asset(
            #         "/Isaac/Robots/FactoryFranka/factory_franka_instanceable.usd", "/FactoryFranka"
            #     ),
            # ),
            make_menu_item_description(
                ext_id,
                "Franka",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Franka/franka_alt_fingers.usd", "/Franka"),
            ),
            make_menu_item_description(
                ext_id,
                "FR3",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Franka/FR3/fr3.usd", "/FR3"),
            ),
        ]

        menu_manipulators = [
            MenuItemDescription(header="Manipulators"),
            MenuItemDescription(name="Denso", sub_menu=menu_denso),
            make_menu_item_description(
                ext_id,
                "Dofbot",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Dofbot/dofbot.usd", "/Dofbot"),
            ),
            make_menu_item_description(
                ext_id,
                "Fanuc CRX10IAL",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Fanuc/CRX10IAL/crx10ial.usd", "/CRX10IAL"),
            ),
            make_menu_item_description(
                ext_id,
                "Festo Cobot",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Festo/FestoCobot/festo_cobot.usd", "/Cobot"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Flexiv Rizon 4",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Flexiv/Rizon4/flexiv_rizon4.usd", "/Rizon_4"
                ),
            ),
            MenuItemDescription(name="Kawasaki", sub_menu=menu_kawasaki),
            MenuItemDescription(name="Kinova", sub_menu=menu_kinova),
            MenuItemDescription(name="Franka", sub_menu=menu_franka),
            make_menu_item_description(
                ext_id,
                "Kuka KR210_L150",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Kuka/KR210_L150/kr210_l150.usd", "/kuka_kr210"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RethinkRobotics Sawyer",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/RethinkRobotics/sawyer_instanceable.usd", "/Sawyer"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Techman TM12",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Techman/TM12/tm12.usd", "/TM12"),
            ),
            MenuItemDescription(name="Universal Robots", sub_menu=menu_universal_robots),
        ]

        menu_unitree = [
            make_menu_item_description(
                ext_id, "A1", lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Unitree/a1.usd", "/A1")
            ),
            make_menu_item_description(
                ext_id, "Go1", lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Unitree/go1.usd", "/Go1")
            ),
        ]

        menu_quadrupeds = [
            MenuItemDescription(header="Quadrupeds"),
            make_menu_item_description(
                ext_id,
                "ANYmal C",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/ANYbotics/anymal_c.usd", "/ANYmal_C"),
            ),
            MenuItemDescription(name="Unitree", sub_menu=menu_unitree),
            # MenuItemDescription(name="ANYbotics", sub_menu=menu_anybotics), # for some reason, the header needed to be above a item, not submenu, to show up
        ]

        menu_aerial = [
            MenuItemDescription(header="Aerials"),
            make_menu_item_description(
                ext_id,
                "Crazyflie",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Crazyflie/cf2x.usd", "/Crazyflie"),
            ),
            make_menu_item_description(
                ext_id,
                "Quadcopter",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Quadcopter/quadcopter.usd", "/Quadcopter"),
            ),
            make_menu_item_description(
                ext_id,
                "Ingenuity",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Ingenuity/ingenuity.usd", "/Ingenuity"),
            ),
        ]

        menu_clearpath = [
            make_menu_item_description(
                ext_id,
                "Dingo",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Clearpath/Dingo/dingo.usd", "/Dingo"),
            ),
            make_menu_item_description(
                ext_id,
                "Jackal",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Clearpath/Jackal/jackal.usd", "/Jackal"),
            ),
            make_menu_item_description(
                ext_id,
                "RidgebackFranka",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Clearpath/RidgebackFranka/ridgeback_franka.usd", "/RidgebackFranka"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "RidgebackUr",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Clearpath/RidgebackUr/ridgeback_ur5.usd", "/RidgebackUr"
                ),
            ),
        ]

        menu_nvidia = [
            make_menu_item_description(
                ext_id,
                "Carter V1",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Carter/carter_v1.usd", "/Carter_v1"),
            ),
            make_menu_item_description(
                ext_id,
                "Nova Carter",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Carter/nova_carter_sensors.usd", "/Nova_Carter"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Jetbot",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Jetbot/jetbot.usd", "/Jetbot"),
            ),
            make_menu_item_description(
                ext_id,
                "Jetracer",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Jetracer/jetracer.usd", "/Jetracer"),
            ),
            make_menu_item_description(
                ext_id, "Kaya", lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Kaya/kaya.usd", "/Kaya")
            ),
        ]

        menu_fraunhofer = [
            make_menu_item_description(
                ext_id,
                "Evobot",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Evobot/evobot.usd", "/Evobot"),
            ),
            make_menu_item_description(
                ext_id,
                "O3dyn",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/O3dyn/o3dyn.usd", "/O3dyn"),
            ),
        ]

        menu_mobile = [
            MenuItemDescription(header="Wheeled Robots"),
            MenuItemDescription(name="Clearpath", sub_menu=menu_clearpath),
            MenuItemDescription(name="Fraunhofer", sub_menu=menu_fraunhofer),
            make_menu_item_description(
                ext_id,
                "Forklift",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/Forklift/forklift_b.usd", "/Forklift"),
            ),
            make_menu_item_description(
                ext_id,
                "Idealworks iw.hub",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Transporter/transporter_sensors.usd", "/iw_hub"
                ),
            ),
            MenuItemDescription(name="NVIDIA", sub_menu=menu_nvidia),
        ]

        menu_other = [
            MenuItemDescription(header="Other"),
            make_menu_item_description(
                ext_id,
                "Humanoid",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Humanoid/humanoid_instanceable.usd", "/Humanoid"
                ),
            ),
        ]

        robot_menu += menu_manipulators
        robot_menu += menu_quadrupeds
        robot_menu += menu_aerial
        robot_menu += menu_mobile
        robot_menu += menu_other

        env_menu = [
            MenuItemDescription(header="Basic"),
            make_menu_item_description(
                ext_id,
                "Flat Grid",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Grid/default_environment.usd", "/FlatGrid"
                ),
            ),
            MenuItemDescription(header="Rooms"),
            make_menu_item_description(
                ext_id,
                "Grid Room",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Grid/gridroom_curved.usd", "/GridRoom"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Simple Room",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Room/simple_room.usd", "/SimpleRoom", [3.15, 3.15, 2.0], [0, 0, 0]
                ),
            ),
            MenuItemDescription(header="Warehouse"),
            make_menu_item_description(
                ext_id,
                "Small Warehouse",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse.usd", "/Warehouse"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Small Warehouse With Multiple Shelves",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/warehouse_multiple_shelves.usd", "/Warehouse"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Full Warehouse",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/Warehouse"
                ),
            ),
            MenuItemDescription(header="Architectural"),
            make_menu_item_description(
                ext_id,
                "Hospital",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Hospital/hospital.usd", "/Hospital", [7.35, -1.5, 2.3], [0, 0, 0]
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Office",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Environments/Office/office.usd", "/Office", [3.15, 3.15, 2.0], [0, 0, 0]
                ),
            ),
        ]
        apriltag_menu = [
            make_menu_item_description(
                ext_id,
                "tag36h11",
                lambda a=weakref.proxy(self): a.create_apriltag(
                    "/Isaac/Materials/AprilTag/AprilTag.mdl",
                    "AprilTag",
                    "/Looks/AprilTag",
                    "/Isaac/Materials/AprilTag/Textures/tag36h11.png",
                ),
            )
        ]

        menu_robotiq = [
            make_menu_item_description(
                ext_id,
                "2F-140",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Robotiq/2F-140/Robotiq_2F_140_physics_edit.usd", "/Robotiq_2F_140"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "2F-85",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Robotiq/2F-85/2f85_instanceable.usd", "/Robotiq_2F_85"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "2F-C2",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/Robotiq/2F-C2/2fc2_instanceable.usd", "/Robotiq_2F_C2"
                ),
            ),
        ]

        menu_grippers = [
            # MenuItemDescription(header="Parallel Grippers"),
            MenuItemDescription(name="Robotiq", sub_menu=menu_robotiq)
        ]

        menu_hand = [
            # MenuItemDescription(header="Hands"),
            make_menu_item_description(
                ext_id,
                "Allegro Hand",
                lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Robots/AllegroHand/allegro_hand.usd", "/AllegroHand"
                ),
            ),
            make_menu_item_description(
                ext_id,
                "Shadow Hand",
                lambda a=weakref.proxy(self): a.create_asset("/Isaac/Robots/ShadowHand/shadow_hand.usd", "/ShadowHand"),
            ),
        ]

        end_effector_menu = menu_hand + menu_grippers

        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                glyph="plug.svg",
                sub_menu=[
                    MenuItemDescription(name="Robots", sub_menu=robot_menu),
                    MenuItemDescription(name="End Effectors", sub_menu=end_effector_menu),
                    MenuItemDescription(name="Environments", sub_menu=env_menu),
                    MenuItemDescription(name="April Tag", sub_menu=apriltag_menu),
                ],
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def create_asset(self, usd_path, stage_path, camera_position=None, camera_target=None):

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
        if camera_position is not None and camera_target is not None:
            set_camera_view(camera_position, camera_target)

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
