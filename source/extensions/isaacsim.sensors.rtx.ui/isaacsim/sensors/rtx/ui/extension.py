# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc
import json
import os
import re
import weakref
from pathlib import Path

import carb
import omni.ext
import omni.kit.commands
from isaacsim.core.utils.extensions import get_extension_path_from_name
from isaacsim.core.utils.prims import create_prim, set_prim_visibility
from isaacsim.core.utils.stage import get_next_free_path
from isaacsim.gui.components.menu import make_menu_item_description
from isaacsim.storage.native import get_assets_root_path
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf, Tf


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:

        rtx_lidar_sub_menu = {}

        # TODO: This currently scans for all the subfolders for json config files, in the future we want to make the menu resemble the folder structure
        config_dir_path = os.path.join(get_extension_path_from_name("isaacsim.sensors.rtx"), "data", "lidar_configs")
        carb.log_warn(f"config_dir_path {config_dir_path}")
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
                    # the regex will substitute symbols from the sensor name with space, to match the file name
                    ui_name = re.sub(r'[@#!$%^&<>:"/\\|?*\0_]', " ", ui_name)
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

        # search each nucleus folder OS0, OS1, OS2, get all usd files
        os_lidars = ["OS0", "OS1", "OS2"]
        for os_lidar in os_lidars:
            os_lidar_path = get_assets_root_path() + f"/Isaac/Sensors/Ouster/{os_lidar}"
            result, files = omni.client.list(os_lidar_path)

            if not result:
                carb.log_error(f"Unable to find {os_lidar_path}")

            for file in files:
                if file.relative_path.endswith(".usd"):
                    name = os.path.splitext(os.path.basename(file.relative_path))[0]
                    # make sure the file name matches the menu display name by replace underscore with space
                    update_lidar_menu_item_with_usd_path(
                        f"{os_lidar}", name.replace("_", " "), f"/Isaac/Sensors/Ouster/{os_lidar}/{name}.usd"
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

        menu_items = [
            MenuItemDescription(
                name="RTX Lidar",
                sub_menu=rtx_lidar_sub_menu_as_list,
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

    def _add_rtx_rotating_lidar(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/rtx_lidar",
            parent=self._get_stage_and_path(),
            config="Example_Rotary",
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        if result:
            # Make lidar invisible on stage as camera
            set_prim_visibility(prim=prim, visible=False)

    def _add_rtx_solid_lidar(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/rtx_lidar",
            parent=self._get_stage_and_path(),
            config="Example_Solid_State",
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        if result:
            # Make lidar invisible on stage as camera
            set_prim_visibility(prim=prim, visible=False)

    def _add_rtx_lidar(self, name, config_name, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/" + Tf.MakeValidIdentifier(name),
            parent=self._get_stage_and_path(),
            config=config_name,
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        if result:
            # Make lidar invisible on stage as camera
            set_prim_visibility(prim=prim, visible=False)
