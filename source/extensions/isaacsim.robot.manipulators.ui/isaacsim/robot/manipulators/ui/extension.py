# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import omni.ext
from omni.kit.menu.utils import MenuHelperExtensionFull

from .menu_graphs import ArticulationPositionWindow, ArticulationVelocityWindow, GripperWindow


class Extension(omni.ext.IExt, MenuHelperExtensionFull):
    def on_startup(self, ext_id: str):

        # Create menu using MenuHelperExtensionFull
        self.menu_startup(
            lambda: ArticulationPositionWindow(),
            "Articulation Position Controller",
            "Joint Position",
            "Tools/Robotics/OmniGraph Controllers",
        )
        self.menu_startup(
            lambda: ArticulationVelocityWindow(),
            "Articulation Velocity Controller",
            "Joint Velocity",
            "Tools/Robotics/OmniGraph Controllers",
        )
        self.menu_startup(
            lambda: GripperWindow(), "Gripper Controller", "Open Loop Gripper", "Tools/Robotics/OmniGraph Controllers"
        )

    def on_shutdown(self):
        self.menu_shutdown()
