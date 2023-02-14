import omni.ui as ui

from omni.isaac.ui.ui_utils import (
    btn_builder,
    state_btn_builder,
    cb_builder,
    multi_btn_builder,
    multi_cb_builder,
    multi_dropdown_builder,
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
)

import omni.physx as _physx

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
        load_btn = btn_builder(label=label, text=text, tooltip=tooltip, on_clicked_fn=self._on_click)
        load_btn.enabled = True
        return load_btn


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
