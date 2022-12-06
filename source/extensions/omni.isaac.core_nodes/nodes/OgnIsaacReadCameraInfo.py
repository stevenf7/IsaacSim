# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
from omni.kit.viewport.utility import get_viewport_from_window_name, get_active_viewport
from omni.isaac.core.utils.render_product import get_camera_prim_path, get_resolution


class OgnIsaacReadCameraInfo:
    """
    Isaac Sim Camera Info Node
    """

    @staticmethod
    def compute(db) -> bool:
        stage = omni.usd.get_context().get_stage()

        if db.inputs.viewport:
            db.log_warn(
                "viewport input is deprecated, please use renderProductPath and the IsaacGetViewportRenderProduct to get a viewports render product path"
            )
            viewport_name = db.inputs.viewport
            if viewport_name:
                viewport_api = get_viewport_from_window_name(viewport_name)
            else:
                viewport_api = get_active_viewport()
            if viewport_api:
                camera = stage.GetPrimAtPath(viewport_api.get_active_camera())
                (db.outputs.width, db.outputs.height) = viewport_api.get_texture_resolution()
        else:
            render_product_path = db.inputs.renderProductPath
            camera = stage.GetPrimAtPath(get_camera_prim_path(render_product_path))
            (db.outputs.width, db.outputs.height) = get_resolution(render_product_path)

        db.outputs.focalLength = camera.GetAttribute("focalLength").Get()

        db.outputs.horizontalAperture = camera.GetAttribute("horizontalAperture").Get()
        db.outputs.verticalAperture = camera.GetAttribute("verticalAperture").Get()

        db.outputs.horizontalOffset = camera.GetAttribute("horizontalApertureOffset").Get()
        db.outputs.verticalOffset = camera.GetAttribute("verticalApertureOffset").Get()

        projection_type = camera.GetAttribute("cameraProjectionType").Get()
        if projection_type is None:
            projection_type = "pinhole"

        db.outputs.projectionType = projection_type
        if projection_type is not "pinhole":
            db.outputs.cameraFisheyeParams = [
                camera.GetAttribute("fthetaWidth"),
                camera.GetAttribute("fthetaHeight"),
                camera.GetAttribute("fthetaCx"),
                camera.GetAttribute("fthetaCy"),
                camera.GetAttribute("fthetaMaxFov"),
                camera.GetAttribute("fthetaPolyA"),
                camera.GetAttribute("fthetaPolyB"),
                camera.GetAttribute("fthetaPolyC"),
                camera.GetAttribute("fthetaPolyD"),
                camera.GetAttribute("fthetaPolyE"),
            ]
        else:
            db.outputs.cameraFisheyeParams = [0.0] * 10

        return True
