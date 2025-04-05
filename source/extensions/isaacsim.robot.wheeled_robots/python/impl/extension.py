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
import omni.kit.commands
from isaacsim.robot.wheeled_robots.bindings._isaacsim_robot_wheeled_robots import (
    acquire_wheeled_robots_interface,
    release_wheeled_robots_interface,
)


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        # we need to acquire the interface to actually load the plugin, otherwise the DifferentialController can't be found
        self.__interface = acquire_wheeled_robots_interface()

    def on_shutdown(self):
        release_wheeled_robots_interface(self.__interface)
