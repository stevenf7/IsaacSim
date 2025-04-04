# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio

import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import MenuHelperExtensionFull

from .synthetic_recorder_window import SyntheticRecorderWindow


class SyntheticRecorderExtension(omni.ext.IExt, MenuHelperExtensionFull):
    WINDOW_NAME = "Synthetic Data Recorder"
    MENU_GROUP = "Tools/Replicator"

    def on_startup(self, ext_id):
        # Add the menu item
        self.menu_startup(
            lambda: SyntheticRecorderWindow(SyntheticRecorderExtension.WINDOW_NAME, ext_id),
            SyntheticRecorderExtension.WINDOW_NAME,
            SyntheticRecorderExtension.WINDOW_NAME,
            SyntheticRecorderExtension.MENU_GROUP,
        )

    def on_shutdown(self):
        self.menu_shutdown()
