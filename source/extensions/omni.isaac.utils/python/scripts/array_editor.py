import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from pxr import Gf
import gc
import weakref


class EditableArrayDelegate(ui.AbstractItemDelegate):
    def __init__(self, selection):
        super().__init__()
        self.listView = None
        self.selection = selection

    def build_branch(self, model, item, column_id, level, expanded):
        with ui.HStack(width=16 * (level + 2), height=15):
            ui.Spacer(width=level * 5)
            with ui.ZStack(width=30):
                ui.Spacer()
                if model.can_item_have_children(item):
                    ui.Circle(style={"background_color": 0x00000000, "border_color": 0xFF000000, "border_width": 1})
                    with ui.HStack():
                        ui.Spacer()
                        align = ui.Alignment.V_CENTER
                        ui.Line(name="title", width=6, alignment=align)
                        ui.Spacer()
                    if not expanded:
                        with ui.VStack():
                            ui.Spacer()
                            align = ui.Alignment.H_CENTER
                            ui.Line(name="title", height=6, alignment=align)
                            ui.Spacer()
        # if column_id == 0:
        #     with ui.HStack(width=16 * (level + 2), height=0):
        #         ui.Spacer()
        #         if model.can_item_have_children(item):
        #             # Draw the +/- icon
        #             image_name = "-" if expanded else "+"
        #             ui.Label(image_name)
        #             ui.Spacer(width=4)

    def add_List_view(self, listView):
        self.listView = listView

    def colored_block(self, color, label):
        with ui.ZStack(width=20):
            ui.Rectangle(style={"background_color": color})
            model = ui.HStack()
            with model:
                ui.Spacer(width=2)
                ui.Label(label, alignment=ui.Alignment.CENTER, style={"color": 0xFFFFFFFF})
                ui.Spacer(width=2)

    def add_xyz(self, item, labels, values):
        with ui.HStack():
            all_axis = ["X", "Y", "Z"]
            labels = {"X": labels[0], "Y": labels[1], "Z": labels[2]}
            values = {"X": values[0], "Y": values[1], "Z": values[2]}
            colors = {"X": 0xFF5555AA, "Y": 0xFF76A371, "Z": 0xFFA07D4F}
            add_floats = []
            for axis in all_axis:
                with ui.HStack(width=ui.Percent(20)):
                    self.colored_block(colors[axis], labels[axis])
                    float_field = ui.FloatField(name="transform", min=-1000000, max=1000000, step=0.01)
                    float_field.model.set_value(values[axis])
                    add_floats.append(float_field)

            def add_value(button):
                attr_value = list(item.attr.Get())
                current_selection = self.selection.get_selected_prim_paths()
                x_value = add_floats[0].model.get_value_as_float()
                y_value = add_floats[1].model.get_value_as_float()
                z_value = add_floats[2].model.get_value_as_float()
                attr_value.append(Gf.Vec3f(x_value, y_value, z_value))
                item.attr.Set(attr_value)
                self.selection.clear_selected_prim_paths()
                self.selection.set_selected_prim_paths([current_selection[0]], True)

            button_add = ui.Button("Add", width=0)
            button_add.set_clicked_fn(lambda b=button_add: add_value(b))

    def modify_remove_xyz(self, item, labels, values):
        model = ui.HStack()
        with model:
            all_axis = ["X", "Y", "Z"]
            labels = {"X": labels[0], "Y": labels[1], "Z": labels[2]}
            values = {"X": values[0], "Y": values[1], "Z": values[2]}
            colors = {"X": 0xFF5555AA, "Y": 0xFF76A371, "Z": 0xFFA07D4F}
            modify_floats = []
            for axis in all_axis:
                with ui.HStack(width=ui.Percent(20)):
                    self.colored_block(colors[axis], labels[axis])
                    float_field = ui.FloatField(name="transform", min=-1000000, max=1000000, step=0.01)
                    float_field.model.set_value(values[axis])
                    modify_floats.append(float_field)

            def modify_value(button):
                attr_value = list(item.attr.Get())
                current_selection = self.selection.get_selected_prim_paths()
                x_value = modify_floats[0].model.get_value_as_float()
                y_value = modify_floats[1].model.get_value_as_float()
                z_value = modify_floats[2].model.get_value_as_float()
                attr_value[item.index] = Gf.Vec3f(x_value, y_value, z_value)
                item.attr.Set(attr_value)
                self.selection.clear_selected_prim_paths()
                self.selection.set_selected_prim_paths([current_selection[0]], True)

            button_modify = ui.Button("Modify", width=0)
            button_modify.set_clicked_fn(lambda b=button_modify: modify_value(b))

            def remove_value(button):
                attr_value = list(item.attr.Get())
                current_selection = self.selection.get_selected_prim_paths()
                del attr_value[item.index]
                item.attr.Set(attr_value)
                self.selection.clear_selected_prim_paths()
                self.selection.set_selected_prim_paths([current_selection[0]], True)

            button_remove = ui.Button("Remove", width=0)
            button_remove.set_clicked_fn(lambda b=button_remove: remove_value(b))

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        with ui.VStack():
            if isinstance(item, EditableArraySection):
                ui.Label(item.attr.GetBaseName(), height=20)
            elif isinstance(item, EditableArrayAddItem):
                self.add_xyz(item, [" X ", " Y ", " Z "], [0.0, 0.0, 0.0])
            elif isinstance(item, EditableArrayViewItem):
                self.modify_remove_xyz(item, [" X ", " Y ", " Z "], [item.value[0], item.value[1], item.value[2]])
            else:
                ui.Label("Other Item")
            ui.Line()

    def build_header(self, column_id):
        # ui.Label((self.column_names[column_id]))
        pass

    def on_mouse_pressed(self, button, item, expanded, arg):
        """Called when the user press the mouse button on the item"""
        pass


class EditableArrayAddItem(ui.AbstractItem):
    def __init__(self, attr, value=None):
        super().__init__()
        self.attr = attr
        self.value = value
        self.children = []

    def has_children(self):
        return len(self.children)


class EditableArrayViewItem(ui.AbstractItem):
    def __init__(self, attr, index, value=None):
        super().__init__()
        self.attr = attr
        self.index = index
        self.value = value
        self.children = []

    def has_children(self):
        return len(self.children)


class EditableArraySection(ui.AbstractItem):
    def __init__(self, attr, children=[]):
        super().__init__()
        self.attr = attr
        self.children = children

    def has_children(self):
        return len(self.children)


class EditableArrayListModel(ui.AbstractItemModel):
    def __init__(self, prim, stage):
        super().__init__()
        attributeList = []
        propNames = prim.GetPropertyNames()
        for propName in propNames:
            usd_attribute = prim.GetAttribute(str(propName))
            if usd_attribute.GetTypeName().isArray and usd_attribute.GetTypeName() == "float3[]":
                attributeList.append(usd_attribute)

        self.children = []
        for attr in attributeList:
            childValueList = []
            val_index = 0
            if attr.Get() is not None:
                for val in attr.Get():
                    childValueList.append(EditableArrayViewItem(attr, val_index, val))
                    val_index = val_index + 1
                childValueList.append(EditableArrayAddItem(attr))
                self.children.append(EditableArraySection(attr, childValueList))

    def get_props(self):
        return [item.get_value() for item in self._children]

    def can_item_have_children(self, item):
        """TOO: NOT FINAL. Just a proof that is doesn't crash"""
        return item.has_children()

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is None:
            return self.children
        else:
            return item.children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        """
        if item:
            return item.model


EXTENSION_NAME = "Array Editor"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()

        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        self._menu_items = [
            MenuItemDescription(
                name="Isaac",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Window")
        with self._window.frame:
            self._frame = ui.Frame()

    def _menu_callback(self):
        self._window.visible = not self._window.visible
        if self._window.visible:
            self._selection = self._usd_context.get_selection()
            self._events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = self._events.create_subscription_to_pop(
                self._on_stage_event, name="array editor stage event"
            )
        else:
            self._events = None
            self._stage_event_sub = None

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            selection = self._selection.get_selected_prim_paths()
            stage = self._usd_context.get_stage()
            prim = None
            if len(selection) == 0:
                pass
            else:
                path = selection[0]
                prim = stage.GetPrimAtPath(path)

            if len(selection) > 0:
                with self._frame:
                    with ui.ScrollingFrame(
                        height=400,
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                        style_type_name_override="TreeView",
                    ):
                        self._editable_array_delegate = EditableArrayDelegate(self._selection)
                        self._editable_array_model = EditableArrayListModel(prim, stage)
                        tree_view = ui.TreeView(
                            self._editable_array_model, root_visible=False, delegate=self._editable_array_delegate
                        )
            else:
                self._frame.clear()

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Window")
        self._window = None
        gc.collect()
