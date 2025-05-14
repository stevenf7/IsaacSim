# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from .grasping_window import GraspingWindow


class GraspingUIExtension(omni.ext.IExt, MenuHelperExtensionFull):
    WINDOW_NAME = "Grasping"
    MENU_GROUP = "Tools/Replicator"

    def on_startup(self, ext_id: str):
        self.menu_startup(
            lambda: GraspingWindow(title=self.WINDOW_NAME),
            self.WINDOW_NAME,
            self.WINDOW_NAME,
            self.MENU_GROUP,
        )

    def on_shutdown(self):
        self.menu_shutdown()
