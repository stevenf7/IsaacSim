import omni.ui as ui
from omni.isaac.ui.widgets import DynamicComboBoxModel
from omni.kit.window.property.templates import LABEL_WIDTH
from omni.isaac.core.utils.prims import get_prim_object_type
from pxr import Usd

from cmath import inf
from typing import Callable

from omni.isaac.ui.ui_utils import (
    btn_builder,
    state_btn_builder,
    dropdown_builder,
    cb_builder,
    str_builder,
    float_builder,
    int_builder,
    combo_cb_str_builder,
    combo_cb_plot_builder,
    combo_cb_dropdown_builder,
    combo_cb_scrolling_frame_builder,
    combo_cb_xyz_plot_builder,
    scrolling_frame_builder,
    xyz_builder,
    color_picker_builder,
    progress_bar_builder,
    plot_builder,
    xyz_plot_builder,
    add_line_rect_flourish,
    format_tt,
)

import omni.physx as _physx
import carb
from omni.usd import get_context

from .base_ui_element_wrappers import UIWidgetWrapper


class Button(UIWidgetWrapper):
    def __init__(self, label: str, text: str, tooltip="", on_click_fn=None):
        self._on_click_fn = on_click_fn

        self.button = self._create_ui_widget(label, text, tooltip)
        super().__init__(self.button)

    def set_on_click_fn(self, function):
        self._on_click_fn = function

    def _on_click(self):
        """This function is called when the Load Button is Clicked.
		"""
        if self._on_click_fn is not None:
            self._on_click_fn()

    def _create_ui_widget(self, label: str, text: str, tooltip: str):
        btn = btn_builder(label=label, text=text, tooltip=tooltip, on_clicked_fn=self._on_click)
        btn.enabled = True
        return btn


class StateButton(UIWidgetWrapper):
    def __init__(
        self,
        label: str,
        a_text: str,
        b_text: str,
        tooltip="",
        on_a_click_fn=None,
        on_b_click_fn=None,
        physics_callback_fn=None,
    ):
        """Creates a State Button UI element.

		Args:
			label (str): _description_
			a_text (str): _description_
			b_text (str): _description_
			tooltip (str, optional): _description_. Defaults to "".
			on_a_click_fn (_type_, optional): _description_. Defaults to None.
			on_b_click_fn (_type_, optional): _description_. Defaults to None.
			physics_callback_fn (_type_, optional): _description_. Defaults to None.
		"""
        self.a_text = a_text.upper()
        self.b_text = b_text.upper()

        self._on_a_click_fn = on_a_click_fn
        self._on_b_click_fn = on_b_click_fn

        self._physics_callback_fn = physics_callback_fn
        self._physx_subscription = None
        self._physxIFace = _physx.acquire_physx_interface()

        self.state_btn = self._creat_ui_widget(label, a_text, b_text, tooltip)

        super().__init__(self.state_btn)

    def set_physics_callback_fn(self, physics_callback_fn):
        # Create a physics callback on a_click and remove it on b_click
        self._physics_callback_fn = physics_callback_fn

    def set_on_a_click_fn(self, on_a_click_fn):
        self._on_a_click_fn = on_a_click_fn

    def set_on_b_click_fn(self, on_b_click_fn):
        self._on_b_click_fn = on_b_click_fn

    def reset(self):
        self.state_btn.text = self.a_text
        self._remove_physics_callback()

    def cleanup(self):
        self._remove_physics_callback()

    def _create_physics_callback(self):
        self._physx_subscription = self._physxIFace.subscribe_physics_step_events(self._physics_callback_fn)

    def _remove_physics_callback(self):
        self._physx_subscription = None

    def _on_click(self, value):
        # Button pressed while saying a_text
        if value:
            if self._on_a_click_fn is not None:
                self._on_a_click_fn()
            if self._physics_callback_fn is not None:
                self._create_physics_callback()

        # Button pressed while saying b_text
        else:
            if self._on_b_click_fn is not None:
                self._on_b_click_fn()
            if self._physics_callback_fn is not None:
                self._remove_physics_callback()

    def _creat_ui_widget(self, label: str, a_text: str, b_text: str, tooltip: str):
        state_btn = state_btn_builder(
            label=label, a_text=a_text, b_text=b_text, tooltip=tooltip, on_clicked_fn=self._on_click
        )
        state_btn.enabled = True
        return state_btn


class DropDown(UIWidgetWrapper):
    def __init__(
        self, label: str, tooltip: str = "", populate_fn=None, on_selection_fn=None, keep_old_selections=False
    ):
        self._populate_fn = populate_fn
        self._on_selection_fn = on_selection_fn
        self._keep_old_selection = keep_old_selections
        self._items = []

        self.combobox = self._create_ui_widget(label, tooltip)
        super().__init__(self.combobox)

    def repopulate(self):
        if self._populate_fn is None:
            carb.log_warn("Unable to repopulate drop-down meny without a populate_fn being specified")
            return
        else:
            new_items = self._populate_fn()

            old_selection = self.get_selection()
            self.set_items(new_items)
            new_selection = self.get_selection()

            if self._on_selection_fn is not None and new_selection is not None and new_selection != old_selection:
                # Call the user on_selection_fn if the selection has changed as a result of repopulate()
                self._on_selection_fn(new_selection)

    def set_populate_fn(self, populate_fn, repopulate=True):
        self._populate_fn = populate_fn
        if repopulate:
            self.repopulate()

    def get_items(self):
        return self._items

    def set_items(self, items: list, select_index: int = None):
        if self._keep_old_selection and select_index is None:
            selection = self.get_selection()
            if selection is not None and selection in items:
                select_index = items.index(selection)

        self._items = items
        self.combobox.model = DynamicComboBoxModel(items)

        if select_index is not None and select_index < len(items):
            self.combobox.model.get_item_value_model().set_value(select_index)

        self.combobox.model.add_item_changed_fn(self._item_changed_fn_wrapper)

    def get_selection_index(self):
        return self.combobox.model.get_item_value_model().as_int

    def get_selection(self):
        if len(self._items) == 0:
            return None
        return self._items[self.get_selection_index()]

    def set_on_selection_fn(self, on_selection_fn):
        self._on_selection_fn = on_selection_fn

    def set_keep_old_selection(self, val: bool):
        self._keep_old_selection = val

    def set_populate_fn_to_find_all_usd_objects_of_type(self, object_type: str, repopulate=True):
        self.set_populate_fn(lambda: self._find_all_usd_objects_of_type(object_type), repopulate=repopulate)

    def _item_changed_fn_wrapper(self, model, val):
        if self._on_selection_fn is not None:
            selected_item = self._items[model.get_item_value_model().as_int]
            self._on_selection_fn(selected_item)

    def _create_ui_widget(self, label, tooltip):
        items = []
        combobox_model = DynamicComboBoxModel(items)
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=tooltip)
            combobox = ui.ComboBox(combobox_model)
            add_line_rect_flourish(False)

        self.set_on_selection_fn(self._on_selection_fn)
        return combobox

    def _find_all_usd_objects_of_type(self, obj_type: str):
        items = []
        stage = get_context().get_stage()
        if stage:
            for prim in Usd.PrimRange(stage.GetPrimAtPath("/")):
                path = str(prim.GetPath())
                # Get prim type get_prim_object_type
                type = get_prim_object_type(path)
                if type == obj_type:
                    items.append(path)

        return items


class FloatField(UIWidgetWrapper):
    def __init__(
        self,
        label,
        tooltip="",
        default_value: float = 0.0,
        step: float = 0.01,
        format: str = "%.2f",
        lower_limit: float = None,
        upper_limit: float = None,
        on_value_changed_fn: Callable = None,
    ):

        self._lower_limit = lower_limit
        self._upper_limit = upper_limit

        self._on_value_changed_fn = on_value_changed_fn

        self.float_field = self._create_ui_widget(label, tooltip, default_value, step, format)

        super().__init__(self.float_field)

    def set_value(self, val: float):
        self.float_field.model.set_value(val)

    def set_upper_limit(self, upper_limit: float):
        self._upper_limit = upper_limit

    def set_lower_limit(self, lower_limit: float):
        self._lower_limit = lower_limit

    def set_on_value_changed_fn(self, on_value_changed_fn: Callable):
        self._on_value_changed_fn = on_value_changed_fn

    def _on_value_changed_fn_wrapper(self, model):
        # Enforces upper and lower limits on value change
        model.set_max(self._upper_limit)
        model.set_min(self._lower_limit)
        val = model.get_value_as_float()
        if self._upper_limit is not None and self._upper_limit < val:
            val = self._upper_limit
            model.set_value(float(val + 1))
            return
        elif self._lower_limit is not None and self._lower_limit > val:
            val = self._lower_limit
            model.set_value(float(val - 1))
            return

        if self._on_value_changed_fn is not None:
            self._on_value_changed_fn(val)

    def _create_ui_widget(self, label, tooltip, default_value, step, format):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
            float_field = ui.FloatDrag(
                name="FloatField",
                width=ui.Fraction(1),
                height=0,
                alignment=ui.Alignment.LEFT_CENTER,
                min=-inf,
                max=inf,
                step=step,
                format=format,
            )
            float_field.model.set_value(default_value)
            add_line_rect_flourish(False)

        float_field.model.add_value_changed_fn(self._on_value_changed_fn_wrapper)
        return float_field
