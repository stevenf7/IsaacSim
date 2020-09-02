import carb
import omni
import omni.ext
import omni.kit.commands
import omni.ui as ui
import os
import asyncio
import weakref
from enum import Enum

from omni.isaac.step_importer import _step_importer

from .usd_exporter import get_all_prims_with_material


class itemType(Enum):
    Assembly = 0
    Mesh = 1
    Color = 2
    Color_emissive = 3
    Color_metallic = 4
    Color_roughness = 5


item_type_str = {
    itemType.Assembly: "Assembly",
    itemType.Mesh: "Mesh",
    itemType.Color: "Material",
    itemType.Color_emissive: "",
    itemType.Color_metallic: "",
    itemType.Color_roughness: "",
}


class AssemblyDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = None
        # Text that is highlighted in flat mode
        self._highlighting_text = None

    def build_branch(self, model, item, column_id, level, expanded):
        """Create a branch widget that opens or closes subtree"""
        # from omni.kit.widget.stage.stage_icons import StageIcons
        if item.type.value >= itemType.Color.value:
            stage = omni.usd.get_context().get_stage()
            if stage:
                if len(get_all_prims_with_material(stage, item.get_name())) == 0:
                    return
        if column_id == 0:
            with ui.HStack(width=16 * (level + 2), height=0):
                ui.Spacer()
                if model.can_item_have_children(item):
                    # Draw the +/- icon
                    image_name = "Minus" if expanded else "Plus"
                    ui.Label("-" if expanded else "+")
                    # ui.Image(
                    #     StageIcons().get(image_name), width=10, height=10, style_type_name_override="TreeView.Item"
                    # )
                    ui.Spacer(width=4)

    def on_mouse_double_clicked(self, item):
        """Called when the user double clicks on the item"""
        print(type(item))
        if item.type in [itemType.Assembly, itemType.Mesh]:
            if item.usd_path is not None:
                usd_context = omni.usd.get_context()

                async def save_and_open(path):
                    if omni.usd.get_context().has_pending_edit():
                        await omni.kit.asyncapi.save_stage()
                    result = await omni.kit.asyncapi.open_stage(path)
                    return result

                asyncio.ensure_future(save_and_open(item.usd_path.strip()))

    def on_mouse_pressed(self, button, item, expanded):
        """Called when the user press the mouse button on the item"""
        if button != 1:
            # It's for context menu only
            return

        pass

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        value_model = model.get_item_value_model(item, column_id)
        if not value_model:
            return
        name = item.get_name()
        if item.type.value >= itemType.Color.value:
            stage = omni.usd.get_context().get_stage()
            if stage:
                if len(get_all_prims_with_material(stage, item.get_name())) == 0:
                    return
        row = ui.HStack(
            spacing=4, height=20, mouse_double_clicked_fn=lambda x, y, b, c, i=item: self.on_mouse_double_clicked(item)
        )
        with row:
            if column_id == 1:
                ui.Label(
                    value_model.get_value_as_string(),
                    width=0,
                    name=name,
                    style_type_name_override="TreeView.Item",
                    mouse_pressed_fn=lambda x, y, b, _: self.on_mouse_pressed(b, item, expanded),
                )

            elif column_id == 0:
                if item.type in [itemType.Assembly, itemType.Mesh]:
                    if model.edit_mode and item.type == itemType.Assembly:
                        name_model = ui.SimpleStringModel(name)

                        def assembly_name(name_model, item):
                            if name != name_model.get_value_as_string():
                                item.set_name(name_model.get_value_as_string())

                        name_model.add_end_edit_fn(lambda b, item=item: assembly_name(b, item))
                        ui.StringField(model=name_model, style_type_name_override="TreeView.Edit", width=ui.Percent(90))
                    else:
                        text = value_model.get_value_as_string()
                        ui.Label(text, width=0, name=text, style_type_name_override="TreeView.Item")
                else:
                    if item.type == itemType.Color:
                        widget = ui.ColorWidget(width=0)
                        if not model.edit_mode:
                            ui.Label(name, width=0, style_type_name_override="TreeView.Item")
                        else:
                            name_model = ui.SimpleStringModel(name)

                            def assembly_name(name_model, item):
                                if name != name_model.get_value_as_string():
                                    item.set_name(name_model.get_value_as_string())

                            name_model.add_end_edit_fn(lambda b, item=item: assembly_name(b, item))
                            ui.StringField(
                                model=name_model, style_type_name_override="TreeView.Edit", width=ui.Percent(90)
                            )

                        m = widget.model
                        color = value_model.get_value_as_color()
                        for i, item in enumerate(m.get_item_children()):
                            item_model = m.get_item_value_model(item)
                            item_model.set_value(color[i])
                            # item_model.add_begin_edit_fn(lambda _: value_model.begin_edit())
                            # item_model.add_end_edit_fn(lambda _: value_model.end_edit())
                            item_model.add_value_changed_fn(
                                lambda m, b=value_model, i=i: value_model.set_color(m.get_value_as_float(), i)
                            )
                    elif item.type == itemType.Color_emissive:
                        enabled, emissive = value_model.get_value_as_emissive()
                        ui.Label("Emissive", width=0, style_type_name_override="TreeView.Item")

                        # cb.model.add_begin_edit_fn(lambda _: value_model.begin_edit())
                        # cb.model.add_end_edit_fn(lambda _: value_model.end_edit())

                        widget = ui.ColorWidget(width=0)
                        em = widget.model

                        for i, item in enumerate(em.get_item_children()):
                            if i < 3:
                                item_model = em.get_item_value_model(item)
                                item_model.set_value(emissive[i])
                                item_model.add_value_changed_fn(
                                    lambda m, b=value_model, i=i: b.set_emissive_value(m.get_value_as_float(), i)
                                )
                        fd = ui.FloatDrag(min=0, max=10000.0, style_type_name_override="TreeView.Edit")
                        fd.model.set_value(enabled)
                        fd.model.add_value_changed_fn(lambda a, b=value_model: b.set_emissive(a.get_value_as_float()))

                    elif item.type == itemType.Color_metallic:
                        ui.Label("Metallic", width=0, style_type_name_override="TreeView.Item")
                        fd = ui.FloatDrag(style_type_name_override="TreeView.Edit")
                        fd.model.set_value(value_model.get_value_as_metallic())
                        fd.model.add_value_changed_fn(lambda m, b=value_model: b.set_metallic(m.get_value_as_float()))
                    elif item.type == itemType.Color_roughness:
                        ui.Label("Roughness", width=0, style_type_name_override="TreeView.Item")
                        fd = ui.FloatDrag(style_type_name_override="TreeView.Edit")
                        fd.model.set_value(value_model.get_value_as_roughness())
                        fd.model.add_value_changed_fn(lambda m, b=value_model: b.set_roughness(m.get_value_as_float()))

        # else:
        #         # If highlighting disabled completley, all the items should be light
        #         is_highlighted = not self._highlighting_enabled and not self._highlighting_text

    def build_header(self, column_id):
        style_type_name = "TreeView.Header"
        with ui.HStack():
            ui.Spacer(width=10)
            if column_id == 0:
                ui.Label("Name", name="columnname", style_type_name_override=style_type_name)
            else:
                ui.Label("Type", name="columnname", style_type_name_override=style_type_name)


class MaterialModel(ui.AbstractItemModel):
    def __init__(self, exporter, index):
        self.exporter = exporter
        self.index = index

    def begin_edit(self):

        carb.log_warn("begin edit")

    def end_edit(self):

        carb.log_warn("end edit")

    def get_value_as_string(self):
        return self.exporter.material_names[self.index]

    def set_material_name(self, name):
        self.exporter.material_names[self.index] = name

    def get_value_as_color(self):
        c = self.exporter.part.materials[self.index].rgba_color
        return [c.r, c.g, c.b, c.a]

    def get_value_as_emissive(self):
        c = self.exporter.part.materials[self.index].emissive
        return c.a, [c.r, c.g, c.b]

    def get_value_as_metallic(self):
        return self.exporter.part.materials[self.index].metallic

    def get_value_as_roughness(self):
        return self.exporter.part.materials[self.index].roughness

    def get_material(self):
        return self.exporter.part.materials[self.index]

    def set_metallic(self, value):
        self.exporter.part.materials[self.index].metallic = value
        self.exporter.update_material(self.index)

    def set_roughness(self, value):
        self.exporter.part.materials[self.index].roughness = value
        self.exporter.update_material(self.index)

    def set_emissive(self, value):
        self.exporter.part.materials[self.index].emissive.a = value
        self.exporter.update_material(self.index)

    def set_emissive_value(self, value, index):
        if index == 0:
            self.exporter.part.materials[self.index].emissive.r = value
        elif index == 1:
            self.exporter.part.materials[self.index].emissive.g = value
        elif index == 2:
            self.exporter.part.materials[self.index].emissive.b = value
        self.exporter.update_material(self.index)

    def set_color(self, value, index):
        if index == 0:
            self.exporter.part.materials[self.index].rgba_color.r = value
        elif index == 1:
            self.exporter.part.materials[self.index].rgba_color.g = value
        elif index == 2:
            self.exporter.part.materials[self.index].rgba_color.b = value
        elif index == 3:
            self.exporter.part.materials[self.index].rgba_color.a = value
        self.exporter.update_material(self.index)


class AssemblyItem(ui.AbstractItem):
    def __init__(self, exporter, item_type: itemType, index, pose=None, usd_path=None, parent_model=None):
        """
        Item to be added on the extracted Hierarchy  
        """
        super().__init__()

        self.exporter = exporter
        self.index = index
        self.pose = pose
        self.usd_path = usd_path
        self.children = []
        self.key = None
        self.type = item_type
        if self.exporter:
            if item_type == itemType.Assembly:
                self.name_model = ui.SimpleStringModel(self.exporter.part.assemblies[index].name)
                self.key = "assembly_" + self.name_model.get_value_as_string() + "_" + str(self.index)
            elif item_type == itemType.Mesh:
                self.name_model = ui.SimpleStringModel(self.exporter.get_mesh_name(index))
            else:
                if item_type == itemType.Color:
                    self.name_model = MaterialModel(self.exporter, index)
                    self.children = [
                        AssemblyItem(exporter, itemType.Color_emissive, index, parent_model=self.name_model),
                        AssemblyItem(exporter, itemType.Color_metallic, index, parent_model=self.name_model),
                        AssemblyItem(exporter, itemType.Color_roughness, index, parent_model=self.name_model),
                    ]
                else:
                    self.name_model = parent_model
            self.type_model = ui.SimpleStringModel(item_type_str[item_type])
            self.model_cols = [self.name_model, self.type_model]

    def set_name(self, name):
        if self.type == itemType.Assembly:
            self.exporter.part.assemblies[self.index].name = name
            return
        elif self.type == itemType.Mesh:
            pass
        else:
            self.exporter.material_names[self.index] = name

    def get_name(self):
        if self.type == itemType.Assembly:
            return self.exporter.part.assemblies[self.index].name
        if self.type == itemType.Mesh:
            return self.exporter.get_mesh_name(self.index)
        else:
            return self.exporter.material_names[self.index]

    def add_child(self, child, pos=-1):
        if pos > 0:
            self.children.insert(pos, child)
        else:
            self.children.append(child)

    def pop_child(self, pos):
        if pos >= 0 and pos < len(self.children):
            child = self.children[pos]
            self.children.pop(pos)
            return child
        return None

    def clear(self):
        for c in self.children:
            c.clear()
        self.children.clear()


def traverse_item(item):
    stack = [item]
    out = [
        i
        for i in item.children
        if i.type not in [itemType.Color_emissive, itemType.Color_metallic, itemType.Color_roughness]
    ]
    while len(stack) > 0:
        item = stack.pop()
        if len(item.children):
            stack = stack + item.children
            out = out + item.children
    return out


class AssemblyTreeModel(ui.AbstractItemModel):
    def __init__(self, exporter=None):
        super().__init__()
        self.exporter = None
        self._root = AssemblyItem(exporter, itemType.Assembly, 0, _step_importer.Transform())
        self.usd_paths = {}
        self.edit_mode = False
        self._childrenMap = {}

    def reset(self):
        self.exporter = None
        self._root.clear()
        self._item_changed(None)
        self._childrenMap.clear()
        self.usd_paths.clear()

    def add_part(self, exporter):
        self.reset()
        self.exporter = exporter
        self._root.exporter = self.exporter
        self.make_sub_tree(weakref.proxy(self._root))
        for i, c in enumerate(self.exporter.part.materials):
            self._root.children.append(AssemblyItem(self.exporter, itemType.Color, i))
        self._childrenMap = {i.key: i for i in self._root.children}
        self._item_changed(None)

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        for item in traverse_item(self._root):
            self._item_changed(item)
        if not self.edit_mode:
            self.export_assembly(False)

    def update(self):
        for i in self._root.children:
            self._item_changed(i)

    def export_assembly(self, item_Changed=True):
        def export():
            self.exporter.export()
            for item in self._root.children:
                old_key = item.key
                key = "assembly_" + item.name_model.get_value_as_string() + "_" + str(item.index)
                if old_key != key:
                    item.key = key
                if item_Changed:
                    self._item_changed(item)

        omni.usd.get_context().new_stage(lambda a, b: omni.usd.get_context().close_stage(lambda a, b: export()))

    def make_sub_tree(self, child):
        for a in self.exporter.part.assemblies[child.index].sub_assemblies:
            child.children.append(
                AssemblyItem(self.exporter, itemType.Assembly, a.id, a.pose, self.exporter.assemblies_path[a.id])
            )
            self.make_sub_tree(weakref.proxy(child.children[-1]))
        for m in self.exporter.part.assemblies[child.index].meshes:
            child.children.append(
                AssemblyItem(self.exporter, itemType.Mesh, m.id, m.pose, self.exporter.get_mesh_path(m.id))
            )

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is None:
            item = self._root
        return item.children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 2

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """
        if item and isinstance(item, AssemblyItem):
            return item.model_cols[column_id]
