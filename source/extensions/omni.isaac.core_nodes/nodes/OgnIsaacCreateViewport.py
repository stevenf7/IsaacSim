# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
from omni.kit.viewport.utility import create_viewport_window
from omni.isaac.core.utils.viewports import get_window_from_id


class OgnIsaacCreateViewport:
    """
    Isaac Sim Create Viewport
    """

    @staticmethod
    def compute(db) -> bool:
        window = get_window_from_id(db.inputs.viewportId)
        if window is not None:
            db.outputs.viewport = window.title
            db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
            return True

        # Viewport Id not found, create one
        window = create_viewport_window()
        db.outputs.viewport = window.title
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
