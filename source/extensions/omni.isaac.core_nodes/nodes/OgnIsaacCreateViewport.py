# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import omni.kit.viewport_legacy


class OgnIsaacCreateViewport:
    """
    Isaac Sim Create Viewport
    """

    @staticmethod
    def compute(db) -> bool:

        vp = omni.kit.viewport_legacy.get_viewport_interface()
        for instance in vp.get_instance_list():
            if vp.get_viewport_window(instance).get_id() == db.inputs.viewportId:
                db.outputs.viewport = vp.get_viewport_window_name(instance)
                db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
                return True

        # Viewport Id not found, create one
        instance = vp.create_instance()
        db.outputs.viewport = vp.get_viewport_window_name(instance)
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
