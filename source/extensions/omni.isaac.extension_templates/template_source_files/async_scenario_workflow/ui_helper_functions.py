from omni.isaac.ui.widgets import DynamicComboBoxModel
from omni.isaac.ui.ui_utils import (
    add_line_rect_flourish,
    btn_builder,
    state_btn_builder,
    float_builder,
    int_builder,
    xyz_builder,
    color_picker_builder,
    setup_ui_headers,
    get_style,
    str_builder,
)
import omni.ui as ui
from omni.kit.window.property.templates import LABEL_WIDTH
from pxr import Usd
from omni.isaac.core.utils.prims import get_prim_object_type, get_prim_at_path
import omni.usd


def build_combobox(label: str, items: list, tooltip: str = ""):
    combobox_model = DynamicComboBoxModel(items)
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=tooltip)
        combobox = ui.ComboBox(combobox_model)
        add_line_rect_flourish(False)

    return combobox


def modify_combobox_items(combobox, new_items: list, item_changed_fn=None, select_index: int = 0):
    combobox.model = DynamicComboBoxModel(new_items)
    if item_changed_fn is not None:
        combobox.model.add_item_changed_fn(item_changed_fn)
    if select_index < len(new_items):
        combobox.model.get_item_value_model().set_value(select_index)


def get_all_articulations():
    """Get all the articulation objects from the Stage.

    Returns:
        list(str): list of prim_paths as strings
    """
    articulations = ["None"]
    stage = omni.usd.get_context().get_stage()
    if stage:
        for prim in Usd.PrimRange(stage.GetPrimAtPath("/")):
            path = str(prim.GetPath())
            # Get prim type get_prim_object_type
            type = get_prim_object_type(path)
            if type == "articulation":
                articulations.append(path)

    return articulations
