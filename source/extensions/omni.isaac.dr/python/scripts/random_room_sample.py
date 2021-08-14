# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.usd
import weakref
from omni.isaac.utils.scripts.nucleus_utils import get_server_path


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._asset_path = None
        self._window = ui.Window("Simple Room Python Sample", width=600, height=400)
        self._window.visible = False
        self._window.deferred_dock_in("Console")

        menu_items = [
            MenuItemDescription(
                name="Simple Room (Python)", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
            )
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Domain Randomization", sub_menu=[MenuItemDescription(name="Samples", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Synthetic Data")
        with self._window.frame:
            with ui.VStack(height=0):
                ui.Spacer(width=5)
                load_stage_btn = ui.Button("Load Stage", width=100)
                load_stage_btn.set_clicked_fn(self._on_load_stage)
                load_comp_btn = ui.Button("Load DR Component", width=100)
                load_comp_btn.set_clicked_fn(self._on_load_component)

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Synthetic Data")
        self._window = None
        self._usd_context = None
        self._stage = None

    def _on_load_stage(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return
        omni.usd.get_context().open_stage(self._asset_path + "/Environments/Simple_Room/simple_room.usd", None)

    def _on_load_component(self):
        """Creates DR components with various attributes
        """
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return
        # List of textures to randomize from
        texture_list = [
            self._asset_path + "/Samples/DR/Materials/Textures/checkered.png",
            self._asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
            self._asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
            self._asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
            self._asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
        ]

        # Some prim paths to used for randomization
        simple_room_prim_path = "/Root"
        light_prim_path = "/Root/RectLight"
        table_prim_path = "/Root/table_low_327"
        floor_prim_path = "/Root/Towel_Room01_floor_bottom_218"

        # Create DR texture component
        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            prim_paths=[simple_room_prim_path],
            enable_project_uvw=False,
            texture_list=texture_list,
            ignored_class_list=["floor_bottom"],
            grouped_class_list=[],
            duration=1.0,
            include_children=True,
        )
        # Create DR color component
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            prim_paths=[floor_prim_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=1.0,
            include_children=False,
        )
        # Create DR movement component
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(-50.0, -50.0, -77),
            max_range=(50.0, 50.0, -77),
            target_position=None,
            target_paths=None,
            duration=1.0,
            include_children=False,
        )
        # Create DR rotation component
        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(0.0, 0.0, 360.0),
            duration=1.0,
            include_children=False,
        )
        # Create DR scale component
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            prim_paths=[table_prim_path],
            min_range=(0.4, 0.4, 0.4),
            max_range=(1.3, 1.3, 1.3),
            uniform_scaling=True,
            duration=1.0,
            include_children=False,
        )
        # Create DR light component
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            light_paths=[light_prim_path],
            first_color_range=(0.9, 0.9, 0.9),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(1500.0, 6500.0),
            enable_temperature=True,
            duration=1.0,
            include_children=False,
        )
