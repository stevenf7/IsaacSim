# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
Support required by the Carbonite extension loader
"""
import gc

import omni.ext
import omni.kit.commands
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items

from .menu_graphs import ArticulationPositionGraph, ArticulationVelocityGraph, GripperGraph


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        controller_menu = [
            make_menu_item_description(
                ext_id, "Articulation Position Controller", onclick_fun=self._open_articulation_position
            ),
            make_menu_item_description(
                ext_id, "Articulation Velocity Controller", onclick_fun=self._open_articulation_velocity
            ),
            make_menu_item_description(ext_id, "Gripper Controller", onclick_fun=self._open_gripper_graph),
        ]
        self._menu_controller = [
            MenuItemDescription(
                name="Common Omnigraphs",
                sub_menu=controller_menu,
            )
        ]
        add_menu_items(self._menu_controller, "Isaac Utils")

    def on_shutdown(self):
        remove_menu_items(self._menu_controller, "Isaac Utils")
        gc.collect()

    def _open_articulation_position(self):
        ArticulationPositionGraph().create_articulation_controller_graph()

    def _open_articulation_velocity(self):
        ArticulationVelocityGraph().create_articulation_controller_graph()

    def _open_gripper_graph(self):
        GripperGraph().create_gripper_controller_graph()
