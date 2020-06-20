from pxr import Gf, Usd, UsdGeom, Sdf
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.kit.ui
import omni.usd

ADD_COLOR_DR_MENU_ITEM = "Create/Isaac/DR/Color Component"
ADD_MOVEMENT_DR_MENU_ITEM = "Create/Isaac/DR/Movement Component"
ADD_ROTATION_DR_MENU_ITEM = "Create/Isaac/DR/Rotation Component"
ADD_SCALE_DR_MENU_ITEM = "Create/Isaac/DR/Scale Component"
ADD_LIGHT_DR_MENU_ITEM = "Create/Isaac/DR/Light Component"
ADD_TEXTURE_DR_MENU_ITEM = "Create/Isaac/DR/Texture Component"
ADD_MATERIAL_DR_MENU_ITEM = "Create/Isaac/DR/Material Component"
ADD_MESH_DR_MENU_ITEM = "Create/Isaac/DR/Mesh Component"


class DRMenu:
    def __init__(self, domain_randomizer_interface):
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._layers = self._usd_context.get_layers()
        self._window = omni.kit.ui.Window("Domain Randomizer", 960, 600)
        self._dr = domain_randomizer_interface
        self.texture_layer_index = -1
        self.texture_component_count = 0
        self.num_components = 8

        self._menus = []
        editor_menu = omni.kit.ui.get_editor_menu()
        self._menus.append(editor_menu.add_item(ADD_COLOR_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_MOVEMENT_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROTATION_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCALE_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_LIGHT_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_TEXTURE_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_MATERIAL_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_MESH_DR_MENU_ITEM, self._on_dr_menu_click))

    def add_color_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/color_component_" + str(self.component_count[0]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/color_component_" + str(self.component_count[0]), True
            )

        prim = DrSchema.ColorComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("color_component_" + str(self.component_count[0])))
        prim.CreatePrimPathsRel()
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_movement_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/movement_component_" + str(self.component_count[1]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/movement_component_" + str(self.component_count[1]), True
            )

        prim = DrSchema.MovementComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("movement_component_" + str(self.component_count[1])))
        prim.CreatePrimPathsRel()
        prim.CreateXRangeAttr().Set((float(0.0), float(0.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(0.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(0.0)))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_rotation_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/rotation_component_" + str(self.component_count[5]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/rotation_component_" + str(self.component_count[5]), True
            )

        prim = DrSchema.RotationComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("rotation_component_" + str(self.component_count[5])))
        prim.CreatePrimPathsRel()
        prim.CreateXRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(360.0)))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_scale_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/scale_component_" + str(self.component_count[2]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/scale_component_" + str(self.component_count[2]), True
            )

        prim = DrSchema.ScaleComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("scale_component_" + str(self.component_count[2])))
        prim.CreatePrimPathsRel()
        prim.CreateXRangeAttr().Set((float(1.0), float(1.0)))
        prim.CreateYRangeAttr().Set((float(1.0), float(1.0)))
        prim.CreateZRangeAttr().Set((float(1.0), float(1.0)))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_light_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/light_component_" + str(self.component_count[3]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/light_component_" + str(self.component_count[3]), True
            )

        prim = DrSchema.LightComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("light_component_" + str(self.component_count[3])))
        prim.CreatePrimPathsRel()
        prim.CreateFirstColorAttr().Set((float(0.0), float(0.0), float(0.0)))
        prim.CreateSecondColorAttr().Set((float(1.0), float(1.0), float(1.0)))
        prim.CreateIntensityRangeAttr().Set((float(40000.0), float(70000.0)))
        prim.CreateTemperatureRangeAttr().Set((float(6500.0), float(6500.0)))
        prim.CreateEnableTemperatureAttr().Set(bool(False))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_texture_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/texture_component_" + str(self.component_count[4]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/texture_component_" + str(self.component_count[4]), True
            )

        prim = DrSchema.TextureComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("texture_component_" + str(self.component_count[4])))
        prim.CreatePrimPathsRel()
        prim.CreateTextureListAttr().Set(str(""))
        prim.CreateIgnoredClassAttr().Set(str(""))
        prim.CreateGroupedClassAttr().Set(str(""))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_material_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/material_component_" + str(self.component_count[6]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/material_component_" + str(self.component_count[6]), True
            )

        prim = DrSchema.MaterialComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("material_component_" + str(self.component_count[6])))
        prim.CreatePrimPathsRel()
        prim.CreateMaterialListAttr().Set(str(""))
        prim.CreateIgnoredClassAttr().Set(str(""))
        prim.CreateGroupedClassAttr().Set(str(""))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def add_mesh_menu(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, parent + "/mesh_component_" + str(self.component_count[6]), False
            )
        else:
            path = omni.kit.utils.get_stage_next_free_path(
                self._stage, "/mesh_component_" + str(self.component_count[6]), True
            )

        prim = DrSchema.MeshComponent.Define(self._stage, Sdf.Path(path))

        prim.CreateCompNameAttr().Set(str("mesh_component_" + str(self.component_count[6])))
        prim.CreatePrimPathsRel()
        prim.CreateMeshListAttr().Set(str(""))
        prim.CreateNumMeshRangeAttr().Set(Gf.Vec2i(1, 1))
        prim.CreateDurationAttr().Set(float(1.0))
        prim.CreateIncludeChildrenAttr().Set(bool(False))
        pass

    def _on_dr_menu_click(self, menu, value):
        self._stage = self._usd_context.get_stage()
        self.component_count = [0] * self.num_components
        for child_prim in self._stage.Traverse():
            if child_prim.GetTypeName() == "ColorComponent":
                self.component_count[0] = self.component_count[0] + 1
            if child_prim.GetTypeName() == "MovementComponent":
                self.component_count[1] = self.component_count[1] + 1
            if child_prim.GetTypeName() == "ScaleComponent":
                self.component_count[2] = self.component_count[2] + 1
            if child_prim.GetTypeName() == "LightComponent":
                self.component_count[3] = self.component_count[3] + 1
            if child_prim.GetTypeName() == "TextureComponent":
                self.component_count[4] = self.component_count[4] + 1
            if child_prim.GetTypeName() == "RotationComponent":
                self.component_count[5] = self.component_count[5] + 1
            if child_prim.GetTypeName() == "MaterialComponent":
                self.component_count[6] = self.component_count[6] + 1
            if child_prim.GetTypeName() == "MeshComponent":
                self.component_count[7] = self.component_count[7] + 1

        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()
        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None

        if menu == ADD_COLOR_DR_MENU_ITEM:
            self.add_color_menu(curr_prim)
        if menu == ADD_MOVEMENT_DR_MENU_ITEM:
            self.add_movement_menu(curr_prim)
        if menu == ADD_ROTATION_DR_MENU_ITEM:
            self.add_rotation_menu(curr_prim)
        if menu == ADD_SCALE_DR_MENU_ITEM:
            self.add_scale_menu(curr_prim)
        if menu == ADD_LIGHT_DR_MENU_ITEM:
            self.add_light_menu(curr_prim)
        if menu == ADD_TEXTURE_DR_MENU_ITEM:
            self.add_texture_menu(curr_prim)
        if menu == ADD_MATERIAL_DR_MENU_ITEM:
            self.add_material_menu(curr_prim)
        if menu == ADD_MESH_DR_MENU_ITEM:
            self.add_mesh_menu(curr_prim)

    def _build_dr_ui(self):
        title = "Manual Mode"
        layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(layout_collapsing)

        manual_layout = omni.kit.ui.RowColumnLayout(2, True)
        layout_collapsing.add_child(manual_layout)
        manual_layout.set_column_width(0, 150)
        manual_layout.set_column_width(1, 150)

        self.btn_manual_comp = omni.kit.ui.Button("Enable Manual Mode")
        self.btn_manual_comp.set_clicked_fn(self._toggle_manual_mode)
        manual_layout.add_child(self.btn_manual_comp)

        self.btn_randomize_once = omni.kit.ui.Button("Randomize Once")
        self.btn_randomize_once.set_clicked_fn(self._randomize_once)
        manual_layout.add_child(self.btn_randomize_once)

    def _toggle_manual_mode(self, value):
        if str(self.btn_manual_comp.text) == "Enable Manual Mode":
            self.btn_manual_comp.text = "Disable Manual Mode"
        else:
            self.btn_manual_comp.text = "Enable Manual Mode"
        self._dr.toggle_manual_mode()

    def _randomize_once(self, value):
        self._dr.randomize_once()

    def shutdown(self):
        self._menus = None
        self._window.set_update_fn(None)
        del self._window
