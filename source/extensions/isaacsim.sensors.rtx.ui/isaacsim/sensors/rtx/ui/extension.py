# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc
from pathlib import Path

import carb
import omni.ext
import omni.kit.commands
from isaacsim.core.utils.prims import create_prim, set_prim_visibility
from isaacsim.core.utils.stage import get_next_free_path
from isaacsim.storage.native import get_assets_root_path
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf, Tf


class Extension(omni.ext.IExt):
    HESAI = [{"name": "XT-32 10hz", "filepath": "/Isaac/Sensors/HESAI/XT-32.usd"}]
    NVIDIA = [
        {"name": "Debug Rotary", "filepath": "/Isaac/Sensors/NVIDIA/Debug_Rotary.usda"},
        {"name": "Example Rotary 2D", "filepath": "/Isaac/Sensors/NVIDIA/Example_Rotary_2D.usda"},
        {"name": "Example Rotary Beams", "filepath": "/Isaac/Sensors/NVIDIA/Example_Rotary_BEAMS.usda"},
        {"name": "Example Rotary", "filepath": "/Isaac/Sensors/NVIDIA/Example_Rotary.usda"},
        {"name": "Simple Example Solid State", "filepath": "/Isaac/Sensors/NVIDIA/Simple_Example_Solid_State.usda"},
    ]
    OUSTER = [
        {"name": "OS0", "filepath": "/Isaac/Sensors/Ouster/OS0/OS0.usd"},
        {"name": "OS1", "filepath": "/Isaac/Sensors/Ouster/OS1/OS1.usd"},
        {"name": "OS2", "filepath": "/Isaac/Sensors/Ouster/OS2/OS2.usd"},
    ]
    SICK = [
        {"name": "microScan3 official", "filepath": "/Isaac/Sensors/SICK/microScan3.usd"},
        {"name": "multiScan136", "filepath": "/Isaac/Sensors/SICK/multiScan136.usd"},
        {"name": "multiScan165", "filepath": "/Isaac/Sensors/SICK/multiScan165.usd"},
        {"name": "picoScan150", "filepath": "/Isaac/Sensors/SICK/picoScan150.usd"},
        {"name": "TiM781", "filepath": "/Isaac/Sensors/SICK/tim781.usd"},
    ]
    SLAMTEC = [
        {"name": "RPLIDAR S2E", "filepath": "/Isaac/Sensors/Slamtec/RPLidar_S2e.usd"},
    ]
    Velodyne = [
        {"name": "VLS 128", "filepath": "/Isaac/Sensors/Velodyne/vls-128/vls_128.usd"},
    ]
    ZVISION = [
        {"name": "ML305", "filepath": "/Isaac/Sensors/ZVISION/ZVISION_ML30S.usda"},
        {"name": "MLXS", "filepath": "/Isaac/Sensors/ZVISION/ZVISION_MLXS.usda"},
    ]

    LIDAR_DICT = {
        "HESAI": HESAI,
        "NVIDIA": NVIDIA,
        "OUSTER": OUSTER,
        "SICK": SICK,
        "SLAMTEC": SLAMTEC,
        "Velodyne": Velodyne,
        "ZVISION": ZVISION,
    }

    def on_startup(self, ext_id: str) -> None:
        icon_dir = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        sensor_icon_path = str(Path(icon_dir).joinpath("data/sensor.svg"))

        # Build the RTX Lidar menu as a dictionary.
        rtx_lidar_vendor_list = []
        for vendor, sensors in Extension.LIDAR_DICT.items():
            vendor_menu_items = []
            for sensor in sensors:
                sensor_name = sensor["name"]
                sensor_filepath = sensor["filepath"]
                # Create a menu item with an onclick function that creates the sensor prim
                vendor_menu_items.append(
                    {
                        "name": sensor_name,
                        "onclick_fn": (
                            lambda *_, sensor_name=sensor_name, sensor_filepath=sensor_filepath: self._create_sensor(
                                sensor_name, sensor_filepath
                            )
                        ),
                    }
                )
            rtx_lidar_vendor_list.append({"name": {vendor: vendor_menu_items}})

        # Compose the RTX Lidar menu dictionary.
        rtx_lidar_menu_dict = {"name": {"RTX Lidar": rtx_lidar_vendor_list}}

        # Wrap into a top-level Sensors dictionary (like in the camera extension).
        sensors_menu_dict = {
            "name": {
                "Sensors": [
                    rtx_lidar_menu_dict,
                ]
            },
            "glyph": sensor_icon_path,
        }

        # Define a helper to recursively create submenus.
        def create_submenu(menu_dict):
            # If the dict is a leaf (i.e. "name" is a string), create a MenuItemDescription.
            if "name" in menu_dict and isinstance(menu_dict["name"], str):
                return MenuItemDescription(
                    name=menu_dict["name"],
                    onclick_fn=menu_dict.get("onclick_fn"),
                    onclick_action=menu_dict.get("onclick_action"),
                )
            # Otherwise, for nested dictionaries the key is the submenu name.
            submenu_name = next(iter(menu_dict["name"]))
            items = menu_dict["name"][submenu_name]
            sub_menu_items = []
            for item in items:
                if isinstance(item.get("name"), dict):
                    sub_menu_items.append(create_submenu(item))
                else:
                    sub_menu_items.append(
                        MenuItemDescription(
                            name=item["name"],
                            onclick_fn=item.get("onclick_fn"),
                            onclick_action=item.get("onclick_action"),
                        )
                    )
            return MenuItemDescription(name=submenu_name, sub_menu=sub_menu_items, glyph=menu_dict.get("glyph"))

        # Convert the dictionary to a menu and add it.
        self._menu_items = create_submenu(sensors_menu_dict)
        add_menu_items([self._menu_items], "Create")

        # Add a menu item to the Isaac Sim in context menus.
        context_menu_dict = {
            "name": {
                "Isaac": [
                    sensors_menu_dict,
                ],
            },
            "glyph": sensor_icon_path,
        }

        self._viewport_create_menu = omni.kit.context_menu.add_menu(context_menu_dict, "CREATE")

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self._viewport_create_menu = None
        gc.collect()

    def _get_stage_and_path(self):
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def _create_sensor(self, sensor_name, sensor_filepath):
        create_prim(
            prim_path=get_next_free_path("/" + Tf.MakeValidIdentifier(sensor_name), None),
            prim_type="Xform",
            usd_path=get_assets_root_path() + sensor_filepath,
        )
