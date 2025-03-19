# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc
import os
import weakref
from pathlib import Path

import carb
import omni.ext
import omni.kit.commands
from isaacsim.core.utils.prims import create_prim, set_prim_visibility
from isaacsim.core.utils.stage import get_next_free_path
from isaacsim.gui.components.menu import make_menu_item_description
from isaacsim.storage.native import get_assets_root_path
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf, Tf

SUPPORTED_VARIANTS_OUSTER = {
    "OS0": [
        "OS0_REV6_128ch10hz512res",
        "OS0_REV6_128ch10hz1024res",
        "OS0_REV6_128ch10hz2048res",
        "OS0_REV6_128ch20hz512res",
        "OS0_REV6_128ch20hz1024res",
        "OS0_REV7_128ch10hz512res",
        "OS0_REV7_128ch10hz1024res",
        "OS0_REV7_128ch10hz2048res",
        "OS0_REV7_128ch20hz512res",
        "OS0_REV7_128ch20hz1024res",
    ],
    "OS1": [
        "OS1_REV6_32ch10hz512res",
        "OS1_REV6_32ch10hz1024res",
        "OS1_REV6_32ch10hz2048res",
        "OS1_REV6_32ch20hz512res",
        "OS1_REV6_32ch20hz1024res",
        "OS1_REV6_32ch20hz2048res",
        "OS1_REV6_128ch10hz512res",
        "OS1_REV6_128ch10hz1024res",
        "OS1_REV6_128ch10hz2048res",
        "OS1_REV6_128ch20hz512res",
        "OS1_REV6_128ch20hz1024res",
        "OS1_REV6_128ch20hz2048res",
        "OS1_REV7_128ch10hz512res",
        "OS1_REV7_128ch10hz1024res",
        "OS1_REV7_128ch10hz2048res",
        "OS1_REV7_128ch20hz512res",
        "OS1_REV7_128ch20hz1024res",
        "OS1_REV7_128ch20hz2048res",
    ],
    "OS2": [
        "OS2_REV6_128ch10hz512res",
        "OS2_REV6_128ch10hz1024res",
        "OS2_REV6_128ch10hz2048res",
        "OS2_REV6_128ch20hz512res",
        "OS0_REV6_128ch20hz1024res",
        "OS2_REV7_128ch10hz512res",
        "OS2_REV7_128ch10hz1024res",
        "OS2_REV7_128ch10hz2048res",
        "OS2_REV7_128ch20hz512res",
        "OS2_REV7_128ch20hz1024res",
    ],
}


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str) -> None:

        # Dictionary of all the submenus for the RTX Lidar menu
        # key is the submenu name, value is a dictionary of menu items
        rtx_lidar_sub_menu = {
            "HESAI": {},
            "NVIDIA": {},
            "OUSTER": {},
            "SICK": {},
            "SLAMTEC": {},
            "Velodyne": {},
            "ZVISION": {},
        }

        # Explicitly add menu items for any lidar config with a USD or USDA
        def update_lidar_menu_item_with_usd_path(sub_menu: str, config_name: str, usd_path: str):
            if usd_path.endswith(".usd"):
                rtx_lidar_sub_menu[sub_menu][config_name] = make_menu_item_description(
                    ext_id,
                    config_name,
                    lambda a=weakref.proxy(self): create_prim(
                        prim_path=get_next_free_path("/" + Tf.MakeValidIdentifier(config_name), None),
                        prim_type="Xform",
                        usd_path=get_assets_root_path() + usd_path,
                    ),
                )
            elif usd_path.endswith(".usda"):
                rtx_lidar_sub_menu[sub_menu][config_name] = make_menu_item_description(
                    ext_id,
                    config_name,
                    lambda a=weakref.proxy(
                        self
                    ), name=config_name, asset_path=get_assets_root_path() + usd_path: a._add_rtx_lidar(
                        name, asset_path
                    ),
                )

        update_lidar_menu_item_with_usd_path("HESAI", "Hesai XT32 SD10", "/Isaac/Sensors/HESAI/XT-32.usd")
        update_lidar_menu_item_with_usd_path("NVIDIA", "Debug Rotary", "/Isaac/Sensors/NVIDIA/Debug_Rotary.usda")
        update_lidar_menu_item_with_usd_path(
            "NVIDIA", "Example Rotary 2D", "/Isaac/Sensors/NVIDIA/Example_Rotary_2D.usda"
        )
        update_lidar_menu_item_with_usd_path(
            "NVIDIA", "Example Rotary Beams", "/Isaac/Sensors/NVIDIA/Example_Rotary_BEAMS.usda"
        )
        update_lidar_menu_item_with_usd_path("NVIDIA", "Example Rotary", "/Isaac/Sensors/NVIDIA/Example_Rotary.usda")
        update_lidar_menu_item_with_usd_path(
            "NVIDIA", "Example Solid State", "/Isaac/Sensors/NVIDIA/Example_Solid_State.usda"
        )
        update_lidar_menu_item_with_usd_path(
            "NVIDIA", "Simple Example Solid State", "/Isaac/Sensors/NVIDIA/Simple_Example_Solid_State.usda"
        )
        update_lidar_menu_item_with_usd_path("SICK", "SICK microscan3 official", "/Isaac/Sensors/SICK/microScan3.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK multiScan136", "/Isaac/Sensors/SICK/multiScan136.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK multiScan165", "/Isaac/Sensors/SICK/multiScan165.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK picoScan150", "/Isaac/Sensors/SICK/picoScan150.usd")
        update_lidar_menu_item_with_usd_path("SICK", "SICK TiM781", "/Isaac/Sensors/SICK/tim781.usd")
        update_lidar_menu_item_with_usd_path("SLAMTEC", "RPLIDAR S2E", "/Isaac/Sensors/Slamtec/RPLidar_S2e.usd")
        update_lidar_menu_item_with_usd_path(
            "Velodyne", "Velodyne VLS 128", "/Isaac/Sensors/Velodyne/vls-128/vls_128.usd"
        )
        update_lidar_menu_item_with_usd_path("SLAMTEC", "RPLIDAR S2E", "/Isaac/Sensors/Slamtec/RPLidar_S2e.usd")
        update_lidar_menu_item_with_usd_path("ZVISION", "ZVISION ML305", "/Isaac/Sensors/ZVISION/ZVISION_ML30S.usda")
        update_lidar_menu_item_with_usd_path("ZVISION", "ZVISION MLXS", "/Isaac/Sensors/ZVISION/ZVISION_MLXS.usda")

        # Build Ouster Lidar Menu separately since it contains further submenus
        ouster_lidar_menu = []
        for ouster_lidar in SUPPORTED_VARIANTS_OUSTER:
            # Retrieve path to main Ouster lidar USD, for each Ouster lidar type
            ouster_lidar_path = get_assets_root_path() + f"/Isaac/Sensors/Ouster/{ouster_lidar}"
            result, _ = omni.client.list(ouster_lidar_path)

            if not result:
                carb.log_error(f"Unable to find {ouster_lidar_path}")
                continue

            file = ouster_lidar_path + f"/{ouster_lidar}.usd"

            # Iterate over Ouster lidar variants, creating a menu item for each
            ouster_lidar_sub_menu = []
            for variant in SUPPORTED_VARIANTS_OUSTER[ouster_lidar]:
                ui_name = ouster_lidar + " " + variant
                ouster_lidar_sub_menu.append(
                    make_menu_item_description(
                        ext_id,
                        ui_name,
                        lambda a=weakref.proxy(
                            self
                        ), name=ui_name, asset_path=file, visibility=True, variant=variant: a._add_rtx_lidar(
                            name, asset_path, variant, visibility
                        ),
                    )
                )
            ouster_lidar_menu.append(MenuItemDescription(name=ouster_lidar, sub_menu=ouster_lidar_sub_menu))

        rtx_lidar_sub_menu_as_list = []
        for name in rtx_lidar_sub_menu:
            if name == "OUSTER":
                rtx_lidar_sub_menu_as_list.append(MenuItemDescription(name="Ouster", sub_menu=ouster_lidar_menu))
            else:
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

    def _add_rtx_lidar(self, name, asset_path, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path="/" + Tf.MakeValidIdentifier(name),
            parent=self._get_stage_and_path(),
            asset_path=asset_path,
            translation=Gf.Vec3d(0, 0, 0),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
        )
        if result:
            # Make lidar invisible on stage
            set_prim_visibility(prim=prim, visible=False)
