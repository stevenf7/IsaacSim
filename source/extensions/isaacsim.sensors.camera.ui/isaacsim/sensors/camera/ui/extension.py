# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import gc
import weakref
from pathlib import Path

import omni.ext
import omni.kit.commands
from isaacsim.core.utils.prims import create_prim
from isaacsim.core.utils.stage import get_next_free_path
from isaacsim.gui.components.menu import make_menu_item_description
from isaacsim.storage.native import get_assets_root_path
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:

        assets_root_path = get_assets_root_path()
        menu_items = [
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
                                    usd_path=assets_root_path + "/Isaac/Sensors/Intel/RealSense/rsd455.usd",
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
                                    usd_path=assets_root_path + "/Isaac/Sensors/Orbbec/Gemini2/orbbec_gemini2_v1.0.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Orbbec FemtoMega",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Femto", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Orbbec/FemtoMega/orbbec_femtomega_v1.0.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Orbbec Gemini 335",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Gemini335", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path + "/Isaac/Sensors/Orbbec/Gemini335/orbbec_gemini_335.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Orbbec Gemini 335L",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Gemini335L", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
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
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/LeopardImaging/Hawk/hawk_v1.1_nominal.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Owl",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/Owl", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path + "/Isaac/Sensors/LeopardImaging/Owl/owl.usd",
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
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG2/H100F1A/SG2-AR0233C-5200-G2A-H100F1A.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG2-OX03CC-5200-GMSL2-H60YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG2_OX03CC_5200_GMSL2_H60YA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG2/H60YA/Camera_SG2_OX03CC_5200_GMSL2_H60YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG3-ISX031C-GMSL2F-H190XA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG3_ISX031C_GMSL2F_H190XA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG3/H190XA/SG3S-ISX031C-GMSL2F-H190XA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG5-IMX490C-5300-GMSL2-H110SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG5_IMX490C_5300_GMSL2_H110SA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG5/H100SA/SG5-IMX490C-5300-GMSL2-H110SA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H120YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H120YA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG8/H120YA/SG8S-AR0820C-5300-G2A-H120YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H30YA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H30YA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
                                    + "/Isaac/Sensors/Sensing/SG8/H30YA/SG8S-AR0820C-5300-G2A-H30YA.usd",
                                ),
                            ),
                            make_menu_item_description(
                                ext_id,
                                "Sensing SG8-AR0820C-5300-G2A-H60SA",
                                lambda a=weakref.proxy(self): create_prim(
                                    prim_path=get_next_free_path("/SG8_AR0820C_5300_G2A_H60SA", None),
                                    prim_type="Xform",
                                    usd_path=assets_root_path
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
                                    usd_path=assets_root_path + "/Isaac/Sensors/Stereolabs/ZED_X/ZED_X.usd",
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ]

        icon_dir = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        sensor_icon_path = str(Path(icon_dir).joinpath("data/sensor.svg"))
        self._menu_items = [MenuItemDescription(name="Sensors", glyph=sensor_icon_path, sub_menu=menu_items)]
        add_menu_items(self._menu_items, "Create")

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        gc.collect()

    def _get_stage_and_path(self):
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim
