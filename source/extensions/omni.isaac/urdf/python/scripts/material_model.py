import omni.ui as ui


def set_color(model, material):
    color = []
    for item in model.get_item_children():
        item_model = model.get_item_value_model(item)
        color.append(item_model.get_value_as_float())

    material.color.r = color[0]
    material.color.g = color[1]
    material.color.b = color[2]


class MaterialPropertiesModel(ui.AbstractValueModel):
    def __init__(self, props):
        self.props = props
        self.models = [props.name, ui.ColorWidget(props.color.r, props.color.g, props.color.b).model]
        self.models[1].get_item_value_model(self.models[1].get_item_children()[0]).add_value_changed_fn(
            lambda m, color_model=self.models[1], p=self.props: set_color(color_model, p)
        )

    def get_value(self):
        return self.props

    def get_value_model(self, column_id):
        if column_id < len(self.models):
            return self.models[column_id]


class MaterialPropertiesDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = True
        self._highlighting_text = None
        # self.tooltip_fns = [
        #     lin_deflection_tooltip,
        #     ang_deflection_tooltip,
        #     surface_area_tooltip,
        #     rel_offset_tooltip,
        #     int_verts_tooltip,
        #     com_tooltip,
        # ]
        self.column_names = ["Material Name", "RGB"]
        self.num_columns = len(self.column_names)
        self.listView = None

    def build_branch(self, model, item, column_id, level, expanded):
        pass

    def add_List_view(self, listView):
        self.listView = listView

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        if item is None:
            return
        value_model = model.get_item_value_model(item, column_id)
        if column_id < self.num_columns:
            with ui.HStack(
                spacing=4,
                height=20,
                # mouse_pressed_fn=(lambda x, y, b, arg: self.on_mouse_pressed(b, item, expanded, arg)),
                alignment=(ui.Alignment.CENTER),
            ):
                if column_id == 0:
                    ui.Spacer()
                    ui.Label(value_model)
                else:
                    ui.Spacer(width=3)
                    ui.ColorWidget(value_model)
                    for item in value_model.get_item_children():
                        component = value_model.get_item_value_model(item)
                        ui.FloatDrag(component)
                    ui.Spacer(width=3)

    def build_header(self, column_id):
        # style_type_name = "TreeView.Header"
        if column_id < self.num_columns:
            with ui.HStack(height=15):
                ui.Spacer(width=4)
                with ui.Frame(horizontal_clipping=True):
                    ui.Label(
                        (self.column_names[column_id]),
                        name="columnname",
                        # style_type_name_override=style_type_name,
                        # tooltip_fn=(self.tooltip_fns[column_id]),
                        # tooltip_offset_y=15,
                    )

    def on_mouse_pressed(self, button, item, expanded, arg):
        """Called when the user press the mouse button on the item"""
        pass


class MaterialPropertiesItem(ui.AbstractItem):
    def __init__(self, props=None):
        super().__init__()
        self.model = MaterialPropertiesModel(props)

    def get_value(self):
        return self.model.get_value()


class MaterialPropertiesListModel(ui.AbstractItemModel):
    def __init__(self, props_list):
        super().__init__()
        self._children = [MaterialPropertiesItem(material) for name, material in props_list.items()]

    def get_props(self):
        return [item.get_value() for item in self._children]

    def reset(self):
        self._children.clear()
        self._item_changed(None)

    def add_prop(self):
        self._children.append(MaterialPropertiesItem())
        self._item_changed(None)

    def remove_item(self, items):
        if len(items) > 0:
            for item in items:
                if item in self._children:
                    self._children.remove(item)

        else:
            self._children.pop()
        if len(self._children) == 0:
            self._children.append(MaterialPropertiesItem())
        self._item_changed(None)

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            return []
        else:
            return self._children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 2

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        """
        if item:
            if isinstance(item, MaterialPropertiesItem):
                return item.model.get_value_model(column_id)
