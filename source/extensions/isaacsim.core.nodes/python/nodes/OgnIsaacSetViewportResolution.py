# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import omni
from isaacsim.core.utils.carb import set_carb_setting
from omni.kit.viewport.utility import get_active_viewport, get_viewport_from_window_name


class OgnIsaacSetViewportResolution:
    """
    Isaac Sim Set Viewport Resolution
    """

    @staticmethod
    def compute(db) -> bool:
        viewport_name = db.inputs.viewport
        if viewport_name:
            viewport_api = get_viewport_from_window_name(viewport_name)
        else:
            viewport_api = get_active_viewport()

        if viewport_api:
            viewport_api.set_texture_resolution((db.inputs.width, db.inputs.height))
            set_carb_setting(carb.settings.get_settings(), "/app/hydra/aperture/conform", 3)
            set_carb_setting(carb.settings.get_settings(), "/app/hydra/aperture/conform", 4)

        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
