# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.ui.ui_utils import setup_ui_headers, get_style, btn_builder
from omni.isaac.samples.scripts.base_sample import BaseSampleExtension
from omni.isaac.samples.scripts.follow_target import FollowTarget
import asyncio
import omni.ui as ui


class FollowTargetExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Controlling",
            submenu_name="Manipulation",
            name="Follow Target",
            buttons_mapping={},
            title="Follow Target Controller",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            overview="This Example shows how to follow a target using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
            stage_units_in_meters=0.01,
            sample=FollowTarget(),
            file_path=os.path.abspath(__file__),
        )
        self.task_buttons = {}
        frame = self.get_extra_frame()
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

                self.task_buttons["Follow Target"] = btn_builder(**dict)
                self.task_buttons["Follow Target"].enabled = False
                dict = {
                    "label": "Add Obstacle",
                    "type": "button",
                    "text": "Add Obstacle",
                    "tooltip": "Add Obstacle",
                    "on_clicked_fn": self._on_add_obstacle_button_event,
                }

                self.task_buttons["Add Obstacle"] = btn_builder(**dict)
                self.task_buttons["Add Obstacle"].enabled = False
                dict = {
                    "label": "Remove Obstacle",
                    "type": "button",
                    "text": "Remove Obstacle",
                    "tooltip": "Remove Obstacle",
                    "on_clicked_fn": self._on_remove_obstacle_button_event,
                }

                self.task_buttons["Remove Obstacle"] = btn_builder(**dict)
                self.task_buttons["Remove Obstacle"].enabled = False
        return

    def _on_follow_target_button_event(self):
        asyncio.ensure_future(self.sample._on_follow_target_event_async())
        self.task_buttons["Follow Target"].enabled = False
        return

    def _on_add_obstacle_button_event(self):
        self.sample._on_add_obstacle_event()
        self.task_buttons["Remove Obstacle"].enabled = True
        return

    def _on_remove_obstacle_button_event(self):
        self.sample._on_remove_obstacle_event()
        world = self.sample.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        if not current_task.obstacles_exist():
            self.task_buttons["Remove Obstacle"].enabled = False
        return

    def on_reset(self):
        self.task_buttons["Follow Target"].enabled = True
        self.task_buttons["Remove Obstacle"].enabled = False
        self.task_buttons["Add Obstacle"].enabled = True
        return

    def on_load(self):
        self.task_buttons["Follow Target"].enabled = True
        self.task_buttons["Add Obstacle"].enabled = True
        return

    def on_clear(self):
        self.task_buttons["Follow Target"].enabled = False
        self.task_buttons["Remove Obstacle"].enabled = False
        self.task_buttons["Add Obstacle"].enabled = False
        return
