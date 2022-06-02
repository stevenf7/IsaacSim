# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import omni.kit.viewport_legacy


class OgnIsaacSetViewportResolution:
    """
    Isaac Sim Set Viewport Resolution
    """

    @staticmethod
    def compute(db) -> bool:
        vp = omni.kit.viewport_legacy.get_viewport_interface()
        for instance in vp.get_instance_list():
            if vp.get_viewport_window_name(instance) == db.inputs.viewport:
                window = vp.get_viewport_window(instance)
                window.set_texture_resolution(db.inputs.width, db.inputs.height)
                db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
                return True
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
