# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
__all__ = ["IconScene"]

import carb.input
import carb.settings
import omni.ui as ui
from omni.ui import scene as sc

from .manipulator import IconManipulator, PreventOthers
from .model import IconModel

VISIBLE_SETTING = "/persistent/app/viewport/sensor_icon/visible"


class IconScene:  # pragma: no cover
    """The window with the manupulator"""

    def __init__(self, title: str = None, icon_scale: float = 1.0, **kwargs):
        self._sensor_icon = SensorIcon.get_instance()
        self._manipulater = IconManipulator(
            model=self._sensor_icon.get_model(),
            aspect_ratio_policy=sc.AspectRatioPolicy.PRESERVE_ASPECT_HORIZONTAL,
            icon_scale=icon_scale,
        )
        prevent_others = PreventOthers()

        # we don't want the prim icon show outside the viewport area
        # so we need do check on end drag,
        # don't check it on change(dragging) to get a better performance
        right_drag_gesture = sc.DragGesture(
            name="SensorIcon_look_drag",
            on_ended_fn=lambda sender: self._end_drag(sender),
            mouse_button=1,  # hook right button
            manager=prevent_others,
        )

        left_drag_gesture = sc.DragGesture(
            name="SensorIcon_navigation_drag",  # naigation bar use left button to drag
            on_ended_fn=lambda sender: self._end_drag(sender),
            mouse_button=0,  # hook left button
            manager=prevent_others,
        )

        # TODO: This would cause crash when click the prim icon,
        # note it until find a better solution
        # self._screen = sc.Screen(gestures=[
        #     right_drag_gesture,
        #     left_drag_gesture
        # ])
        self.visible = True

    def _end_drag(self, sender):
        self._manipulater.rebuild_icons(need_check=True)

    @property
    def visible(self):
        return self._manipulater.visible

    @visible.setter
    def visible(self, value: bool):
        value = bool(value)
        # self._model.beam_visible = value
        self._manipulater.visible = value

    def destroy(self):
        self.clear()
        self._manipulater = None

    def clear(self):
        if not self._manipulater:
            return
        self._manipulater.clear()

    def __del__(self):
        self.destroy()


class SensorIcon:
    _instance = None

    def __init__(self, test=False):
        self.model = IconModel()
        self._settings = carb.settings.get_settings()
        self._visible_sub = self._settings.subscribe_to_node_change_events(VISIBLE_SETTING, self._on_visible_changed)
        self.toggle_all_fn = []

    def _on_visible_changed(self, *args):
        if not self.model:
            return

        visible = self._settings.get(VISIBLE_SETTING)
        if visible:
            self.model.show_all()
        else:
            self.model.hide_all()
        for fn in self.toggle_all_fn:
            fn(visible)

    def register_toggle_all_fn(self, fn):
        self.toggle_all_fn.append(fn)

    def unregister_toggle_all_fn(self, fn):
        self.toggle_all_fn.remove(fn)

    @staticmethod
    def get_instance():
        if not SensorIcon._instance:
            SensorIcon._instance = SensorIcon()
        return SensorIcon._instance

    def destroy(self):
        self.clear()
        self.model = None
        SensorIcon._instance = None

    def get_model(self):
        return self.model

    def add_sensor_icon(self, prim_path, icon_url=None):
        if not self.model:
            return
        self.model.add_sensor_icon(prim_path, icon_url)

    def remove_sensor_icon(self, prim_path):
        if not self.model:
            return
        self.model.remove_sensor_icon(prim_path)

    def set_icon_click_fn(self, prim_path, call_back):
        if not self.model:
            return
        self.model.set_icon_click_fn(prim_path, call_back)

    def show_sensor_icon(self, prim_path):
        if not self.model:
            return
        self.model.show_sensor_icon(prim_path)

    def hide_sensor_icon(self, prim_path):
        if not self.model:
            return
        self.model.hide_sensor_icon(prim_path)

    def clear(self):
        if not self.model:
            return
        self.model.clear()
