# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import carb.tokens
import omni.kit
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.usd
import weakref
from omni.isaac.core.utils.nucleus import get_server_path
from omni.isaac.core.utils.stage import add_reference_to_stage, is_stage_loading

from pxr import UsdGeom


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._asset_path = None

        menu_items = [
            MenuItemDescription(
                name="Component Randomizer", onclick_fn=lambda a=weakref.proxy(self): a.add_component_sample()
            ),
            MenuItemDescription(name="Simple Room", onclick_fn=lambda a=weakref.proxy(self): a.add_simple_room_scene()),
            MenuItemDescription(name="Warehouse", onclick_fn=lambda a=weakref.proxy(self): a.add_warehouse_scene()),
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Domain Randomization", sub_menu=[MenuItemDescription(name="Samples", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Synthetic Data")

    def add_component_sample(self):
        self._window = ui.Window(
            "Domain Randomizer Component Samples", dockPreference=omni.ui.DockPreference.LEFT_BOTTOM
        )

        with self._window.frame:
            with ui.VStack(spacing=5):
                self._selected_scenario = ui.ComboBox(
                    0,
                    "Color",
                    "Movement",
                    "Rotation",
                    "Scale",
                    "Light",
                    "Texture",
                    "Material",
                    "Mesh",
                    "Visibility",
                    "Transform",
                    "Attribute",
                    height=0,
                    width=200,
                )
                clear_stage_btn = ui.Button("Clear Stage", height=30, width=100)
                clear_stage_btn.set_clicked_fn(self._on_clear_stage)
                load_stage_btn = ui.Button("Load Stage", height=30, width=100)
                load_stage_btn.set_clicked_fn(self._on_load_stage)
                load_comp_btn = ui.Button("Load DR Component", height=30, width=100)
                load_comp_btn.set_clicked_fn(self._on_load_component)

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Synthetic Data")
        self._window = None
        self._usd_context = None
        self._stage = None

    def _on_clear_stage(self):
        async def clear_stage():
            while is_stage_loading():
                await omni.kit.app.get_app().next_update_async()
            await omni.usd.get_context().new_stage_async()
            await omni.kit.app.get_app().next_update_async()

        asyncio.ensure_future(clear_stage())

    async def load_stage(self, path):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return
        await omni.kit.app.get_app().next_update_async()
        add_reference_to_stage(usd_path=self._asset_path + path, prim_path="/World")
        await omni.kit.app.get_app().next_update_async()

    def _on_load_stage(self):

        current_scenario_index = self._selected_scenario.model.get_item_value_model().as_int
        path = "/Samples/DR/Props/simple_cube_with_light.usd"
        if current_scenario_index == 7:
            path = "/Samples/DR/Props/only_light.usd"
        elif current_scenario_index == 8:
            path = "/Samples/DR/Props/multiple_cubes_with_light.usd"

        asyncio.ensure_future(self.load_stage(path))

    def _on_load_component(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return

        current_scenario_index = self._selected_scenario.model.get_item_value_model().as_int
        if current_scenario_index == 0:
            asyncio.ensure_future(self.add_color_menu())
        elif current_scenario_index == 1:
            asyncio.ensure_future(self.add_movement_menu())
        elif current_scenario_index == 2:
            asyncio.ensure_future(self.add_rotation_menu())
        elif current_scenario_index == 3:
            asyncio.ensure_future(self.add_scale_menu())
        elif current_scenario_index == 4:
            asyncio.ensure_future(self.add_light_menu())
        elif current_scenario_index == 5:
            asyncio.ensure_future(self.add_texture_menu())
        elif current_scenario_index == 6:
            asyncio.ensure_future(self.add_material_menu())
        elif current_scenario_index == 7:
            asyncio.ensure_future(self.add_mesh_menu())
        elif current_scenario_index == 8:
            asyncio.ensure_future(self.add_visibility_menu())
        elif current_scenario_index == 9:
            asyncio.ensure_future(self.add_transform_menu())
        elif current_scenario_index == 10:
            asyncio.ensure_future(self.add_attribute_menu())

    async def add_color_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR color component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateColorComponentCommand",
            path=path,
            prim_paths=[cube_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            roughness_range=(0.0, 1.0),
            metallic_range=(0.0, 1.0),
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_movement_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR movement component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/movement_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMovementComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(100.0, 100.0, 100.0),
            target_position=None,
            target_paths=None,
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_rotation_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR rotation component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/rotation_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateRotationComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.0, 0.0, 0.0),
            max_range=(360.0, 360.0, 360.0),
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_scale_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR scale component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateScaleComponentCommand",
            path=path,
            prim_paths=[cube_path],
            min_range=(0.5, 0.5, 0.5),
            max_range=(5.0, 5.0, 5.0),
            uniform_scaling=False,
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_light_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        light_path = default_prim_path + "/RectLight"
        # Disable default light
        deflightPrim = stage.GetPrimAtPath(default_prim_path + "/defaultLight")
        imageable = UsdGeom.Imageable(deflightPrim)
        if imageable:
            imageable.MakeInvisible()
        # Create DR light component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateLightComponentCommand",
            path=path,
            light_paths=[light_path],
            first_color_range=(0.0, 0.0, 0.0),
            second_color_range=(1.0, 1.0, 1.0),
            intensity_range=(40000.0, 70000.0),
            temperature_range=(1500.0, 6500.0),
            enable_temperature=True,
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_texture_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR texture component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateTextureComponentCommand",
            path=path,
            prim_paths=[cube_path],
            enable_project_uvw=False,
            texture_list=[
                self._asset_path + "/Samples/DR/Materials/Textures/checkered.png",
                self._asset_path + "/Samples/DR/Materials/Textures/marble_tile.png",
                self._asset_path + "/Samples/DR/Materials/Textures/picture_a.png",
                self._asset_path + "/Samples/DR/Materials/Textures/picture_b.png",
                self._asset_path + "/Samples/DR/Materials/Textures/textured_wall.png",
                self._asset_path + "/Samples/DR/Materials/Textures/checkered_color.png",
            ],
            ignored_class_list=[],
            grouped_class_list=[],
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_material_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR material component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/material_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMaterialComponentCommand",
            path=path,
            prim_paths=[cube_path],
            material_list=[
                self._asset_path + "/Samples/DR/Materials/checkered.mdl",
                self._asset_path + "/Samples/DR/Materials/checkered_color.mdl",
                self._asset_path + "/Samples/DR/Materials/marble_tile.mdl",
                self._asset_path + "/Samples/DR/Materials/picture_a.mdl",
                self._asset_path + "/Samples/DR/Materials/picture_b.mdl",
                self._asset_path + "/Samples/DR/Materials/textured_wall.mdl",
            ],
            ignored_class_list=[],
            grouped_class_list=[],
            loaded_material_paths=[],
            duration=0.3,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_mesh_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        # Create DR mesh component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            parent_prim=["/World"],
            mesh_list=[
                self._asset_path + "/Props/Blocks/nvidia_cube.usd",
                self._asset_path + "/Props/Rubiks_Cube/rubiks_cube.usd",
            ],
            mesh_range=[3, 5],
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_visibility_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        # Create DR visibility component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/visibility_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateVisibilityComponentCommand",
            prim_paths=["/World/Cube", "/World/Cube_01", "/World/Cube_02", "/World/Cube_03", "/World/Cube_04"],
            num_visible_range=[1, 3],
            duration=0.3,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_transform_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR transform component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/transform_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateTransformComponentCommand",
            path=path,
            prim_paths=[cube_path],
            translate_min_range=(0.0, 0.0, 0.0),
            translate_max_range=(100.0, 100.0, 100.0),
            rotate_min_range=(0.0, 0.0, 0.0),
            rotate_max_range=(360.0, 360.0, 360.0),
            scale_min_range=(1.0, 1.0, 1.0),
            scale_max_range=(2.0, 2.0, 2.0),
            target_position=None,
            target_paths=None,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    async def add_attribute_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR attribute component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/attribute_component", False)
        attribute_dict = {
            "attribute_3": {"name": "xformOp:rotateXYZ", "min": "0.0", "max": "360.0", "distribution": "uniform"},
            "attribute_1": {"name": "xformOp:translate", "min": "1.0", "max": "50.0", "distribution": "uniform"},
        }
        result, prim = omni.kit.commands.execute(
            "CreateAttributeComponentCommand",
            path=path,
            prim_paths=[cube_path],
            custom_data=attribute_dict,
            duration=1.0,
            include_children=False,
            seed=12345,
        )
        await omni.kit.app.get_app().next_update_async()

    def add_simple_room_scene(self):
        asyncio.ensure_future(self.load_stage("/Samples/DR/Stage/simple_room_sample.usd"))

    def add_warehouse_scene(self):
        asyncio.ensure_future(self.load_stage("/Samples/DR/Stage/simple_warehouse_material_sample.usd"))
