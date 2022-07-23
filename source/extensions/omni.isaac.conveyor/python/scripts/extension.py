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
from ..bindings._omni_isaac_conveyor import acquire_interface as _acquire
from ..bindings._omni_isaac_conveyor import release_interface as _release


class Extension(omni.ext.IExt):
    def __init__(self) -> None:
        menu_items = [
            MenuItemDescription(
                name="Warehouse Items",
                sub_menu=[
                    MenuItemDescription(name="Conveyor", onclick_fn=lambda a=weakref.proxy(self): a._add_conveyor())
                ],
            )
        ]

        self._menu_items = [MenuItemDescription(name="Isaac", glyph="plug.svg", sub_menu=menu_items)]

        add_menu_items(self._menu_items, "Create")

    def on_startup(self):
        self.__interface = _acquire()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        _release(self.__interface)
        self.__interface = None
        gc.collect()

    def _add_conveyor(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute("CreateConveyorBelt")
