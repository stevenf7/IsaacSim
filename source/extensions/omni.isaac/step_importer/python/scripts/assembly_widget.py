import carb
import omni.ext
import omni.kit.commands
import omni.ui as ui
import os
import asyncio
from enum import Enum

from omni.isaac.step_importer import _step_importer


class itemType(Enum):
    Assembly = 0
    Mesh = 1
    Color = 2


item_type_str = {itemType.Assembly: "Assembly", itemType.Mesh: "Mesh", itemType.Color: "Material"}


class AssemblyDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = None
        # Text that is highlighted in flat mode
        self._highlighting_text = None

    def build_branch(self, model, item, column_id, level, expanded):
        """Create a branch widget that opens or closes subtree"""
        from omni.kit.widget.stage.stage_icons import StageIcons

        if column_id == 0:
            with ui.HStack(width=16 * (level + 2), height=0):
                ui.Spacer()
                if model.can_item_have_children(item):
                    # Draw the +/- icon
                    image_name = "Minus" if expanded else "Plus"
                    ui.Image(
                        StageIcons().get(image_name), width=10, height=10, style_type_name_override="TreeView.Item"
                    )
                    ui.Spacer(width=4)

    def on_mouse_double_clicked(self, item):
        """Called when the user double clicks on the item"""
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
        with ui.HStack(spacing=4, height=20):
            text = value_model.get_value_as_string()
            ui.Label(
                text,
                width=0,
                name=text,
                style_type_name_override="TreeView.Item",
                mouse_pressed_fn=lambda x, y, b, _: self.on_mouse_pressed(b, item, expanded),
                mouse_double_clicked_fn=lambda x, y, b, _: self.on_mouse_double_clicked(item),
            )

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


class AssemblyItem(ui.AbstractItem):
    def __init__(self, text, item_type, index, pose=None, usd_path=None):
        """
        Item to be added on the extracted Hierarchy 
        """
        super().__init__()
        self.name_model = ui.SimpleStringModel(text)
        self.type_model = ui.SimpleStringModel(item_type_str[item_type])
        self.model_cols = [self.name_model, self.type_model]
        self.type = item_type
        self.index = index

        self.pose = pose
        self.usd_path = usd_path
        self.children = []

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


class AssemblyTreeModel(ui.AbstractItemModel):
    def __init__(self, part=None):
        super().__init__()

        self._root = AssemblyItem("Root", itemType.Assembly, 0, _step_importer.Transform())
        self.usd_paths = {}

    def reset(self):
        self.part = None
        self._root.clear()
        self._item_changed(None)
        self.usd_paths.clear()

    def add_part(self, part, assembly_paths, mesh_paths):
        self.part = part
        self.usd_paths[itemType.Assembly] = assembly_paths
        self.usd_paths[itemType.Mesh] = mesh_paths
        self.make_sub_tree(self._root)
        for i, c in enumerate(part.materials):
            self._root.children.append(AssemblyItem("Color {}".format(i), itemType.Color, i))
        self._item_changed(None)
        # for c in self._root.children:
        #     self._item_changed(c)
        # print("Done", self.get_item_value_model_count(self.children[0]), len(self.get_item_children(self.children[0])))

    def make_sub_tree(self, child):
        assembly = self.part.assemblies[child.index]
        for a in assembly.sub_assemblies:
            child_assembly = self.part.assemblies[a.id]
            child.children.append(
                AssemblyItem(
                    child_assembly.name, itemType.Assembly, a.id, a.pose, self.usd_paths[itemType.Assembly][a.id]
                )
            )
            self.make_sub_tree(child.children[-1])
        for m in assembly.meshes:
            child_mesh = self.part.meshes[m.id]
            child.children.append(
                AssemblyItem(child_mesh.name, itemType.Mesh, m.id, m.pose, self.usd_paths[itemType.Mesh][m.id])
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
