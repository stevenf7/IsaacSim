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
from omni.isaac.core.utils.prims import create_prim, set_prim_visibility
from omni.isaac.core.utils.stage import get_next_free_path
from omni.isaac.nucleus import get_assets_root_path
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf, Tf


class IsaacSensorMenu:
    def __init__(self, ext_id: str):
        menu_items = [
            make_menu_item_description(ext_id, "Contact Sensor", lambda a=weakref.proxy(self): a._add_contact_sensor()),
            make_menu_item_description(ext_id, "Imu Sensor", lambda a=weakref.proxy(self): a._add_imu_sensor()),
            make_menu_item_description(
                ext_id, "LightBeam Sensor", lambda a=weakref.proxy(self): a._add_lightbeam_sensor()
            ),
            MenuItemDescription(
                name="Camera and Depth Sensors",
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
                                    prim_path=get_next_free_path("/Gemini2", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Orbbec/Gemini2/orbbec_gemini2_v1.0.usd",
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
                            make_menu_item_description(
                                ext_id,
                                "Orbbec Gemini 335",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Gemini335", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Orbbec/Gemini335/orbbec_gemini_335.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Orbbec Gemini 335L",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Gemini335L", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Orbbec/Gemini335L/orbbec_gemini_335L.usd",
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
                            make_menu_item_description(
                                ext_id,
                                "Owl",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Owl", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path() + "/Isaac/Sensors/LeopardImaging/Owl/owl.usd",
                                ),
                            ),
                        ],
                    ),
                    MenuItemDescription(
                        name="Sensing",
                        sub_menu=[
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG2-AR0233C-5200-G2A-H100F1A",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG2_AR0233C_5200_G2A_H100F1A", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG2/H100F1A/SG2-AR0233C-5200-G2A-H100F1A.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG2-OX03CC-5200-GMSL2-H60YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG2_OX03CC_5200_GMSL2_H60YA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG2/H60YA/Camera_SG2_OX03CC_5200_GMSL2_H60YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG3-ISX031C-GMSL2F-H190XA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG3_ISX031C_GMSL2F_H190XA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG3/H190XA/SG3S-ISX031C-GMSL2F-H190XA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG5-IMX490C-5300-GMSL2-H110SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG5_IMX490C_5300_GMSL2_H110SA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG5/H100SA/SG5-IMX490C-5300-GMSL2-H110SA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H120YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H120YA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG8/H120YA/SG8S-AR0820C-5300-G2A-H120YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H30SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H30SA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG8/H30SA/SG8S-AR0820C-5300-G2A-H30YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H60SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H60SA", None),
                                    prim_type="Xform",
                                    usd_path=get_assets_root_path()
                                    + "/Isaac/Sensors/Sensing/SG8/H60SA/SG8S-AR0820C-5300-G2A-H60SA.usd",
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
                                    usd_path=get_assets_root_path() + "/Isaac/Sensors/Stereolabs/ZED_X/ZED_X.usd",
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ]

        rtx_lidar_sub_menu = {}

        # TODO: This currently scans for all the subfolders for json config files, in the future we want to make the menu resemble the folder structure
        config_dir_path = os.path.join(get_extension_path(ext_id), "data", "lidar_configs")
        config_dirs = []
        config_dirs.sort()

        for root, dirs, files in os.walk(config_dir_path):
            for name in dirs:
                config_dirs.append(os.path.join(root, name))

        for d in config_dirs:
            if d is None:
                continue
            sub_menu = {}
            n = os.path.basename(d)

            config_files = os.listdir(d)
            config_files.sort()
            for file in config_files:
                if file.endswith(".json"):
                    data = json.load(open(os.path.join(d, file)))
                    ui_name = data["name"]
                    file_name = file[:-5]
                    sub_menu[ui_name] = make_menu_item_description(
                        ext_id,
                        ui_name,
                        lambda a=weakref.proxy(self), name=ui_name, config_name=file_name: a._add_rtx_lidar(
                            name, config_name
                        ),
                    )
            if len(sub_menu) > 0:
                rtx_lidar_sub_menu[n] = sub_menu

        def update_lidar_menu_item_with_usd_path(sub_menu: str, config_name: str, usd_path: str):
            rtx_lidar_sub_menu[sub_menu][config_name] = make_menu_item_description(
                ext_id,
                config_name,
                lambda a=weakref.proxy(self): create_prim(
                    prim_path=get_next_free_path("/" + Tf.MakeValidIdentifier(config_name), None),
                    prim_type="Xform",
                    usd_path=get_assets_root_path() + usd_path,
                ),
            )

        update_lidar_menu_item_with_usd_path("HESAI", "XT-32 10hz", "/Isaac/Sensors/HESAI/XT-32.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK microscan3 official", "/Isaac/Sensors/SICK/microScan3.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK multiScan136", "/Isaac/Sensors/SICK/multiScan136.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK multiScan165", "/Isaac/Sensors/SICK/multiScan165.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK picoScan150", "/Isaac/Sensors/SICK/picoScan150.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK TiM781", "/Isaac/Sensors/SICK/tim781.usd")
        update_lidar_menu_item_with_usd_path("SLAMTEC", "RPLIDAR S2E", "/Isaac/Sensors/Slamtec/RPLidar_S2e.usd")
        update_lidar_menu_item_with_usd_path(
            "Velodyne", "Velodyne VLS-128", "/Isaac/Sensors/Velodyne/vls-128/vls_128.usd"
        )

        # Convert lidar submenu dictionary into list
        rtx_lidar_sub_menu_as_list = [
            make_menu_item_description(
                ext_id, "Rotating", lambda a=weakref.proxy(self): a._add_rtx_lidar("Rotating", "Example_Rotary")
            ),
            make_menu_item_description(
                ext_id,
                "Solid State",
                lambda a=weakref.proxy(self): a._add_rtx_lidar("Solid_State", "Example_Solid_State"),
            ),
        ]
        for name in rtx_lidar_sub_menu:
            rtx_lidar_sub_menu_as_list.append(
                MenuItemDescription(name=name, sub_menu=list(rtx_lidar_sub_menu[name].values()))
            )

        menu_items.append(
            MenuItemDescription(
                name="RTX Lidar",
                sub_menu=rtx_lidar_sub_menu_as_list,
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

    # create light beam sensor
    def _add_lightbeam_sensor(self, *args, **kargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateLightBeamSensor",
            path="/LightBeam_Sensor",
            parent=self._get_stage_and_path(),
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
            forward_axis=Gf.Vec3d(1, 0, 0),
        )

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
