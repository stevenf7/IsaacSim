# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext

# import omni.kit.editor
# import omni.kit.ui
import carb.settings
from .. import _manip
from enum import IntEnum
from functools import partial
from pxr import Sdf

EXTENSION_NAME = "Gamepad Binding"

control_slider_range = 200.0

joystick_deadzone = 0.2


def clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def input_to_control(input, input_min, input_max):
    input_range = input_max - input_min
    if input_range == 0.0:
        input_range = 1.0
    return (input - input_min) * control_slider_range / input_range


class GamePadAxis(IntEnum):
    eNone = -1

    eLeftStickX = 0
    eLeftStickY = 1
    eRightStickX = 2
    eRightStickY = 3
    eLeftTrigger = 4
    eRightTrigger = 5

    eCount = 6


class GamePadBinding:
    def __init__(
        self, axis, input_min, input_max, control, value_min, value_max, speed_scale, use_speed, prim_path, attr_name
    ):
        self.axis = axis
        self.input_min = input_min
        self.input_max = input_max
        # values stored in widgets
        self.control = control
        self.value_min = value_min
        self.value_max = value_max
        self.speed_scale = speed_scale
        self.use_speed = use_speed
        self.prim_path = prim_path
        self.attr_name = attr_name
        # cached values
        self.vel = 0.0
        self.attr = None

    def __del__(self):
        self.attr_name.set_on_changed_fn(None)
        self.control.set_on_changed_fn(None)


class Extension(omni.ext.IExt):
    def update_binding(self, binding, input):
        if binding.attr is None:
            return
        input_range = binding.input_max - binding.input_min
        if input_range == 0.0:
            input_range = 1.0
        if binding.use_speed.value is False:
            binding.attr.Set(
                (input - binding.input_min) * (binding.value_max.value - binding.value_min.value) / input_range
                + binding.value_min.value
            )
            binding.vel = 0.0
        else:
            binding.vel = (2 * (input - binding.input_min) / input_range - 1.0) * binding.speed_scale.value

    def on_gamepad_event_fn(self, axis, input):
        if axis < 0 or axis >= len(self.bindings):
            return
        binding = self.bindings[axis]
        if binding.use_speed.value is True:
            if abs(input) < joystick_deadzone:
                input = 0.0
        self.update_binding(binding, input)
        binding.control.value = input_to_control(input, binding.input_min, binding.input_max)

    def on_control_slider_changed_fn(self, slider, slider_value):
        axis = slider.user_data["index"]
        if axis < 0 or axis >= len(self.bindings):
            return
        binding = self.bindings[axis]
        input = slider_value * (binding.input_max - binding.input_min) / control_slider_range + binding.input_min
        self.update_binding(binding, input)

    def on_update(self, dt):
        for binding in self.bindings:
            if binding.use_speed.value and binding.attr is not None:
                current = binding.attr.Get()
                if current is not None:
                    binding.attr.Set(
                        clamp(current + dt * binding.vel, binding.value_min.value, binding.value_max.value)
                    )

    def stage_event_fn(self, event):
        if event.type == int(omni.usd.StageEventType.OPENED):
            self.load_bindings()
        return

    def on_startup(self):
        self.manip = None
        self.editor = None
        self.usd_context = None
        self.window = None
        self.update_sub = None
        self.stage_sub = None
        self.bindings = []
        self.manip = _manip.acquire_manip_interface()

        self.editor = omni.kit.editor.get_editor_interface()
        self.usd_context = omni.usd.get_context()
        self.window = omni.kit.ui.Window(
            EXTENSION_NAME, 960, 600, menu_path=f"Window/Isaac/{EXTENSION_NAME}", open=False
        )
        self.manip.bind_gamepad(self.on_gamepad_event_fn)
        self.update_sub = self.editor.subscribe_to_update_events(self.on_update)
        self.build_window_ui()
        self.stage_sub = self.usd_context.get_stage_event_stream().create_subscription_to_pop(self.stage_event_fn)

        self._settings = carb.settings.get_settings()
        self._settings.set("/persistent/app/omniverse/gamepadCameraControl", False)

    def on_shutdown(self):
        self.stage_sub = None
        self.update_sub = None
        if self.manip is not None:
            self.manip.unbind_gamepad()
            _manip.release_manip_interface(self.manip)
            self.manip = None
        for binding in self.bindings:
            del binding
        self.bindings = []
        del self.window
        self.window = None

    def bind_attribute(self, index):
        binding = self.bindings[index]
        selected = ""
        if (
            binding.attr_name.selected_index >= 0
            and binding.attr_name.selected_index < binding.attr_name.get_item_count()
        ):
            selected = binding.attr_name.get_item_at(binding.attr_name.selected_index)
        stage = self.usd_context.get_stage()
        prim = stage.GetPrimAtPath(binding.prim_path.text)
        if prim.IsValid():
            binding.attr = prim.GetAttribute(selected)
        else:
            binding.attr = None

    def on_prim_path_changed_fn(self, prim_path):
        index = prim_path.user_data["index"]
        attr_name = self.bindings[index].attr_name
        attr_name.clear_items()
        attr_name.selected_index = -1
        stage = self.usd_context.get_stage()
        prim = stage.GetPrimAtPath(prim_path.text)
        if prim.IsValid():
            for attr in prim.GetAttributes():
                if attr.GetTypeName() == Sdf.ValueTypeNames.Float:
                    if len(attr.GetNamespace()) > 0:
                        attr_name.add_item(attr.GetNamespace() + ":" + attr.GetBaseName())
                    else:
                        attr_name.add_item(attr.GetBaseName())
        self.bind_attribute(index)

    def on_button_s_fn(self, button):
        index = button.user_data["index"]
        prim_path = self.bindings[index].prim_path
        selected = self.usd_context.get_selection().get_selected_prim_paths()
        if len(selected) != 0:
            stage = self.usd_context.get_stage()
            prim = stage.GetPrimAtPath(selected[0])
            if prim.IsValid():
                prim_path.text = selected[0]
            self.on_prim_path_changed_fn(prim_path)

    def on_button_x_fn(self, button):
        index = button.user_data["index"]
        self.bindings[index].prim_path.text = ""
        self.bindings[index].attr_name.clear_items()
        self.bindings[index].attr_name.selected_index = -1
        self.bind_attribute(index)

    def on_attr_name_selcted_fn(self, attr_name, value):
        self.bind_attribute(attr_name.user_data["index"])

    def load_bindings(self):
        stage = self.usd_context.get_stage()
        for binding in self.bindings:
            prim = stage.GetPrimAtPath(Sdf.Path("/GamepadBindings/" + GamePadAxis(binding.axis).name))
            if prim.IsValid():
                attr = prim.GetAttribute("value_min")
                if attr.IsValid():
                    binding.value_min.value = attr.Get()
                attr = prim.GetAttribute("value_max")
                if attr.IsValid():
                    binding.value_max.value = attr.Get()
                attr = prim.GetAttribute("control_speed_scale")
                if attr.IsValid():
                    binding.speed_scale.value = attr.Get()
                attr = prim.GetAttribute("use_velocity_control")
                if attr.IsValid():
                    binding.use_speed.value = attr.Get()
                attr = prim.GetAttribute("prim_path")
                if attr.IsValid():
                    binding.prim_path.text = attr.Get()
                    self.on_prim_path_changed_fn(binding.prim_path)
                attr = prim.GetAttribute("attr_name")
                if attr.IsValid():
                    attr_name = attr.Get()
                    selected_index = -1
                    for i in range(binding.attr_name.get_item_count()):
                        if binding.attr_name.get_item_at(i) == attr_name:
                            selected_index = i
                            break
                    binding.attr_name.selected_index = selected_index

    def on_save_clicked_fn(self, button):
        stage = self.usd_context.get_stage()
        for binding in self.bindings:
            prim = stage.DefinePrim(Sdf.Path("/GamepadBindings/" + GamePadAxis(binding.axis).name))
            prim.CreateAttribute("value_min", Sdf.ValueTypeNames.Float, True).Set(binding.value_min.value)
            prim.CreateAttribute("value_max", Sdf.ValueTypeNames.Float, True).Set(binding.value_max.value)
            prim.CreateAttribute("control_speed_scale", Sdf.ValueTypeNames.Float, True).Set(binding.speed_scale.value)
            prim.CreateAttribute("use_velocity_control", Sdf.ValueTypeNames.Bool, True).Set(binding.use_speed.value)
            prim.CreateAttribute("prim_path", Sdf.ValueTypeNames.String, True).Set(binding.prim_path.text)
            selected = ""
            if (
                binding.attr_name.selected_index >= 0
                and binding.attr_name.selected_index < binding.attr_name.get_item_count()
            ):
                selected = binding.attr_name.get_item_at(binding.attr_name.selected_index)
            prim.CreateAttribute("attr_name", Sdf.ValueTypeNames.String, True).Set(selected)

    def add_binding_row(self, layout, name, axis, input_min, input_max):
        row_index = len(self.bindings)

        # Create the row widgets

        # ... label
        label = omni.kit.ui.Label(name)

        # ... control slider
        control = omni.kit.ui.SliderDouble("", input_to_control(0.0, input_min, input_max), 0.0, control_slider_range)
        control.format = ""
        control.width = int(control_slider_range)
        control.user_data["index"] = row_index
        control.set_on_changed_fn(partial(self.on_control_slider_changed_fn, control))

        # ... min value
        value_min = omni.kit.ui.DragDouble("", input_min, -100, 100)
        value_min.format = "%.2f"
        value_min.width = 50
        value_min.user_data["index"] = row_index

        # ... "to" label
        to_label = omni.kit.ui.Label("to")

        # ... max value
        value_max = omni.kit.ui.DragDouble("", input_max, -100, 100)
        value_max.format = "%.2f"
        value_max.width = 50
        value_max.user_data["index"] = row_index

        # ... speed scale
        speed_scale = omni.kit.ui.DragDouble("Vel:", 1, 0, 10)
        speed_scale.format = "%.2f"
        speed_scale.width = 50
        speed_scale.user_data["index"] = row_index

        # ... checkbox to use speed scale
        if axis < GamePadAxis.eLeftTrigger:
            use_speed = omni.kit.ui.CheckBox("", True)
        else:
            use_speed = omni.kit.ui.CheckBox("", False)

        # ... "Path" label
        path_label = omni.kit.ui.Label("Path:")

        # ... prim path
        prim_path = omni.kit.ui.TextBox("")
        prim_path.user_data["index"] = row_index
        prim_path.set_text_changed_fn(self.on_prim_path_changed_fn)

        # ... "Set Selected" button
        button_s = omni.kit.ui.Button("Set Selected")
        button_s.user_data["index"] = row_index
        button_s.set_clicked_fn(self.on_button_s_fn)

        # ... "X" (clear) button
        button_x = omni.kit.ui.Button("X")
        button_x.user_data["index"] = row_index
        button_x.set_clicked_fn(self.on_button_x_fn)

        # ... attribute
        attr_name = omni.kit.ui.ComboBox("Attribute:")
        attr_name.user_data["index"] = row_index
        attr_name.width = 150
        attr_name.set_on_changed_fn(partial(self.on_attr_name_selcted_fn, attr_name))

        # Create a binding object
        binding = GamePadBinding(
            axis, input_min, input_max, control, value_min, value_max, speed_scale, use_speed, prim_path, attr_name
        )
        self.bindings.append(binding)

        # Add the widgets to the layout
        layout.add_child(label)
        layout.add_child(control)
        layout.add_child(value_min)
        layout.add_child(to_label)
        layout.add_child(value_max)
        if axis < GamePadAxis.eLeftTrigger:
            layout.add_child(speed_scale)
            layout.add_child(use_speed)
        else:
            layout.add_child(omni.kit.ui.Label(""))
            layout.add_child(omni.kit.ui.Label(""))
        layout.add_child(path_label)
        layout.add_child(prim_path)
        layout.add_child(button_s)
        layout.add_child(button_x)
        layout.add_child(attr_name)

    def build_window_ui(self):
        col_layout = omni.kit.ui.RowColumnLayout(12, False)
        col_layout.set_column_width(0, 65)  # Controller label
        col_layout.set_column_width(1, 210)  # Slider
        col_layout.set_column_width(2, 60)  # Range Min DragDouble
        col_layout.set_column_width(3, 30)  # "to"
        col_layout.set_column_width(4, 70)  # Range Max DragDouble
        col_layout.set_column_width(5, 88)  # Speed scale
        col_layout.set_column_width(6, 45)  # Speed checkbox
        col_layout.set_column_width(7, 45)  # "Path"
        col_layout.set_column_width(8, 220)  # Path TextBox
        col_layout.set_column_width(9, 94)  # "Set Selected" button
        col_layout.set_column_width(10, 50)  # "Remove" button
        col_layout.set_column_width(11, 218)  # Attribute TextBox
        self.window.layout.add_child(col_layout)
        self.add_binding_row(col_layout, "L stick X", GamePadAxis.eLeftStickX, -1.0, 1.0)
        self.add_binding_row(col_layout, "L stick Y", GamePadAxis.eLeftStickY, -1.0, 1.0)
        self.add_binding_row(col_layout, "R stick X", GamePadAxis.eRightStickX, -1.0, 1.0)
        self.add_binding_row(col_layout, "R stick Y", GamePadAxis.eRightStickY, -1.0, 1.0)
        self.add_binding_row(col_layout, "L trigger", GamePadAxis.eLeftTrigger, 0.0, 1.0)
        self.add_binding_row(col_layout, "R trigger", GamePadAxis.eRightTrigger, 0.0, 1.0)
        # Add some space
        self.window.layout.add_child(omni.kit.ui.Spacer(0))
        # create save button
        save_button = omni.kit.ui.Button("Save to Stage")
        save_button.set_clicked_fn(self.on_save_clicked_fn)
        self.window.layout.add_child(save_button)
