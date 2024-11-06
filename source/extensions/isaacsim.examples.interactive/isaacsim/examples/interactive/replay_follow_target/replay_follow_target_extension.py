# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import os

import omni.ui as ui
from isaacsim.examples.interactive.base_sample import BaseSampleExtension
from isaacsim.examples.interactive.replay_follow_target import ReplayFollowTarget
from isaacsim.gui.components.ui_utils import btn_builder, str_builder


class ReplayFollowTargetExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Manipulation",
            submenu_name="",
            name="Replay Follow Target",
            title="Replay Follow Target Task",
            doc_link="https://docs.omniverse.nvidia.com/isaacsim/latest/core_api_tutorials/tutorial_advanced_data_logging.html",
            overview="This Example shows how to use data logging to replay data collected\n\n from the follow target extension example.\n\n Press the 'Open in IDE' button to view the source code.",
            sample=ReplayFollowTarget(),
            file_path=os.path.abspath(__file__),
        )
        return

    def build_ui(self):
        extra_stacks = self.build_default_frame()
        self.build_extra_frames(extra_stacks)

    def build_extra_frames(self, extra_stacks):
        self.task_ui_elements = {}
        with extra_stacks:
            with ui.CollapsableFrame(
                title="Task Control",
                width=ui.Fraction(0.33),
                height=0,
                visible=True,
                collapsed=False,
                # style=get_style(),
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
            ):
                self.build_data_logging_ui()

    def _on_replay_trajectory_button_event(self):
        asyncio.ensure_future(
            self.sample._on_replay_trajectory_event_async(self.task_ui_elements["Data File"].get_value_as_string())
        )
        self.task_ui_elements["Replay Trajectory"].enabled = False
        self.task_ui_elements["Replay Scene"].enabled = False
        return

    def _on_replay_scene_button_event(self):
        asyncio.ensure_future(
            self.sample._on_replay_scene_event_async(self.task_ui_elements["Data File"].get_value_as_string())
        )
        self.task_ui_elements["Replay Trajectory"].enabled = False
        self.task_ui_elements["Replay Scene"].enabled = False
        return

    def post_reset_button_event(self):
        self.task_ui_elements["Replay Trajectory"].enabled = True
        self.task_ui_elements["Replay Scene"].enabled = True
        return

    def post_load_button_event(self):
        self.task_ui_elements["Replay Trajectory"].enabled = True
        self.task_ui_elements["Replay Scene"].enabled = True
        return

    def post_clear_button_event(self):
        self.task_ui_elements["Replay Trajectory"].enabled = False
        self.task_ui_elements["Replay Scene"].enabled = False
        return

    def build_data_logging_ui(self):
        with ui.VStack(spacing=5):
            example_data_file = os.path.abspath(
                os.path.join(os.path.abspath(__file__), "../../../../../data/example_data_file.json")
            )
            dict = {
                "label": "Data File",
                "type": "stringfield",
                "default_val": example_data_file,
                "tooltip": "Data File",
                "on_clicked_fn": None,
                "use_folder_picker": False,
                "read_only": False,
            }
            self.task_ui_elements["Data File"] = str_builder(**dict)
            dict = {
                "label": "Replay Trajectory",
                "type": "button",
                "text": "Replay Trajectory",
                "tooltip": "Replay Trajectory",
                "on_clicked_fn": self._on_replay_trajectory_button_event,
            }

            self.task_ui_elements["Replay Trajectory"] = btn_builder(**dict)
            self.task_ui_elements["Replay Trajectory"].enabled = False
            dict = {
                "label": "Replay Scene",
                "type": "button",
                "text": "Replay Scene",
                "tooltip": "Replay Scene",
                "on_clicked_fn": self._on_replay_scene_button_event,
            }

            self.task_ui_elements["Replay Scene"] = btn_builder(**dict)
            self.task_ui_elements["Replay Scene"].enabled = False
        return
