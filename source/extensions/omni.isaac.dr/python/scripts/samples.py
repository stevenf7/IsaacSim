import asyncio
import os
import carb
import carb.tokens
import omni.kit
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.usd
import weakref
from .nucleus_utils import get_server_path

from pxr import UsdGeom


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._asset_path = None

        menu_items = [
            MenuItemDescription(
                name="Component Sample", onclick_fn=lambda a=weakref.proxy(self): a.add_component_sample()
            ),
            MenuItemDescription(
                name="Simple Room Sample", onclick_fn=lambda a=weakref.proxy(self): a.add_simple_room_scene()
            ),
            MenuItemDescription(
                name="Warehouse Sample", onclick_fn=lambda a=weakref.proxy(self): a.add_warehouse_scene()
            ),
        ]

        self._menu_items = [MenuItemDescription(name="Domain Randomizer", sub_menu=menu_items)]
        add_menu_items(self._menu_items, "Isaac")

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
        remove_menu_items(self._menu_items, "Isaac")
        self._window = None
        self._usd_context = None
        self._stage = None

    def _on_clear_stage(self):
        omni.usd.get_context().close_stage_with_callback(lambda a, b: omni.usd.get_context().new_stage(None))

    def _on_load_stage(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return

        current_scenario_index = self._selected_scenario.model.get_item_value_model().as_int
        stage_path = self._asset_path + "/Samples/DR/Props/simple_cube_with_light.usd"
        if current_scenario_index == 7:
            stage_path = self._asset_path + "/Samples/DR/Props/only_light.usd"
        elif current_scenario_index == 8:
            stage_path = self._asset_path + "/Samples/DR/Props/multiple_cubes_with_light.usd"
        omni.usd.get_context().close_stage_with_callback(
            lambda a, b: omni.usd.get_context().open_stage(stage_path, None)
        )

    def _on_load_component(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return

        current_scenario_index = self._selected_scenario.model.get_item_value_model().as_int
        if current_scenario_index == 0:
            self.add_color_menu()
        elif current_scenario_index == 1:
            self.add_movement_menu()
        elif current_scenario_index == 2:
            self.add_rotation_menu()
        elif current_scenario_index == 3:
            self.add_scale_menu()
        elif current_scenario_index == 4:
            self.add_light_menu()
        elif current_scenario_index == 5:
            self.add_texture_menu()
        elif current_scenario_index == 6:
            self.add_material_menu()
        elif current_scenario_index == 7:
            self.add_mesh_menu()
        elif current_scenario_index == 8:
            self.add_visibility_menu()

    def add_color_menu(self):
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

    def add_movement_menu(self):
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

    def add_rotation_menu(self):
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

    def add_scale_menu(self):
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

    def add_light_menu(self):
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

    def add_texture_menu(self):
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

    def add_material_menu(self):
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

    def add_mesh_menu(self):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        # Create DR mesh component
        path = omni.usd.get_stage_next_free_path(stage, default_prim_path + "/mesh_component", False)
        result, prim = omni.kit.commands.execute(
            "CreateMeshComponentCommand",
            mesh_list=[
                self._asset_path + "/Props/Blocks/nvidia_cube.usd",
                self._asset_path + "/Props/Rubiks_Cube/rubiks_cube.usd",
            ],
            mesh_range=[3, 5],
            seed=12345,
        )

    def add_visibility_menu(self):
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

    def add_simple_room_scene(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return
        omni.usd.get_context().close_stage_with_callback(
            lambda a, b: omni.usd.get_context().open_stage(
                self._asset_path + "/Samples/DR/Stage/simple_room_sample.usda", None
            )
        )

    def add_warehouse_scene(self):
        if self._asset_path is None:
            self._asset_path = get_server_path("/Isaac")
        if self._asset_path is None:
            return
        omni.usd.get_context().close_stage_with_callback(
            lambda a, b: omni.usd.get_context().open_stage(
                self._asset_path + "/Samples/DR/Stage/simple_warehouse_material_sample.usda", None
            )
        )
