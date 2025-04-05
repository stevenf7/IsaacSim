# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni
from isaacsim.core.utils.viewports import get_id_from_index, get_window_from_id
from omni.kit.viewport.utility import create_viewport_window, get_active_viewport_window


class OgnIsaacCreateViewportInternalState:
    def __init__(self):
        self.window = None


class OgnIsaacCreateViewport:
    """
    Isaac Sim Create Viewport
    """

    @staticmethod
    def internal_state():
        return OgnIsaacCreateViewportInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.per_instance_state
        if state.window is None:
            if len(db.inputs.name) > 0:
                state.window = create_viewport_window(db.inputs.name)
            else:
                if db.inputs.viewportId == 0:
                    state.window = get_active_viewport_window()
                else:
                    state.window = create_viewport_window(str(db.inputs.viewportId))
        db.outputs.viewport = state.window.title
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
