import carb, omni.ext, omni.kit.commands, omni.ui as ui, os, asyncio
from enum import Enum
from omni.isaac.step_importer import _step_importer
from pxr import UsdGeom


class MeshListDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = None
        self._highlighting_text = None
        self.column_names = ["Index", "Name", "Volume", "Density", "Inertia Tensor", "Duplicate Replacement"]

    def build_branch(self, model, item, column_id, level, expanded):
        pass

    def on_mouse_double_clicked(self, item):
        """Called when the user double clicks on the item"""
        if item.get_usd_path() is not None:
            usd_context = omni.usd.get_context()

            async def save_and_open(path):
                if omni.usd.get_context().has_pending_edit():
                    await omni.kit.asyncapi.save_stage()
                omni.usd.get_context().close_stage(lambda a, b: omni.usd.get_context().open_stage(path, None))

            asyncio.ensure_future(save_and_open(item.get_usd_path().strip()))

    def on_mouse_pressed(self, button, item, expanded):
        """Called when the user press the mouse button on the item"""
        if button != 1:
            return

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        value = model.get_item_value(item, column_id)
        if value is None:
            return
        with ui.HStack(
            spacing=4,
            height=20,
            horizontal_clipping=True,
            mouse_double_clicked_fn=(lambda x, y, b, _: self.on_mouse_double_clicked(item)),
        ):
            if column_id not in [1, 4]:
                text = str(value)
                ui.Label(text, width=0, name=text, style_type_name_override="TreeView.Item")
            elif column_id == 1:
                if model.edit_mode:
                    m = ui.SimpleStringModel(item.mesh_props.name)

                    def mesh_name():
                        old_name = item.mesh_props.name
                        if old_name != m.get_value_as_string():
                            item.mesh_props.name = m.get_value_as_string()

                    m.add_end_edit_fn(lambda b: mesh_name())
                    ui.StringField(model=m)
                else:
                    text = str(value)
                    ui.Label(text, width=0, name=text, style_type_name_override="TreeView.Item")
            elif column_id == 4:
                for i in [0, 2, 5]:
                    ui.Label(
                        "{0:.4f}".format(float(value[i] / 1000.0)),
                        width=0,
                        name="Inertia",
                        style_type_name_override="TreeView.Item",
                    )

    def build_header(self, column_id):
        style_type_name = "TreeView.Header"
        with ui.HStack(horizontal_clipping=True):
            ui.Spacer(width=10)
            ui.Label((self.column_names[column_id]), name="columnname", style_type_name_override=style_type_name)


class MeshItem(ui.AbstractItem):
    def __init__(self, mesh_id, lod_props, exporter):
        super().__init__()
        self.exporter = exporter
        self.id = mesh_id
        self.prim_paths = []
        self.key = ""
        self.lod_props = lod_props
        self.mesh_props = self.exporter.part.meshes_properties[self.id]
        self.cols_data = [
            lambda: str(self.id),
            lambda: self.mesh_props.name,
            lambda: self.mesh_props.volume,
            lambda: self.mesh_props.density,
            lambda: self.mesh_props.get_inertia_diag_matrix(),
            lambda: self.get_replacement_id(),
        ]

    def update_prim_paths(self):
        usd_path = self.get_usd_path().replace("\\", "/").lower()
        stage = omni.usd.get_context().get_stage()
        self.prims = [
            t for t in stage.Traverse() if UsdGeom.Mesh(t) and usd_path == (t.GetPrimStack()[-1]).layer.identifier
        ]
        print(usd_path)
        print(self.prims)

    def get_replacement_id(self):
        if self.id in self.exporter.mesh_replacement_map:
            return self.exporter.mesh_replacement_map[self.id]

    def get_usd_path(self):
        return self.exporter.mesh_usd_paths[self.id]

    def get_col_value(self, col_id):
        if col_id < len(self.cols_data):
            return self.cols_data[col_id]()


class MeshListModel(ui.AbstractItemModel):
    def __init__(self, exporter=None):
        super().__init__()
        self._childrenMap = {}
        self.exporter = exporter
        if exporter:
            self.add_mesh_list(exporter)
        else:
            self._children = []
        self.edit_mode = False

    def reset(self):
        self._children.clear()
        self._childrenMap.clear()
        self._item_changed(None)

    def update_prim_paths(self):
        for c in self._children:
            c.update_prim_paths()

    def add_mesh_list(self, exporter):
        self._children.clear()
        self.exporter = exporter
        for i, p in enumerate(self.exporter.part.meshes_properties):
            self._children.append(MeshItem(i, [_step_importer.Tesselation_Properties()], self.exporter))
            # print(self._children[-1].get_usd_path())
            key = ("meshes" + self._children[-1].get_usd_path().split("meshes")[-1]).replace("\\", "/")
            self._children[-1].key = key
            print(key, self._children[-1])
            self._childrenMap[key] = self._children[-1]
        self._item_changed(None)

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        for item in self._children:
            self._item_changed(item)
        if not self.edit_mode:

            def export():
                self.exporter.export()
                for item in self._children:
                    old_key = item.key
                    key = "meshes" + item.get_usd_path().split("meshes")[-1].replace("\\", "/")
                    if old_key != key:
                        print(key)
                        self._childrenMap.pop(old_key)
                        self._childrenMap[key] = item
                        item.key = key

            omni.usd.get_context().close_stage(lambda a, b: export())

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            return []
        else:
            return self._children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 6

    def get_item_value(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """
        if item:
            if isinstance(item, MeshItem):
                return item.get_col_value(column_id)
