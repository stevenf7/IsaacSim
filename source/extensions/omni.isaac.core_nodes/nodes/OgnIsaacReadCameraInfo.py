# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
import omni.kit.viewport_legacy


class OgnIsaacReadCameraInfo:
    """
    Isaac Sim Camera Info Node
    """

    @staticmethod
    def compute(db) -> bool:

        viewport_name = db.inputs.viewport
        vp = omni.kit.viewport_legacy.get_viewport_interface()

        if viewport_name:
            instance = vp.get_instance(viewport_name)
            viewport_window = vp.get_viewport_window(instance)
        else:
            viewport_window = vp.get_viewport_window()

        if not viewport_window:
            return True

        db.outputs.width, db.outputs.height = viewport_window.get_texture_resolution()
        stage = omni.usd.get_context().get_stage()
        camera = stage.GetPrimAtPath(viewport_window.get_active_camera())
        db.outputs.focalLength = camera.GetAttribute("focalLength").Get()

        db.outputs.horizontalAperture = camera.GetAttribute("horizontalAperture").Get()
        db.outputs.verticalAperture = camera.GetAttribute("verticalAperture").Get()

        db.outputs.horizontalOffset = camera.GetAttribute("horizontalApertureOffset").Get()
        db.outputs.verticalOffset = camera.GetAttribute("verticalApertureOffset").Get()

        db.outputs.projectionType = "pinhole"

        return True
