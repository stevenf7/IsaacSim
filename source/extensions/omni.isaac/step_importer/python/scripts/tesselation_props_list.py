import carb, omni.ext, omni.kit.commands, omni.ui as ui, os, asyncio
from enum import Enum
from pathlib import Path
from omni.isaac.step_importer import _step_importer

mins = [0.0, 0.0, 0.0]
maxs = [10.0, 3.14, 10]
defaults = [0.001, 0.5, -1.0]


def image_tooltip(text, image_src, width, height):
    """ Base Image tooltip function used on the UI"""
    with ui.VStack(width=width, height=height):
        ui.Label(text, width=width, height=20, style_type_name_override="Tooltip")
        ui.Image(image_src, height=(height - 20))


def lin_deflection_tooltip():
    image_tooltip(
        " limits the distance between a curve and its tessellation",
        str(Path(__file__).parent.joinpath("data/linear_displacement.png")),
        400,
        220,
    )


def ang_deflection_tooltip():
    image_tooltip(
        "  limits the angle between subsequent segments in a polyline",
        str(Path(__file__).parent.joinpath("data/angular_displacement.png")),
        400,
        220,
    )


def surface_area_tooltip():
    ui.Label(
        "Minimum area for each triangle in the Mesh. Negative values means no limit.",
        style_type_name_override="Tooltip",
    )


def rel_offset_tooltip():
    ui.Label("Scales the linear deflection offset by the segment length.", style_type_name_override="Tooltip")


def int_verts_tooltip():
    ui.Label("Takes internal vertices in consideration when building the mesh.", style_type_name_override="Tooltip")


def com_tooltip():
    ui.Label("Exports meshes with origin at volumetric center of mass", style_type_name_override="Tooltip")


def lin_deflection(model, props):
    props.max_linear_offset = model.get_value_as_float()


def ang_deflection(model, props):
    props.max_angular_offset = model.get_value_as_float()


def min_surface(model, props):
    props.min_surface = model.get_value_as_float()


def relative_offset(model, props):
    props.use_relative_offset = model.get_value_as_bool()


def internal_vertices(model, props):
    props.use_internal_vertices = model.get_value_as_bool()


def recenter_mesh(model, props):
    props.volumetric_center_meshes = model.get_value_as_bool()


class TesselationPropertiesModel(ui.AbstractValueModel):
    def __init__(self, props):
        if props:
            self.props = props
        else:
            self.props = _step_importer.Tesselation_Properties()
        self.models = [
            ui.SimpleFloatModel(self.props.max_linear_offset),
            ui.SimpleFloatModel(self.props.max_angular_offset),
            ui.SimpleFloatModel(self.props.min_surface),
            ui.SimpleBoolModel(self.props.use_relative_offset),
            ui.SimpleBoolModel(self.props.use_internal_vertices),
            ui.SimpleBoolModel(self.props.volumetric_center_meshes),
        ]
        self.models[0].add_value_changed_fn(lambda m, b=self.props: lin_deflection(m, b))
        self.models[1].add_value_changed_fn(lambda m, b=self.props: ang_deflection(m, b))
        self.models[2].add_value_changed_fn(lambda m, b=self.props: min_surface(m, b))
        self.models[3].add_value_changed_fn(lambda m, b=self.props: relative_offset(m, b))
        self.models[4].add_value_changed_fn(lambda m, b=self.props: internal_vertices(m, b))
        self.models[5].add_value_changed_fn(lambda m, b=self.props: recenter_mesh(m, b))

    def get_value(self):
        return self.props

    def get_value_model(self, column_id):
        if column_id < 6:
            return self.models[column_id]


class TesselationPropsDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = True
        self._highlighting_text = None
        self.tooltip_fns = [
            lin_deflection_tooltip,
            ang_deflection_tooltip,
            surface_area_tooltip,
            rel_offset_tooltip,
            int_verts_tooltip,
            com_tooltip,
        ]
        self.column_names = ["Lin Deflection", "Ang Deflection", "Min Poly Area", "Relative Offset"]
        self.num_columns = len(self.column_names)
        self.listView = None

    def build_branch(self, model, item, column_id, level, expanded):
        pass

    def add_List_view(self, listView):
        self.listView = listView

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        value_model = model.get_item_value_model(item, column_id)
        if not value_model:
            return
        if column_id < self.num_columns:
            with ui.HStack(
                spacing=4,
                height=20,
                mouse_pressed_fn=(lambda x, y, b, arg: self.on_mouse_pressed(b, item, expanded, arg)),
                alignment=(ui.Alignment.CENTER),
            ):
                if column_id < 2:
                    ui.Spacer(width=3)
                    ui.FloatDrag(model=value_model, min=(mins[column_id]), max=(maxs[column_id]))
                    ui.Spacer(width=3)
                elif column_id == 2:
                    ui.Spacer(width=3)
                    ui.FloatDrag(model=value_model, min=(mins[column_id]), max=(maxs[column_id]))
                    ui.Spacer(width=3)
                elif column_id > 2:
                    ui.Spacer()
                    ui.CheckBox(model=value_model)

    def build_header(self, column_id):
        style_type_name = "TreeView.Header"
        if column_id < self.num_columns:
            with ui.HStack(height=15):
                ui.Spacer(width=4)
                with ui.Frame(horizontal_clipping=True):
                    ui.Label(
                        (self.column_names[column_id]),
                        name="columnname",
                        style_type_name_override=style_type_name,
                        tooltip_fn=(self.tooltip_fns[column_id]),
                        tooltip_offset_y=15,
                    )

    def on_mouse_pressed(self, button, item, expanded, arg):
        """Called when the user press the mouse button on the item"""
        pass


class TesselationPropertiesItem(ui.AbstractItem):
    def __init__(self, props=None):
        super().__init__()
        self.model = TesselationPropertiesModel(props)

    def get_value(self):
        return self.model.get_value()


class TesselationPropertiesListModel(ui.AbstractItemModel):
    def __init__(self, props_list):
        super().__init__()
        self._children = [TesselationPropertiesItem(props) for props in props_list]

    def get_props(self):
        return [item.get_value() for item in self._children]

    def reset(self):
        self._children.clear()
        self._item_changed(None)

    def add_prop(self):
        self._children.append(TesselationPropertiesItem())
        self._item_changed(None)

    def remove_item(self, items):
        if len(items) > 0:
            for item in items:
                if item in self._children:
                    self._children.remove(item)

        else:
            self._children.pop()
        if len(self._children) == 0:
            self._children.append(TesselationPropertiesItem())
        self._item_changed(None)

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            return []
        else:
            return self._children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 4

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        """
        if item:
            if isinstance(item, TesselationPropertiesItem):
                return item.model.get_value_model(column_id)
