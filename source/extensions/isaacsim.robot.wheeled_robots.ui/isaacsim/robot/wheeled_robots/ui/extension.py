# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import gc

import omni.ext
from omni.kit.menu.utils import MenuHelperExtensionFull

from .menu_graphs import DifferentialControllerWindow


class Extension(omni.ext.IExt, MenuHelperExtensionFull):
    def on_startup(self, ext_id: str):

        # Create menu using MenuHelperExtensionFull
        self.menu_startup(
            lambda: DifferentialControllerWindow(),
            "Differential Controller",
            "Differential Controller",
            "Tools/Robotics/OmniGraph Controllers",
        )

    def on_shutdown(self):
        self.menu_shutdown()
        gc.collect()
