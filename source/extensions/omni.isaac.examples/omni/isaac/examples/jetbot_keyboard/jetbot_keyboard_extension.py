# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.examples.base_sample import BaseSampleExtension
from omni.isaac.examples.jetbot_keyboard import JetbotKeyboard


class JetbotKeyboardExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        overview = "This Example shows how to simulate an NVIDIA Jetbot robot in Isaac Sim."
        overview += "\n\tKeybord Input:"
        overview += "\n\t\tw: Forward"
        overview += "\n\t\ts: Reverse"
        overview += "\n\t\ta: Spin Left"
        overview += "\n\t\td: Spin Right"
        overview += "\n\nPress the 'Open in IDE' button to view the source code."

        super().start_extension(
            menu_name="Input Devices",
            submenu_name="",
            name="Jetbot Keyboard",
            title="NVIDIA Jetbot Navigation Example",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_jetbot.html",
            overview=overview,
            file_path=os.path.abspath(__file__),
            stage_units_in_meters=0.01,
            sample=JetbotKeyboard(),
        )
