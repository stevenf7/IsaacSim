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
from isaacsim.examples.interactive.bin_filling import BinFilling
from isaacsim.gui.components.ui_utils import btn_builder


class BinFillingExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Manipulation",
            submenu_name="",
            name="Bin Filling",
            title="Bin Filling",
            doc_link="https://docs.omniverse.nvidia.com/isaacsim/latest/core_api_tutorials/tutorial_core_adding_manipulator.html",
            overview="This Example shows how to do bin filling using UR10 robot in Isaac Sim.\n It showcases a realistic surface gripper that breaks with heavy bin load.\nPress the 'Open in IDE' button to view the source code.",
            sample=BinFilling(),
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
                self.build_task_controls_ui()

    def _on_fill_bin_button_event(self):
        asyncio.ensure_future(self.sample.on_fill_bin_event_async())
        self.task_ui_elements["Start Bin Filling"].enabled = False
        return

    def post_reset_button_event(self):
        self.task_ui_elements["Start Bin Filling"].enabled = True
        return

    def post_load_button_event(self):
        self.task_ui_elements["Start Bin Filling"].enabled = True
        return

    def post_clear_button_event(self):
        self.task_ui_elements["Start Bin Filling"].enabled = False
        return

    def build_task_controls_ui(self):
        with ui.VStack(spacing=5):

            dict = {
                "label": "Start Bin Filling",
                "type": "button",
                "text": "Start Bin Filling",
                "tooltip": "Start Bin Filling",
                "on_clicked_fn": self._on_fill_bin_button_event,
            }

            self.task_ui_elements["Start Bin Filling"] = btn_builder(**dict)
            self.task_ui_elements["Start Bin Filling"].enabled = False
