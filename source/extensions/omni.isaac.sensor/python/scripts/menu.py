# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import json
import os
import weakref

import omni.kit.commands
from omni.isaac.core.utils.extensions import get_extension_path
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.prims import create_prim, set_prim_visibility
from omni.isaac.core.utils.stage import get_next_free_path
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf, Tf


class IsaacSensorMenu:
    def __init__(self, ext_id: str):
        menu_items = [
            make_menu_item_description(ext_id, "Contact Sensor", lambda a=weakref.proxy(self): a._add_contact_sensor()),
            make_menu_item_description(ext_id, "Imu Sensor", lambda a=weakref.proxy(self): a._add_imu_sensor()),
            MenuItemDescription(
                name="RGBD Sensor",
                sub_menu=[
                    MenuItemDescription(
                        name="Intel",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "Intel Realsense D455",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Realsense", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path() + "/Isaac/Sensors/Intel/RealSense/rsd455.usd",
                                ),
                            ),
                        ],
                    ),
                    MenuItemDescription(
                        name="Orbbec",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "Orbbec Gemini 2",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Gemini", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Orbbec/Gemini 2/orbbec_gemini2_V1.0.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Orbbec FemtoMega",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Femto", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Orbbec/FemtoMega/orbbec_femtomega_v1.0.usd",
                                ),
                            ),
                        ],
                    ),
                    MenuItemDescription(
                        name="LeopardImaging",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "Hawk",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Hawk", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/LeopardImaging/Hawk/hawk_v1.1_nominal.usd",
                                ),
                            ),
                        ],
                    ),
                    MenuItemDescription(
                        name="Sensing",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG2-OX03CC-5200-GMSL2-H100F1",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG2_OX03CC_5200_GMSL2_H100F1", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG2_OX03CC_5200_GMSL2_H100F1.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG2-OX03CC-5200-GMSL2-H60YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG2_OX03CC_5200_GMSL2_H60YA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG2_OX03CC_5200_GMSL2_H60YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG3-ISX031C-GMSL2-H190X",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG3_ISX031C_GMSL2_H190X", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG3_ISX031C_GMSL2_H190X.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG5-IMX490C-5300-GMSL2-H110SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG5_IMX490C_5300_GMSL2_H110SA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG5_IMX490C_5300_GMSL2_H110SA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-GMSL2-H120Y1A",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_GMSL2_H120Y1A", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG8_AR0820C_5300_GMSL2_H120Y1A.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-GMSL2-H30S1A",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_GMSL2_H30S1A", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG8_AR0820C_5300_GMSL2_H30S1A.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-GMSL2-H60SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_GMSL2_H60SA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/Camera_SG8_AR0820C_5300_GMSL2_H60SA.usd",
                                ),
                            ),
                        ],
                    ),
                    MenuItemDescription(
                        name="Stereolabs",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "ZED_X",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/ZED_X", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path() + "/Isaac/Sensors/Stereolabs/ZED_X.usd",
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ]

        rtx_lidar_sub_menu = [
            make_menu_item_description(
                ext_id, "Rotating", lambda a=weakref.proxy(self): a._add_rtx_lidar("Rotating", "Example_Rotary")
            ),
            make_menu_item_description(
                ext_id,
                "Solid State",
                lambda a=weakref.proxy(self): a._add_rtx_lidar("Solid_State", "Example_Solid_State"),
            ),
        ]

        config_dir_path = get_extension_path(ext_id) + "/data/lidar_configs"
        config_dirs = [x for x in os.listdir(config_dir_path) if os.path.isdir(config_dir_path + "/" + x)]
        config_dirs.sort()

        for d in config_dirs:
            if d is None:
                continue
            sub_menu = []
            n = d
            d = config_dir_path + "/" + d
            config_files = os.listdir(d)
            config_files.sort()
            for file in config_files:
                if file.endswith(".json"):
                    data = json.load(open(d + "/" + file))
                    ui_name = data["name"]
                    file_name = file[:-5]
                    sub_menu.append(
                        make_menu_item_description(
                            ext_id,
                            ui_name,
                            lambda a=weakref.proxy(self), name=ui_name, config_name=file_name: a._add_rtx_lidar(
                                name, config_name
                            ),
                        )
                    )
            if len(sub_menu) > 0:
                rtx_lidar_sub_menu.append(MenuItemDescription(name=n, sub_menu=sub_menu))

        menu_items.append(
            MenuItemDescription(
                name="RTX Lidar",
                sub_menu=rtx_lidar_sub_menu,
            )
        )
        self._menu_items = [
            MenuItemDescription(
                name="Isaac", glyph="plug.svg", sub_menu=[MenuItemDescription(name="Sensors", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def _get_stage_and_path(self):
        self._stage = omni.usd.get_context().get_stage()
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def _add_contact_sensor(self, *args, **kargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/Contact_Sensor",
            parent=self._get_stage_and_path(),
            min_threshold=0.0,
            max_threshold=100000.0,
            color=Gf.Vec4f(1, 0, 0, 1),
            radius=-1,
            sensor_period=-1,
            translation=Gf.Vec3d(0, 0, 0),
        )

    def _add_imu_sensor(self, *args, **kargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateImuSensor",
            path="/Imu_Sensor",
            parent=self._get_stage_and_path(),
            sensor_period=-1,
            translation=Gf.Vec3d(0, 0, 0),
        )
        # Make lidar invisible on stage as camera
        set_prim_visibility(prim=prim, visible=False)

    def _add_rtx_rotating_lidar(self, *args, **kwargs):
        _, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/rtx_lidar",
            parent=self._get_stage_and_path(),
            config="Example_Rotary",
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        # Make lidar invisible on stage as camera
        set_prim_visibility(prim=prim, visible=False)

    def _add_rtx_solid_lidar(self, *args, **kwargs):
        _, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/rtx_lidar",
            parent=self._get_stage_and_path(),
            config="Example_Solid_State",
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        # Make lidar invisible on stage as camera
        set_prim_visibility(prim=prim, visible=False)

    def _add_rtx_lidar(self, name, config_name, *args, **kwargs):
        _, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/" + Tf.MakeValidIdentifier(name),
            parent=self._get_stage_and_path(),
            config=config_name,
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        # Make lidar invisible on stage as camera
        set_prim_visibility(prim=prim, visible=False)

    def shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self.menus = None
