# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.kit.app
import omni.usd
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.examples.interactive.base_sample import BaseSample


class GettingStarted(BaseSample):
    def __init__(self) -> None:
        super().__init__()

        return

    @property
    def name(self):
        return "Getting Started"

    def setup_scene(self):
        pass

    async def setup_post_load(self):
        set_camera_view(eye=[5.0, 2.0, 2.5], target=[0.00, 0.00, 0.00], camera_prim_path="/OmniverseKit_Persp")

        return

    async def setup_pre_reset(self):
        return

    async def setup_post_reset(self):
        return

    def world_cleanup(self):

        return
