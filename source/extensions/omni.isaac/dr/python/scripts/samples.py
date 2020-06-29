import asyncio
import os
import carb.tokens
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.kit.asyncapi
import omni.usd

from pxr import Gf, Usd, UsdGeom, Sdf

ADD_COMPONENT_SAMPLE_MENU = "Isaac Robotics/Domain Randomizer/Component Sample"
ADD_SIMPLE_ROOM_SAMPLE_MENU = "Isaac Robotics/Domain Randomizer/Simple Room Sample"
ADD_WAREHOUSE_SAMPLE_MENU = "Isaac Robotics/Domain Randomizer/Warehouse Sample"


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()

        self._window = omni.kit.ui.Window(
            "Domain Randomizer Component Samples",
            300,
            200,
            menu_path=ADD_COMPONENT_SAMPLE_MENU,
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )

        self._menus = []
        editor_menu = omni.kit.ui.get_editor_menu()
        self._menus.append(editor_menu.add_item(ADD_SIMPLE_ROOM_SAMPLE_MENU, self._on_dr_sample_menu_click))
        self._menus.append(editor_menu.add_item(ADD_WAREHOUSE_SAMPLE_MENU, self._on_dr_sample_menu_click))

        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())
        self._selected_scenario = sublayout.add_child(omni.kit.ui.ComboBox())
        self._selected_scenario.add_item("Color")
        self._selected_scenario.add_item("Movement")
        self._selected_scenario.add_item("Rotation")
        self._selected_scenario.add_item("Scale")
        self._selected_scenario.add_item("Light")
        self._selected_scenario.add_item("Texture")
        self._selected_scenario.add_item("Material")
        self._selected_scenario.selected_index = 0
        clear_stage_btn = sublayout.add_child(omni.kit.ui.Button("Clear Stage"))
        clear_stage_btn.set_clicked_fn(self._on_clear_stage)
        load_stage_btn = sublayout.add_child(omni.kit.ui.Button("Load Stage"))
        load_stage_btn.set_clicked_fn(self._on_load_stage)
        load_comp_btn = sublayout.add_child(omni.kit.ui.Button("Load DR Component"))
        load_comp_btn.set_clicked_fn(self._on_load_component)

    def on_shutdown(self):
        self.menus = []
        self._editor = None
        self._window = None
        self._usd_context = None
        self._stage = None

    def _on_clear_stage(self, widget):
        omni.usd.get_context().new_stage(None)

    def _on_load_stage(self, widget):
        omni.usd.get_context().open_stage(
            "omniverse://ov-isaac-dev/Isaac/Samples/DR/Props/simple_cube_with_light.usd", None
        )

    def _on_load_component(self, widget):
        if self._selected_scenario.selected_index == 0:
            self.add_color_menu()
        elif self._selected_scenario.selected_index == 1:
            self.add_movement_menu()
        elif self._selected_scenario.selected_index == 2:
            self.add_rotation_menu()
        elif self._selected_scenario.selected_index == 3:
            self.add_scale_menu()
        elif self._selected_scenario.selected_index == 4:
            self.add_light_menu()
        elif self._selected_scenario.selected_index == 5:
            self.add_texture_menu()
        elif self._selected_scenario.selected_index == 6:
            self.add_material_menu()

    def add_color_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR color component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/color_component", False)
        prim = DrSchema.ColorComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("color_component"))
        # Set attributes for DR color component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateRoughnessAttr().Set((float(0.0), float(1.0)))
        prim.CreateMetallicAttr().Set((float(0.0), float(1.0)))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_movement_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR movement component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/movement_component", False)
        prim = DrSchema.MovementComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("movement_component"))
        mov_comp_path = default_prim_path + "/movement_component"
        mov_comp = stage.GetPrimAtPath(mov_comp_path)
        # Set attributes for DR movement component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(100.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(100.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(100.0)))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_rotation_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR rotation component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/rotation_component", False)
        prim = DrSchema.RotationComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("rotation_component"))
        rot_comp_path = default_prim_path + "/rotation_component"
        rot_comp = stage.GetPrimAtPath(rot_comp_path)
        # Set attributes for DR rotation component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_scale_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR scale component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/scale_component", False)
        prim = DrSchema.ScaleComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("scale_component"))
        scale_comp_path = default_prim_path + "/scale_component"
        scale_comp = stage.GetPrimAtPath(scale_comp_path)
        # Set attributes for DR scale component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateXRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(5.0)))
        prim.CreateEnableUniformAttr().Set(bool(False))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_light_menu(self, parent=None):
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
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/light_component", False)
        prim = DrSchema.LightComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set("light_component")
        light_comp_path = default_prim_path + "/light_component"
        light_comp = stage.GetPrimAtPath(light_comp_path)
        # Set attributes for DR light component
        prim.CreatePrimPathsRel().AddTarget(light_path)
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateIntensityRangeAttr().Set((float(40000.0), float(70000.0)))
        prim.CreateTemperatureRangeAttr().Set((float(1500.0), float(6500.0)))
        prim.CreateEnableTemperatureAttr().Set(bool(True))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_texture_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR texture component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/texture_component", False)
        prim = DrSchema.TextureComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("texture_component"))
        tex_comp_path = default_prim_path + "/texture_component"
        tex_comp = stage.GetPrimAtPath(tex_comp_path)
        # Set attributes for DR texture component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateTextureListAttr().Set(
            str(
                "omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/checkered.png,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/marble_tile.png,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/picture_a.png,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/picture_b.png,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/textured_wall.png,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/Textures/checkered_color.png"
            )
        )
        prim.CreateIgnoredClassAttr().Set(str(""))
        prim.CreateGroupedClassAttr().Set(str(""))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_material_menu(self, parent=None):
        stage = omni.usd.get_context().get_stage()
        default_prim_path = str(stage.GetDefaultPrim().GetPath())
        cube_path = default_prim_path + "/Cube"
        # Create DR material component
        path = omni.kit.utils.get_stage_next_free_path(stage, default_prim_path + "/material_component", False)
        prim = DrSchema.MaterialComponent.Define(stage, Sdf.Path(path))
        prim.CreateCompNameAttr().Set(str("material_component"))
        tex_comp_path = default_prim_path + "/material_component"
        tex_comp = stage.GetPrimAtPath(tex_comp_path)
        # Set attributes for DR material component
        prim.CreatePrimPathsRel().AddTarget(cube_path)
        prim.CreateMaterialListAttr().Set(
            str(
                "omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/checkered.mdl,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/checkered_color.mdl,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/marble_tile.mdl,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/picture_a.mdl,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/picture_b.mdl,omniverse://ov-isaac-dev/Isaac/Samples/DR/Materials/textured_wall.mdl"
            )
        )
        prim.CreateIgnoredClassAttr().Set(str(""))
        prim.CreateGroupedClassAttr().Set(str(""))
        prim.CreateDurationAttr().Set(float(0.3))
        prim.CreateIncludeChildrenAttr().Set(bool(False))

    def add_simple_room_scene(self, parent=None):
        omni.usd.get_context().open_stage(
            "omniverse://ov-isaac-dev/Isaac/Samples/DR/Stage/simple_room_sample.usda", None
        )

    def add_warehouse_scene(self, parent=None):
        omni.usd.get_context().open_stage(
            "omniverse://ov-isaac-dev/Isaac/Samples/DR/Stage/simple_warehouse_material_sample.usda", None
        )

    def _on_dr_sample_menu_click(self, menu, value):
        self._stage = self._usd_context.get_stage()

        if menu == ADD_SIMPLE_ROOM_SAMPLE_MENU:
            self.add_simple_room_scene()
        if menu == ADD_WAREHOUSE_SAMPLE_MENU:
            self.add_warehouse_scene()
