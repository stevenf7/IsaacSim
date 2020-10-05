# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pxr import Usd, UsdGeom
import omni.kit.editor
import omni.usd
import omni.ext

from omni.isaac.dynamic_control import _dynamic_control
from .utils.simple_robot_controller import RobotController

# Utility function to specify the stage with the z axis as "up"
def setUpZAxis(stage):
    rootLayer = stage.GetRootLayer()
    rootLayer.SetPermissionToEdit(True)
    with Usd.EditContext(stage, rootLayer):
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        extension_name = "Simple Robot Navigation"
        menu_path = f"Window/Isaac/{extension_name}"
        self._window = omni.kit.ui.Window(
            "Simple Robot Navigation",
            960,
            300,
            menu_path=menu_path,
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._create_ui()

        self._settings = omni.kit.settings.get_settings_interface()
        self._settings.set("/persistent/physics/updateToUsd", False)
        self._settings.set("/persistent/physics/useFastCache", True)

    def _create_ui(self):
        ui_layout = omni.kit.ui.RowColumnLayout(2, True)
        self._window.layout.add_child(ui_layout)
        ui_layout.set_column_width(0, 150)
        ui_layout.set_column_width(1, 350)
        ui_layout.add_child(omni.kit.ui.Label("Intialize: "))
        self._capture_btn = ui_layout.add_child(omni.kit.ui.Button("Setup Robot"))
        self._capture_btn.set_clicked_fn(self._on_setup_fn)
        ui_layout.add_child(omni.kit.ui.Label("Move forward: "))
        self._move_btn = ui_layout.add_child(omni.kit.ui.Button("Move Robot"))
        self._move_btn.set_clicked_fn(self._on_move_fn)
        ui_layout.add_child(omni.kit.ui.Label("Rotate in-place: "))
        self._rotate_btn = ui_layout.add_child(omni.kit.ui.Button("Rotate Robot"))
        self._rotate_btn.set_clicked_fn(self._on_rotate_fn)
        ui_layout_new = omni.kit.ui.RowColumnLayout(4, True)
        self._window.layout.add_child(ui_layout_new)
        ui_layout_new.set_column_width(0, 150)
        ui_layout_new.set_column_width(1, 150)
        ui_layout_new.set_column_width(2, 150)
        ui_layout_new.set_column_width(3, 150)
        ui_layout_new.add_child(omni.kit.ui.Label("Goal: "))
        self._goal_x = omni.kit.ui.FieldDouble("", -200)
        self._goal_x.width = 100
        ui_layout_new.add_child(self._goal_x)
        self._goal_y = omni.kit.ui.FieldDouble("", -400)
        self._goal_y.width = 100
        ui_layout_new.add_child(self._goal_y)
        self._goal_theta = omni.kit.ui.FieldDouble("", 0)
        self._goal_theta.width = 100
        ui_layout_new.add_child(self._goal_theta)
        self._navigate_btn = ui_layout_new.add_child(omni.kit.ui.Button("Navigate Robot"))
        self._navigate_btn.set_clicked_fn(self._on_navigate_fn)
        self._stop_btn = ui_layout_new.add_child(omni.kit.ui.Button("Stop Robot"))
        self._stop_btn.set_clicked_fn(self._on_navigate_stop_fn)

    def _on_setup_fn(self, widget):
        print("Setup Started")
        self._stage = self._usd_context.get_stage()
        setUpZAxis(self._stage)
        self._rc = RobotController(
            self._stage,
            self._dc,
            "/World/STR_V4_Physics_Caster_Sensors",
            "/World/STR_V4_Physics_Caster_Sensors/chassis",
            ["left_wheel_joint", "right_wheel_joint"],
            [3, 3],
            [1, 0.05],
        )
        self._rc.control_setup()
        # start stepping
        self._editor_event_subscription = self._editor.subscribe_to_update_events(self._rc.update)

    def _on_move_fn(self, widget):
        print("Move Started")
        self._rc.control_command(5, 5)

    def _on_rotate_fn(self, widget):
        print("Rotate Started")
        self._rc.control_command(3, -3)

    def _on_navigate_fn(self, widget):
        print("Navigate Started")
        self._rc.set_goal(float(self._goal_x.value), float(self._goal_y.value), float(self._goal_theta.value))
        self._rc.enable_navigation(True)

    def _on_navigate_stop_fn(self, widget):
        print("Navigate Stopped")
        self._rc.enable_navigation(False)
        self._rc.control_command(0, 0)

    def on_shutdown(self):
        print("Shutting down environment grid setup")
        _dynamic_control.release_dynamic_control_interface()
