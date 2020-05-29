# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb.input
from pxr import Usd, UsdGeom
import omni.kit.commands
import omni.kit.editor
import omni.ext
import omni.kit.ui
import omni.kit.settings

from omni.isaac.motion_planning import _motion_planning
from omni.isaac.dynamic_control import _dynamic_control
from omni.physx import _physx

from .ur10_scenarios.scenario import Scenario
from .ur10_scenarios import bin_stack
from .ur10_scenarios import bmw_fof_demo
from .ur10_scenarios.fill_bin import FillBin


EXTENSION_NAME = "UR10 Preview"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._window = omni.kit.ui.Window(
            EXTENSION_NAME,
            300,
            200,
            menu_path="Isaac Robotics/Samples/" + EXTENSION_NAME,
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        self._window.set_update_fn(self._on_update_ui)

        self._first_step = True
        self._is_playing = False

        self._mp = _motion_planning.acquire_motion_planning_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._physxIFace = _physx.acquire_physx_interface()

        self._selected_scenario = self._window.layout.add_child(omni.kit.ui.ComboBox())
        self._selected_scenario.add_item("Stack Bins")
        self._selected_scenario.add_item("BMW FoF Demo")
        self._selected_scenario.add_item("Fill Bin")
        self._selected_scenario.selected_index = 0

        self._create_UR10_btn = self._window.layout.add_child(omni.kit.ui.Button("Create Scenario"))
        self._create_UR10_btn.set_clicked_fn(self._on_create_UR10)

        self._perform_task_btn = self._window.layout.add_child(omni.kit.ui.Button("Perform Task"))
        self._perform_task_btn.set_clicked_fn(self._on_perform_task)
        self._perform_task_btn.enabled = False

        self._stop_task_btn = self._window.layout.add_child(omni.kit.ui.Button("Reset Task"))
        self._stop_task_btn.set_clicked_fn(self._on_stop_tasks)
        self._stop_task_btn.enabled = False

        self._pause_task_btn = self._window.layout.add_child(omni.kit.ui.Button("Pause Task"))
        self._pause_task_btn.set_clicked_fn(self._on_pause_tasks)
        self._pause_task_btn.enabled = False

        self._open_gripper_btn = self._window.layout.add_child(omni.kit.ui.Button("Close/Open Gripper"))
        self._open_gripper_btn.set_clicked_fn(self._on_open_gripper)
        self._open_gripper_btn.enabled = False

        self._add_new_trays_btn = self._window.layout.add_child(omni.kit.ui.Button("Add New tray"))
        self._add_new_trays_btn.set_clicked_fn(self._on_add_tray)
        self._add_new_trays_btn.enabled = False

        self._settings = omni.kit.settings.get_settings_interface()

        self._settings.set("/app/renderer/gpuSynchronization", False)
        self._settings.set("/persistent/app/stage/upAxis", "Z")

        self._settings.set("/persistent/physics/updateToUsd", False)
        self._settings.set("/persistent/physics/useFastCache", True)
        self._settings.set("/persistent/physics/numThreads", 8)
        self._settings.set("/physics/timeStepsPerSecond", 60.0)

        self._physxIFace.overwrite_gpu_setting(0)

        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)
        self._sub_stage_event = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event
        )
        self._scenario = Scenario(self._editor, self._dc, self._mp)

    def _on_create_UR10(self, *args):
        if self._selected_scenario.selected_index == 0:
            self._scenario = bin_stack.BinStack(self._editor, self._dc, self._mp)
            self._editor.set_camera_position("/OmniverseKit_Persp", 370, 135, 60, True)
            self._editor.set_camera_target("/OmniverseKit_Persp", -83.41, -126.78, -80.28, True)
        if self._selected_scenario.selected_index == 1:
            self._scenario = bmw_fof_demo.AttachBody(self._editor, self._dc, self._mp)
            self._editor.set_camera_position("/OmniverseKit_Persp", 370, 135, 60, True)
            self._editor.set_camera_target("/OmniverseKit_Persp", -83.41, -126.78, -80.28, True)
        if self._selected_scenario.selected_index == 2:
            self._scenario = FillBin(self._editor, self._dc, self._mp)
            self._add_new_trays_btn.text = "Drop Parts"
            self._editor.set_camera_position("/OmniverseKit_Persp", -142.07, 284.72, 111.53, True)
            self._editor.set_camera_target("/OmniverseKit_Persp", -140.6, 282.7, 110.6, True)

        self._first_step = True
        self._create_UR10_btn.enabled = False
        self._selected_scenario.enabled = False

        self._editor.stop()
        self._physxIFace.release_physics_objects()

        self._settings.set("/rtx/reflections/halfRes", True)
        self._settings.set("/rtx/shadows/denoiser/quarterRes", True)
        self._settings.set("/rtx/translucency/reflectionCutoff", 0.1)

        self._scenario.create_UR10()

        self._physxIFace.release_physics_objects()
        self._physxIFace.force_load_physics_from_usd()

        self._editor_event_subscription = self._editor.subscribe_to_update_events(self._on_editor_step)
        self._physxIFace.release_physics_objects()
        self._physxIFace.force_load_physics_from_usd()
        self._stop_task_btn.enabled = True
        self._pause_task_btn.enabled = True
        self._add_new_trays_btn.enabled = True

    def _on_stop_tasks(self, *args):
        self._scenario.stop_tasks()

    def _on_pause_tasks(self, *args):
        self._open_gripper_btn.enabled = self._scenario.pause_tasks()
        self._perform_task_btn.enabled = not self._open_gripper_btn.enabled
        self._stop_task_btn.enabled = True

    def _on_open_gripper(self, *args):
        self._scenario.open_gripper()

    def _on_add_tray(self, *args):
        self._scenario.add_tray()

    def _sub_keyboard_event(self, event, *args, **kwargs):
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input == carb.input.KeyboardInput.KEY_1:
                self._on_perform_task()
            if event.input == carb.input.KeyboardInput.KEY_2:
                self._on_pause_tasks()
            if event.input == carb.input.KeyboardInput.KEY_3:
                self._on_add_tray()
        return True

    def _on_editor_step(self, step):
        if self._editor.is_playing():
            if self._first_step:
                self._scenario.register_assets()
                self._first_step = False
            self._scenario.step(step)

    def _on_stage_event(self, event):
        self.stage = self._usd_context.get_stage()
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._create_UR10_btn.enabled = True
            self._selected_scenario.enabled = True
            self._perform_task_btn.enabled = False
            self._stop_task_btn.enabled = False
            self._pause_task_btn.enabled = False
            self._open_gripper_btn.enabled = False
            self._add_new_trays_btn.enabled = False
            self._editor.stop()
            self._on_stop_tasks()
            self._scenario = Scenario(self._editor, self._dc, self._mp)

    def _on_perform_task(self, *args):
        self._perform_task_btn.enabled = False
        self._pause_task_btn.enabled = True
        self._stop_task_btn.enabled = True
        self._open_gripper_btn.enabled = False
        self._scenario.perform_tasks()

    def _on_update_ui(self, widget):
        is_stopped = self._editor.is_stopped()
        if is_stopped and self._is_playing:
            self._on_stop_tasks()
        self._is_playing = not is_stopped

        if self._editor.is_playing() or self._scenario.is_created():
            self._create_UR10_btn.enabled = False
            self._perform_task_btn.enabled = True
            self._add_new_trays_btn.enabled = True
            self._perform_task_btn.text = "Perform Task"
            if not self._scenario.is_created():
                self._perform_task_btn.enabled = False
                self._perform_task_btn.text = "Press Create To Enable"
        if not self._editor.is_playing():
            self._perform_task_btn.enabled = False
            self._open_gripper_btn.enabled = False
            self._add_new_trays_btn.enabled = False
            self._perform_task_btn.text = "Press Play To Enable"
            if not self._scenario.is_created():
                self._create_UR10_btn.enabled = True
                self._perform_task_btn.text = "Press Create To Enable"

    def on_shutdown(self):
        self._editor.stop()
        self._on_stop_tasks()
        self._scenario = None
        self._editor_event_subscription = None
        self._input.unsubscribe_to_keyboard_events(self._keyboard, self._sub_keyboard)
        self._window.set_update_fn(None)
        print("Shutting down")
