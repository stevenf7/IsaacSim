# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import gc
import asyncio
import weakref
import os
import omni.physx as _physx
from .sample import Replay

EXTENSION_NAME = "Replay Sample"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._window = ui.Window(EXTENSION_NAME, width=400, height=175, visible=False)
        self._window.set_visibility_changed_fn(self._on_window)

        menu_items = [
            MenuItemDescription(name="RMP Replay Example", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Manipulation", sub_menu=menu_items)]
            )
        ]

        add_menu_items(self._menu_items, "Isaac Examples")
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()
        self._replay = Replay()
        # Simple button style that grays out the button if disabled
        self._button_style = {":disabled": {"color": 0xFF000000}}
        with self._window.frame:
            with omni.ui.VStack(style=self._button_style, height=0):
                ui.Label("Loads a trajectory created by the RMP Example")
                self._create_robot_btn = ui.Button("Load Robot", height=0, enabled=True)
                self._create_robot_btn.set_clicked_fn(self._on_setup_environment)
                self._create_robot_btn.set_tooltip("Load robot and environment")
                self._reset_btn = ui.Button("Press Play To Enable", height=0, enabled=False)
                self._reset_btn.set_clicked_fn(self._replay.reset)
                self._reset_btn.set_tooltip("Reset Robot to default position")

                with ui.HStack(height=0, spacing=5):
                    ui.Label("Input File:", width=0)
                    default_dir = os.path.join(os.getcwd(), "output.txt")
                    self._ui_dir_name = ui.StringField()
                    self._ui_dir_name.model.set_value(default_dir)
                    self._ui_dir_name.model.add_end_edit_fn(
                        self._replay.save_dir(self._ui_dir_name.model.get_value_as_string())
                    )
                self._replay_data_btn = ui.Button("Press Play To Enable", enabled=False, height=0)
                self._replay_data_btn.set_clicked_fn(self._replay.replay_data)
                self._replay_data_btn.set_tooltip("Replay trajectory from file")

    def _on_window(self, status):
        if status:
            self._sub_stage_event = (
                omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
            )
            self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
            self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
                self._on_timeline_event
            )
        else:
            self._sub_stage_event = None
            self._physx_subs = None
            self._timeline_sub = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_stage_event(self, event):
        """This function is called when stage events occur.
        Enables UI elements when stage is opened.
        Prevents tasks from being started until all assets are loaded

        Arguments:
            event (int): event type
        """
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._create_robot_btn.enabled = True
            self._reset_btn.enabled = False
            self._replay_data_btn.enabled = False

            self._timeline.stop()
            self._replay.stop_tasks()

    def _on_simulation_step(self, step):
        if self._replay.created:
            self._create_robot_btn.text = "Reload Robot"
            if self._timeline.is_playing():
                self._replay.step(step)
                if self._replay._replay_data:
                    self._replay_data_btn.text = "Stop Playing Trajectories"
                else:
                    self._replay_data_btn.text = "Play Trajectories"
                    self._ui_dir_name.model.add_end_edit_fn(
                        self._replay.save_dir(self._ui_dir_name.model.get_value_as_string())
                    )

            else:
                self._replay_data_btn.text = "Press Play To Enable"
        else:
            self._create_robot_btn.text = "Load Robot"
            self._reset_btn.text = "Reset Robot Pose"
            self._replay_data_btn.text = "Press Play To Enable"

    def _on_timeline_event(self, e):
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            self._replay_data_btn.enabled = True
            self._reset_btn.enabled = True
            self._reset_btn.text = "Reset Robot Pose"
            self._replay_data_btn.text = "Play Trajectories"

        if e.type == int(omni.timeline.TimelineEventType.STOP) or e.type == int(omni.timeline.TimelineEventType.PAUSE):
            self._replay_data_btn.enabled = False
            self._reset_btn.enabled = False
            self._reset_btn.text = "Press Play To Enable"
            self._replay_data_btn.text = "Press Play To Enable"

    def _on_setup_environment(self):
        self._timeline.stop()
        asyncio.ensure_future(self._on_create_robot())

    async def _on_create_robot(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._replay.create_robot()
        self._viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

        self._reset_btn.enabled = True
        self._replay_data_btn.enabled = True

    def on_shutdown(self):
        self._physx_subs = None
        self._sub_stage_event = None
        self._timeline_sub = None

        self._timeline.stop()
        self._replay.stop_tasks()
        self._replay = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        gc.collect()
        pass
