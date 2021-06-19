# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import carb
import omni.ext
import omni.ui
import omni.kit.menu

from .menu import RobotEngineBridgeMenu

EXTENSION_NAME = "Robot Engine Bridge UI"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._menu = RobotEngineBridgeMenu()

    def on_shutdown(self):
        if self._menu is not None:
            self._menu.shutdown()
            self._menu = None
