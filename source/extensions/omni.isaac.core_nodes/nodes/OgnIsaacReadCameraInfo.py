# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
from omni.kit.viewport.utility import get_viewport_from_window_name, get_active_viewport


class OgnIsaacReadCameraInfo:
    """
    Isaac Sim Camera Info Node
    """

    @staticmethod
    def compute(db) -> bool:

        viewport_name = db.inputs.viewport

        if viewport_name:
            viewport_api = get_viewport_from_window_name(viewport_name)
        else:
            viewport_api = get_active_viewport()

        if viewport_api:
            (db.outputs.width, db.outputs.height) = viewport_api.get_texture_resolution()
            stage = omni.usd.get_context().get_stage()
            camera = stage.GetPrimAtPath(viewport_api.get_active_camera())
            db.outputs.focalLength = camera.GetAttribute("focalLength").Get()

            db.outputs.horizontalAperture = camera.GetAttribute("horizontalAperture").Get()
            db.outputs.verticalAperture = camera.GetAttribute("verticalAperture").Get()

            db.outputs.horizontalOffset = camera.GetAttribute("horizontalApertureOffset").Get()
            db.outputs.verticalOffset = camera.GetAttribute("verticalApertureOffset").Get()

            db.outputs.projectionType = "pinhole"

        return True
