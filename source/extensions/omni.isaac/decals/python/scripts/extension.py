import os

from pxr import Usd, UsdGeom, Sdf, Gf, Tf, PhysicsSchemaTools

import carb
import omni.ext
import omni.usd
import omni.kit.ui
import omni.kit.editor
from .. import _decals

EXTENSION_NAME = "Decals"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._decals = _decals.acquire()

        menu_path = f"Window/{EXTENSION_NAME}"
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._selection = self._usd_context.get_selection()
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 600, menu_path=menu_path)
        self._build_window_ui()
        self._x = 0.0

    def on_shutdown(self):
        return

    def _build_window_ui(self):
        enabled_checkbox = omni.kit.ui.CheckBox("Decals Enabled")
        enabled_checkbox.set_on_changed_fn(self._on_enabled_checkbox_changed_fn)
        self._window.layout.add_child(enabled_checkbox)
        picking_checkbox = omni.kit.ui.CheckBox("Picking Enabled")
        picking_checkbox.set_on_changed_fn(self._on_picking_enabled_checkbox_changed_fn)
        self._window.layout.add_child(picking_checkbox)
        color_picker = omni.kit.ui.ColorRgb("Pen Color", value=(1, 0, 0))
        color_picker.width = 400
        color_picker.set_on_changed_fn(self._on_color_picker_changed_fn)
        self._window.layout.add_child(color_picker)
        width_value = omni.kit.ui.DragDouble("Trace Width", value=5, min=0.0, max=10, drag_speed=0.05)
        width_value.width = 200
        width_value.set_on_changed_fn(self._on_width_value_changed_fn)
        self._window.layout.add_child(width_value)
        offset_value = omni.kit.ui.DragDouble("Trace Offset", value=0.01, min=0, max=1.0, drag_speed=0.0005)
        offset_value.width = 200
        offset_value.set_on_changed_fn(self._on_offset_value_changed_fn)
        self._window.layout.add_child(offset_value)
        threshold_value = omni.kit.ui.DragDouble("Trace Threshold", value=10.0, min=0, max=10, drag_speed=0.05)
        threshold_value.width = 200
        threshold_value.set_on_changed_fn(self._on_threshold_value_changed_fn)
        self._window.layout.add_child(threshold_value)
        erase_selected_button = omni.kit.ui.Button("Erase from Selected")
        erase_selected_button.set_clicked_fn(self._erase_selected_button_clicked_fn)
        self._window.layout.add_child(erase_selected_button)
        erase_all_button = omni.kit.ui.Button("Erase All")
        erase_all_button.set_clicked_fn(self._erase_all_button_clicked_fn)
        self._window.layout.add_child(erase_all_button)
        test_button = omni.kit.ui.Button("Run Tests")
        test_button.set_clicked_fn(self._test_button_clicked_fn)
        self._window.layout.add_child(test_button)

    def _on_enabled_checkbox_changed_fn(self, value):
        self._decals.set_enabled(value)

    def _on_picking_enabled_checkbox_changed_fn(self, value):
        self._decals.set_picking_enabled(value)

    def _on_color_picker_changed_fn(self, value):
        self._decals.set_pen_color(value.r, value.g, value.b)

    def _on_width_value_changed_fn(self, value):
        self._decals.set_pen_width(value)

    def _on_offset_value_changed_fn(self, value):
        self._decals.set_pen_offset(value)

    def _on_threshold_value_changed_fn(self, value):
        self._decals.set_pen_threshold(value)

    def _erase_selected_button_clicked_fn(self, widget):
        selected_paths = list(self._selection.get_selected_prim_paths())
        for path in selected_paths:
            self._decals.erase_surface(path)

    def _erase_all_button_clicked_fn(self, widget):
        self._decals.erase_all_surfaces()

    def _test_button_clicked_fn(self, widget):
        self._decals.run_tests()
