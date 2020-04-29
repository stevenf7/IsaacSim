from pxr import Gf, Usd, UsdGeom, Sdf
import asyncio
import json
import omni.isaac.DrSchema as DrSchema
import omni.kit
import omni.kit.ui
import omni.usd
import os
import random

ADD_COLOR_DR_MENU_ITEM = "Create/Isaac/DR/Color Component"
ADD_MOVEMENT_DR_MENU_ITEM = "Create/Isaac/DR/Movement Component"
ADD_ROTATION_DR_MENU_ITEM = "Create/Isaac/DR/Rotation Component"
ADD_SCALE_DR_MENU_ITEM = "Create/Isaac/DR/Scale Component"
ADD_LIGHT_DR_MENU_ITEM = "Create/Isaac/DR/Light Component"
ADD_TEXTURE_DR_MENU_ITEM = "Create/Isaac/DR/Texture Component"


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
        self.num_components = 6

        self._menus = []
        editor_menu = omni.kit.ui.get_editor_menu()
        self._menus.append(editor_menu.add_item(ADD_COLOR_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_MOVEMENT_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROTATION_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCALE_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_LIGHT_DR_MENU_ITEM, self._on_dr_menu_click))
        self._menus.append(editor_menu.add_item(ADD_TEXTURE_DR_MENU_ITEM, self._on_dr_menu_click))

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
        prim.CreateXRangeAttr().Set((float(0.0), float(0.0)))
        prim.CreateYRangeAttr().Set((float(0.0), float(0.0)))
        prim.CreateZRangeAttr().Set((float(0.0), float(0.0)))
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

    def _build_dr_ui(self):
        title = "Domain Randomizer"
        layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(layout_collapsing)

        usd_layout = omni.kit.ui.RowColumnLayout(3, True)
        layout_collapsing.add_child(usd_layout)
        usd_layout.set_column_width(0, 150)
        usd_layout.set_column_width(1, 150)
        usd_layout.set_column_width(2, 150)

        usd_label = omni.kit.ui.Label("Load from USD")
        usd_layout.add_child(usd_label)
        self._usd_txt_stage = omni.kit.ui.TextBox("")
        self._usd_txt_stage.width = -1
        usd_layout.add_child(self._usd_txt_stage)

        btn_usd_comp = omni.kit.ui.Button("Load")
        btn_usd_comp.set_clicked_fn(self._load_components_from_usd)
        usd_layout.add_child(btn_usd_comp)

        json_layout = omni.kit.ui.RowColumnLayout(3, True)
        layout_collapsing.add_child(json_layout)
        json_layout.set_column_width(0, 150)
        json_layout.set_column_width(1, 150)
        json_layout.set_column_width(2, 150)

        j = omni.kit.ui.Label("JSON File")
        json_layout.add_child(j)
        self._json_txt_stage = omni.kit.ui.TextBox("sample.json")
        self._json_txt_stage.width = -1
        json_layout.add_child(self._json_txt_stage)

        btn_json_comp = omni.kit.ui.Button("Load")
        btn_json_comp.set_clicked_fn(self._load_json)
        json_layout.add_child(btn_json_comp)

        delete_layout = omni.kit.ui.RowColumnLayout(3, True)
        layout_collapsing.add_child(delete_layout)
        delete_layout.set_column_width(0, 150)
        delete_layout.set_column_width(1, 150)
        delete_layout.set_column_width(2, 150)

        self.deletecomponentTypeBox = delete_layout.add_child(omni.kit.ui.ComboBox(""))
        self.deletecomponentTypeBox.add_item("COLOR")
        self.deletecomponentTypeBox.add_item("MOVEMENT")
        self.deletecomponentTypeBox.add_item("SCALE")
        self.deletecomponentTypeBox.add_item("LIGHT")
        self.deletecomponentTypeBox.add_item("TEXTURE")
        self.deletecomponentTypeBox.selected_index = 0

        self._handle_txt_stage = omni.kit.ui.TextBox("0")
        self._handle_txt_stage.width = 100
        delete_layout.add_child(self._handle_txt_stage)

        btn_delete_comp = omni.kit.ui.Button("Delete Component")
        btn_delete_comp.set_clicked_fn(self._on_delete_component)
        delete_layout.add_child(btn_delete_comp)

        layout = omni.kit.ui.RowColumnLayout(3, True)
        layout_collapsing.add_child(layout)
        layout.set_column_width(0, 150)
        layout.set_column_width(1, 150)
        layout.set_column_width(2, 150)

        self.componentTypeBox = layout.add_child(omni.kit.ui.ComboBox(""))
        self.componentTypeBox.add_item("COLOR")
        self.componentTypeBox.add_item("MOVEMENT")
        self.componentTypeBox.add_item("SCALE")
        self.componentTypeBox.add_item("LIGHT")
        self.componentTypeBox.add_item("TEXTURE")
        self.componentTypeBox.selected_index = 0
        self.componentTypeBox.set_on_changed_fn(self._create_component_ui)

        btn_add_comp = omni.kit.ui.Button("Add Component")
        btn_add_comp.set_clicked_fn(self._on_add_component)
        layout.add_child(btn_add_comp)

        btn_clear_comp = omni.kit.ui.Button("Clear Component")
        btn_clear_comp.set_clicked_fn(self._on_clear_component)
        layout.add_child(btn_clear_comp)

    def _load_components_from_usd(self, value):
        self._stage = self._usd_context.get_stage()
        for child_prim in self._stage.Traverse():
            if child_prim.GetTypeName() == "TextureComponent":
                self.texture_component_count = self.texture_component_count + 1

        self._dr.load_component_from_usd()

    def _load_color_json(self, value):
        for each_value in value:
            all_prims = []
            for prim in each_value["prim"]:
                all_prims.append(prim)
            first_color = each_value["first_color"]
            second_color = each_value["second_color"]
            duration = -1 if "duration" not in each_value else each_value["duration"]
            include_child = False if "include_child" not in each_value else bool(each_value["include_child"])
            r_range = [float(first_color[0]), float(second_color[0])]
            g_range = [float(first_color[1]), float(second_color[1])]
            b_range = [float(first_color[2]), float(second_color[2])]

    def _load_movement_json(self, value):
        for each_value in value:
            all_prims = []
            for prim in each_value["prim"]:
                all_prims.append(prim)
            duration = -1 if "duration" not in each_value else each_value["duration"]
            include_child = False if "include_child" not in each_value else bool(each_value["include_child"])
            x_range = [float(each_value["x_range"][0]), float(each_value["x_range"][1])]
            y_range = [float(each_value["y_range"][0]), float(each_value["y_range"][1])]
            z_range = [float(each_value["z_range"][0]), float(each_value["z_range"][1])]

    def _load_scale_json(self, value):
        for each_value in value:
            all_prims = []
            for prim in each_value["prim"]:
                all_prims.append(prim)
            duration = -1 if "duration" not in each_value else each_value["duration"]
            include_child = False if "include_child" not in each_value else bool(each_value["include_child"])
            x_range = [float(each_value["x_range"][0]), float(each_value["x_range"][1])]
            y_range = [float(each_value["y_range"][0]), float(each_value["y_range"][1])]
            z_range = [float(each_value["z_range"][0]), float(each_value["z_range"][1])]

    def _load_light_json(self, value):
        for each_value in value:
            all_prims = []
            for prim in each_value["prim"]:
                all_prims.append(prim)
            first_color = each_value["first_color"]
            second_color = each_value["second_color"]
            duration = -1 if "duration" not in each_value else each_value["duration"]
            include_child = False if "include_child" not in each_value else bool(each_value["include_child"])
            lr_range = [float(first_color[0]), float(second_color[0])]
            lg_range = [float(first_color[1]), float(second_color[1])]
            lb_range = [float(first_color[2]), float(second_color[2])]
            li_range = [float(each_value["intensity_range"][0]), float(each_value["intensity_range"][1])]
            lt_range = [float(each_value["temperature_range"][0]), float(each_value["temperature_range"][1])]
            let_value = bool(each_value["enable_temperature"])
            light_dict = dict()
            light_dict["color"] = [lr_range, lg_range, lb_range]
            light_dict["intensity"] = [li_range]
            light_dict["colorTemperature"] = [lt_range]

    def _load_texture_json(self, value):
        for each_value in value:
            self.texture_component_count = self.texture_component_count + 1
            all_prims = []
            all_textures = []
            ignored_class = []
            grouped_class = []
            for prim in each_value["prim"]:
                all_prims.append(prim)
            for texture in each_value["texture_list"]:
                all_textures.append(texture)
            if "ignored_class" in each_value:
                for each_class in each_value["ignored_class"]:
                    ignored_class.append(each_class)
            if "grouped_class" in each_value:
                for each_class in each_value["grouped_class"]:
                    grouped_class.append(each_class)
            duration = -1 if "duration" not in each_value else each_value["duration"]
            include_child = False if "include_child" not in each_value else bool(each_value["include_child"])

    def _load_json(self, widget):
        json_file = open(self._json_txt_stage.value, mode="r")
        json_content = json_file.read()
        json_file.close()
        self._json_value = json.loads(json_content)
        if "color_component" in self._json_value:
            self._load_color_json(self._json_value["color_component"])
        if "movement_component" in self._json_value:
            self._load_movement_json(self._json_value["movement_component"])
        if "scale_component" in self._json_value:
            self._load_scale_json(self._json_value["scale_component"])
        if "light_component" in self._json_value:
            self._load_light_json(self._json_value["light_component"])
        if "texture_component" in self._json_value:
            self._load_texture_json(self._json_value["texture_component"])

    def _create_color_component_ui(self, widget):
        title = "Color Randomizer"
        self.layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(self.layout_collapsing)

        layout = omni.kit.ui.RowColumnLayout(2, True)
        self.layout_collapsing.add_child(layout)
        layout.set_column_width(0, 250)
        layout.set_column_width(1, 250)

        # Row 1 of interface objects
        self.prim_widget = layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        btn_select_prim = omni.kit.ui.Button("Select Prim")
        btn_select_prim.set_clicked_fn(self._on_prim_select)
        layout.add_child(btn_select_prim)

        ch = omni.kit.ui.Label("Include Child Prim")
        layout.add_child(ch)
        self.col_check_child = omni.kit.ui.CheckBox("", value=True)
        layout.add_child(self.col_check_child)

        r = omni.kit.ui.Label("R Range")
        layout.add_child(r)
        self._r_txt_stage = omni.kit.ui.TextBox("0,1")
        self._r_txt_stage.width = 100
        layout.add_child(self._r_txt_stage)

        g = omni.kit.ui.Label("G Range")
        layout.add_child(g)
        self._g_txt_stage = omni.kit.ui.TextBox("0,1")
        self._g_txt_stage.width = 100
        layout.add_child(self._g_txt_stage)

        b = omni.kit.ui.Label("B Range")
        layout.add_child(b)
        self._b_txt_stage = omni.kit.ui.TextBox("0,1")
        self._b_txt_stage.width = 100
        layout.add_child(self._b_txt_stage)

        ic = omni.kit.ui.Label("Ignore Classes")
        layout.add_child(ic)
        self._ignore_class_txt = omni.kit.ui.TextBox("")
        self._ignore_class_txt.width = 200
        layout.add_child(self._ignore_class_txt)

        cdi = omni.kit.ui.Label("Duration Interval")
        layout.add_child(cdi)
        self._cdi_txt_stage = omni.kit.ui.TextBox("2")
        self._cdi_txt_stage.width = 100
        layout.add_child(self._cdi_txt_stage)

    def _create_movement_component_ui(self, widget):
        title = "Movement Randomizer"
        self.layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(self.layout_collapsing)

        layout = omni.kit.ui.RowColumnLayout(2, True)
        self.layout_collapsing.add_child(layout)
        layout.set_column_width(0, 250)
        layout.set_column_width(1, 250)

        # Row 1 of interface objects
        self.prim_widget = layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        btn_select_prim = omni.kit.ui.Button("Select Prim")
        btn_select_prim.set_clicked_fn(self._on_prim_select)
        layout.add_child(btn_select_prim)

        ch = omni.kit.ui.Label("Include Child Prim")
        layout.add_child(ch)
        self.mov_check_child = omni.kit.ui.CheckBox("", value=True)
        layout.add_child(self.mov_check_child)

        x = omni.kit.ui.Label("X Range")
        layout.add_child(x)
        self._x_txt_stage = omni.kit.ui.TextBox("0,1")
        self._x_txt_stage.width = 100
        layout.add_child(self._x_txt_stage)

        y = omni.kit.ui.Label("Y Range")
        layout.add_child(y)
        self._y_txt_stage = omni.kit.ui.TextBox("0,1")
        self._y_txt_stage.width = 100
        layout.add_child(self._y_txt_stage)

        z = omni.kit.ui.Label("Z Range")
        layout.add_child(z)
        self._z_txt_stage = omni.kit.ui.TextBox("0,1")
        self._z_txt_stage.width = 100
        layout.add_child(self._z_txt_stage)

        imc = omni.kit.ui.Label("Ignore Classes")
        layout.add_child(imc)
        self._mov_ignore_class_txt = omni.kit.ui.TextBox("")
        self._mov_ignore_class_txt.width = 200
        layout.add_child(self._mov_ignore_class_txt)

        mdi = omni.kit.ui.Label("Duration Interval")
        layout.add_child(mdi)
        self._mdi_txt_stage = omni.kit.ui.TextBox("2")
        self._mdi_txt_stage.width = 100
        layout.add_child(self._mdi_txt_stage)

    def _create_scale_component_ui(self, widget):
        title = "Scale Randomizer"
        self.layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(self.layout_collapsing)

        layout = omni.kit.ui.RowColumnLayout(2, True)
        self.layout_collapsing.add_child(layout)
        layout.set_column_width(0, 250)
        layout.set_column_width(1, 250)

        # Row 1 of interface objects
        self.prim_widget = layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        btn_select_prim = omni.kit.ui.Button("Select Prim")
        btn_select_prim.set_clicked_fn(self._on_prim_select)
        layout.add_child(btn_select_prim)

        ch = omni.kit.ui.Label("Include Child Prim")
        layout.add_child(ch)
        self.sca_check_child = omni.kit.ui.CheckBox("", value=True)
        layout.add_child(self.sca_check_child)

        scale_x = omni.kit.ui.Label("X Range")
        layout.add_child(scale_x)
        self._scale_x_txt_stage = omni.kit.ui.TextBox("1,3")
        self._scale_x_txt_stage.width = 100
        layout.add_child(self._scale_x_txt_stage)

        scale_y = omni.kit.ui.Label("Y Range")
        layout.add_child(scale_y)
        self._scale_y_txt_stage = omni.kit.ui.TextBox("1,3")
        self._scale_y_txt_stage.width = 100
        layout.add_child(self._scale_y_txt_stage)

        scale_z = omni.kit.ui.Label("Z Range")
        layout.add_child(scale_z)
        self._scale_z_txt_stage = omni.kit.ui.TextBox("1,3")
        self._scale_z_txt_stage.width = 100
        layout.add_child(self._scale_z_txt_stage)

        isc = omni.kit.ui.Label("Ignore Classes")
        layout.add_child(isc)
        self._scale_ignore_class_txt = omni.kit.ui.TextBox("")
        self._scale_ignore_class_txt.width = 200
        layout.add_child(self._scale_ignore_class_txt)

        sdi = omni.kit.ui.Label("Duration Interval")
        layout.add_child(sdi)
        self._sdi_txt_stage = omni.kit.ui.TextBox("2")
        self._sdi_txt_stage.width = 100
        layout.add_child(self._sdi_txt_stage)

    def _create_light_component_ui(self, widget):
        title = "Light Randomizer"
        self.layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(self.layout_collapsing)

        layout = omni.kit.ui.RowColumnLayout(2, True)
        self.layout_collapsing.add_child(layout)
        layout.set_column_width(0, 250)
        layout.set_column_width(1, 250)

        # Row 1 of interface objects
        self.prim_widget = layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        btn_select_prim = omni.kit.ui.Button("Select Prim")
        btn_select_prim.set_clicked_fn(self._on_prim_select)
        layout.add_child(btn_select_prim)

        ch = omni.kit.ui.Label("Include Child Prim")
        layout.add_child(ch)
        self.lig_check_child = omni.kit.ui.CheckBox("", value=True)
        layout.add_child(self.lig_check_child)

        lr = omni.kit.ui.Label("R Range")
        layout.add_child(lr)
        self._lr_txt_stage = omni.kit.ui.TextBox("0,1")
        self._lr_txt_stage.width = 100
        layout.add_child(self._lr_txt_stage)

        lg = omni.kit.ui.Label("G Range")
        layout.add_child(lg)
        self._lg_txt_stage = omni.kit.ui.TextBox("0,1")
        self._lg_txt_stage.width = 100
        layout.add_child(self._lg_txt_stage)

        lb = omni.kit.ui.Label("B Range")
        layout.add_child(lb)
        self._lb_txt_stage = omni.kit.ui.TextBox("0,1")
        self._lb_txt_stage.width = 100
        layout.add_child(self._lb_txt_stage)

        li = omni.kit.ui.Label("Intensity Range")
        layout.add_child(li)
        self._li_txt_stage = omni.kit.ui.TextBox("1000,10000")
        self._li_txt_stage.width = 100
        layout.add_child(self._li_txt_stage)

        let = omni.kit.ui.Label("Enable Temperature")
        layout.add_child(let)
        self._let_txt_stage = omni.kit.ui.CheckBox()
        self._let_txt_stage.width = 100
        layout.add_child(self._let_txt_stage)

        lt = omni.kit.ui.Label("Temperature Range")
        layout.add_child(lt)
        self._lt_txt_stage = omni.kit.ui.TextBox("1000,10000")
        self._lt_txt_stage.width = 100
        layout.add_child(self._lt_txt_stage)

        ldi = omni.kit.ui.Label("Duration Interval")
        layout.add_child(ldi)
        self._ldi_txt_stage = omni.kit.ui.TextBox("2")
        self._ldi_txt_stage.width = 100
        layout.add_child(self._ldi_txt_stage)

    def _create_texture_component_ui(self, widget):
        title = "Texture Randomizer"
        self.layout_collapsing = omni.kit.ui.CollapsingFrame(title, True)
        self._window.layout.add_child(self.layout_collapsing)

        layout = omni.kit.ui.RowColumnLayout(2, True)
        self.layout_collapsing.add_child(layout)
        layout.set_column_width(0, 250)
        layout.set_column_width(1, 250)

        # Row 1 of interface objects
        self.prim_widget = layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        btn_select_prim = omni.kit.ui.Button("Select Prim")
        btn_select_prim.set_clicked_fn(self._on_prim_select)
        layout.add_child(btn_select_prim)

        ch = omni.kit.ui.Label("Include Child Prim")
        layout.add_child(ch)
        self.tex_check_child = omni.kit.ui.CheckBox("", value=True)
        layout.add_child(self.tex_check_child)

        tl = omni.kit.ui.Label("Texture List")
        layout.add_child(tl)
        self._tl_txt_stage = omni.kit.ui.TextBox(
            "omni:/Projects/mwc_2019/Maps/Props/Materials/M_NvidiaCube.mdl,omni:/Projects/mwc_2019/Maps/Props/Materials/MI_006_mustard_bottle.mdl,omni:/Projects/mwc_2019/Maps/Props/Materials/MI_011_banana.mdl,omni:/Projects/mwc_2019/Maps/Props/Materials/MI_025_mug.mdl,omni:/Projects/mwc_2019/Maps/Props/Materials/MI_Apple_2.mdl"
        )
        self._tl_txt_stage.width = -1
        layout.add_child(self._tl_txt_stage)

        tic = omni.kit.ui.Label("Ignore Classes")
        layout.add_child(tic)
        self._texture_ignore_class_txt = omni.kit.ui.TextBox("")
        self._texture_ignore_class_txt.width = 200
        layout.add_child(self._texture_ignore_class_txt)

        tgc = omni.kit.ui.Label("Group Classes")
        layout.add_child(tgc)
        self._texture_group_class_txt = omni.kit.ui.TextBox("")
        self._texture_group_class_txt.width = 200
        layout.add_child(self._texture_group_class_txt)

        tdi = omni.kit.ui.Label("Duration Interval")
        layout.add_child(tdi)
        self._tdi_txt_stage = omni.kit.ui.TextBox("2")
        self._tdi_txt_stage.width = 100
        layout.add_child(self._tdi_txt_stage)

    def _create_component_ui(self, widget):
        if self.componentTypeBox.selected_index == 0:
            self._create_color_component_ui(widget)
        if self.componentTypeBox.selected_index == 1:
            self._create_movement_component_ui(widget)
        if self.componentTypeBox.selected_index == 2:
            self._create_scale_component_ui(widget)
        if self.componentTypeBox.selected_index == 3:
            self._create_light_component_ui(widget)
        if self.componentTypeBox.selected_index == 4:
            self._create_texture_component_ui(widget)

    def _on_prim_select(self, widget):
        prim_list = self._usd_context.get_selection().get_selected_prim_paths()
        for prim in prim_list:
            self.prim_widget.add_item(prim)

    def _on_add_component(self, widget):
        prim_list = [self.prim_widget.get_item_at(index) for index in range(self.prim_widget.get_item_count())]
        if self.componentTypeBox.selected_index == 0:
            r_val = self._r_txt_stage.value.split(",")
            g_val = self._g_txt_stage.value.split(",")
            b_val = self._b_txt_stage.value.split(",")
            include_child = self.col_check_child.value
            self.r_range = [float(r_val[0]), float(r_val[1])]
            self.g_range = [float(g_val[0]), float(g_val[1])]
            self.b_range = [float(b_val[0]), float(b_val[1])]
        if self.componentTypeBox.selected_index == 1:
            x_val = self._x_txt_stage.value.split(",")
            y_val = self._y_txt_stage.value.split(",")
            z_val = self._z_txt_stage.value.split(",")
            include_child = self.mov_check_child.value
            self.x_range = [float(x_val[0]), float(x_val[1])]
            self.y_range = [float(y_val[0]), float(y_val[1])]
            self.z_range = [float(z_val[0]), float(z_val[1])]
        if self.componentTypeBox.selected_index == 2:
            scale_x_val = self._scale_x_txt_stage.value.split(",")
            scale_y_val = self._scale_y_txt_stage.value.split(",")
            scale_z_val = self._scale_z_txt_stage.value.split(",")
            include_child = self.sca_check_child.value
            self.scale_x_range = [float(scale_x_val[0]), float(scale_x_val[1])]
            self.scale_y_range = [float(scale_y_val[0]), float(scale_y_val[1])]
            self.scale_z_range = [float(scale_z_val[0]), float(scale_z_val[1])]
        if self.componentTypeBox.selected_index == 3:
            lr_val = self._lr_txt_stage.value.split(",")
            lg_val = self._lg_txt_stage.value.split(",")
            lb_val = self._lb_txt_stage.value.split(",")
            li_val = self._li_txt_stage.value.split(",")
            lt_val = self._lt_txt_stage.value.split(",")
            let_val = self._let_txt_stage.value
            include_child = self.lig_check_child.value
            self.lr_range = [float(lr_val[0]), float(lr_val[1])]
            self.lg_range = [float(lg_val[0]), float(lg_val[1])]
            self.lb_range = [float(lb_val[0]), float(lb_val[1])]
            self.li_range = [float(li_val[0]), float(li_val[1])]
            self.lt_range = [float(lt_val[0]), float(lt_val[1])]
            self.let_value = bool(let_val)
            light_dict = dict()
            light_dict["color"] = [self.lr_range, self.lg_range, self.lb_range]
            light_dict["intensity"] = [self.li_range]
            light_dict["colorTemperature"] = [self.lt_range]
        if self.componentTypeBox.selected_index == 4:
            self.texture_component_count = self.texture_component_count + 1
            tl_val = self._tl_txt_stage.value.split(",")
            ignored_class = []
            if self._texture_ignore_class_txt.value != "":
                ignored_class = self._texture_ignore_class_txt.value.split(",")
            grouped_class = []
            if self._texture_group_class_txt.value != "":
                grouped_class = self._texture_group_class_txt.value.split(",")
            include_child = self.tex_check_child.value
        self._window.layout.remove_child(self.layout_collapsing)

    def _on_delete_component(self, widget):
        componentId = self.deletecomponentTypeBox.selected_index
        componenthandle = int(self._handle_txt_stage.value)
        # Tracking texture components on deletion and clear texture layer
        if componentId == 4:
            self.texture_component_count = self.texture_component_count - 1

    def _on_clear_component(self, widget):
        self._window.layout.remove_child(self.layout_collapsing)

    def shutdown(self):
        self._window.set_update_fn(None)
        del self._window
