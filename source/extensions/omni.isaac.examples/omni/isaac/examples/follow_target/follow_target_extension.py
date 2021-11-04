# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.examples.base_sample import BaseSampleExtension
from omni.isaac.examples.follow_target import FollowTarget
import asyncio
import omni.ui as ui
from omni.isaac.ui.ui_utils import btn_builder, str_builder


class FollowTargetExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Manipulation",
            submenu_name="",
            name="Follow Target",
            title="Follow Target Task",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            overview="This Example shows how to follow a target using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
            stage_units_in_meters=0.01,
            sample=FollowTarget(),
            file_path=os.path.abspath(__file__),
            number_of_extra_frames=2,
            window_width=700,
        )
        self.task_ui_elements = {}
        frame = self.get_frame(index=0)
        self.build_task_controls_ui(frame)
        frame = self.get_frame(index=1)
        self.build_data_logging_ui(frame)
        return

    def _on_follow_target_button_event(self):
        asyncio.ensure_future(self.sample._on_follow_target_event_async())
        self.task_ui_elements["Follow Target"].enabled = False
        return

    def _on_add_obstacle_button_event(self):
        self.sample._on_add_obstacle_event()
        self.task_ui_elements["Remove Obstacle"].enabled = True
        return

    def _on_remove_obstacle_button_event(self):
        self.sample._on_remove_obstacle_event()
        world = self.sample.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        if not current_task.obstacles_exist():
            self.task_ui_elements["Remove Obstacle"].enabled = False
        return

    def _on_start_logging_button_event(self):
        self.sample._on_start_logging_event()
        self.task_ui_elements["Save Data"].enabled = True
        self.task_ui_elements["Start Logging"].enabled = False
        return

    def _on_save_data_button_event(self):
        self.sample._on_save_data_event(self.task_ui_elements["Output Directory"].get_value_as_string())
        self.task_ui_elements["Save Data"].enabled = False
        self.task_ui_elements["Start Logging"].enabled = True
        return

    def post_reset_button_event(self):
        self.task_ui_elements["Follow Target"].enabled = True
        self.task_ui_elements["Remove Obstacle"].enabled = False
        self.task_ui_elements["Add Obstacle"].enabled = True
        self.task_ui_elements["Start Logging"].enabled = True
        self.task_ui_elements["Save Data"].enabled = False
        return

    def post_load_button_event(self):
        self.task_ui_elements["Follow Target"].enabled = True
        self.task_ui_elements["Add Obstacle"].enabled = True
        self.task_ui_elements["Start Logging"].enabled = True
        self.task_ui_elements["Save Data"].enabled = False
        return

    def post_clear_button_event(self):
        self.task_ui_elements["Follow Target"].enabled = False
        self.task_ui_elements["Remove Obstacle"].enabled = False
        self.task_ui_elements["Add Obstacle"].enabled = False
        self.task_ui_elements["Start Logging"].enabled = False
        self.task_ui_elements["Save Data"].enabled = False
        return

    def shutdown_cleanup(self):
        return

    def build_task_controls_ui(self, frame):
        with frame:
            with ui.VStack(spacing=5):
                # Update the Frame Title
                frame.title = "Task Controls"
                frame.visible = True
                dict = {
                    "label": "Follow Target",
                    "type": "button",
                    "text": "Follow Target",
                    "tooltip": "Follow Target",
                    "on_clicked_fn": self._on_follow_target_button_event,
                }

                self.task_ui_elements["Follow Target"] = btn_builder(**dict)
                self.task_ui_elements["Follow Target"].enabled = False
                dict = {
                    "label": "Add Obstacle",
                    "type": "button",
                    "text": "Add Obstacle",
                    "tooltip": "Add Obstacle",
                    "on_clicked_fn": self._on_add_obstacle_button_event,
                }

                self.task_ui_elements["Add Obstacle"] = btn_builder(**dict)
                self.task_ui_elements["Add Obstacle"].enabled = False
                dict = {
                    "label": "Remove Obstacle",
                    "type": "button",
                    "text": "Remove Obstacle",
                    "tooltip": "Remove Obstacle",
                    "on_clicked_fn": self._on_remove_obstacle_button_event,
                }

                self.task_ui_elements["Remove Obstacle"] = btn_builder(**dict)
                self.task_ui_elements["Remove Obstacle"].enabled = False

    def build_data_logging_ui(self, frame):
        with frame:
            with ui.VStack(spacing=5):
                frame.title = "Data Logging"
                frame.visible = True
                dict = {
                    "label": "Output Directory",
                    "type": "stringfield",
                    "default_val": os.path.join(os.getcwd(), "output_data.json"),
                    "tooltip": "Output Directory",
                    "on_clicked_fn": None,
                    "use_folder_picker": False,
                    "read_only": False,
                }
                self.task_ui_elements["Output Directory"] = str_builder(**dict)
                dict = {
                    "label": "Start Logging",
                    "type": "button",
                    "text": "Start Logging",
                    "tooltip": "Start Logging",
                    "on_clicked_fn": self._on_start_logging_button_event,
                }

                self.task_ui_elements["Start Logging"] = btn_builder(**dict)
                self.task_ui_elements["Start Logging"].enabled = False
                dict = {
                    "label": "Save Data",
                    "type": "button",
                    "text": "Save Data",
                    "tooltip": "Save Data",
                    "on_clicked_fn": self._on_save_data_button_event,
                }

                self.task_ui_elements["Save Data"] = btn_builder(**dict)
                self.task_ui_elements["Save Data"].enabled = False
        return
