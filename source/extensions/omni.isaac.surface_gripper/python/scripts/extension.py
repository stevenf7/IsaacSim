# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ext
import omni.ui as ui
import gc
import carb
import omni.kit.commands
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from pxr import Sdf, UsdGeom, Gf
import weakref


class Extension(omni.ext.IExt):
    def __init__(self) -> None:
        menu_items = [
            MenuItemDescription(
                name="End Effectors",
                sub_menu=[
                    MenuItemDescription(header="Grippers"),
                    MenuItemDescription(name="Surface Gripper", onclick_fn=lambda a=weakref.proxy(self): a._add_sgn()),
                ],
            )
        ]

        self._menu_items = [MenuItemDescription(name="Isaac", glyph="plug.svg", sub_menu=menu_items)]

        add_menu_items(self._menu_items, "Create")

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        gc.collect()

    def _add_sgn(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute("CreateSurfaceGripper")
