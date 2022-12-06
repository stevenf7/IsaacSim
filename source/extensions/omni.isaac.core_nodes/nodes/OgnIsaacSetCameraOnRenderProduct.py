# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni
from omni.isaac.core.utils.render_product import set_camera_prim_path
import carb


class OgnIsaacSetCameraOnRenderProduct:
    """
    Isaac Sim Set Camera On Render Product
    """

    @staticmethod
    def compute(db) -> bool:
        if db.inputs.cameraPrim.path is None:
            carb.log_warn(f"No camera prim at {db.inputs.cameraPrim.path}")
            return False
        set_camera_prim_path(db.inputs.renderProductPath, db.inputs.cameraPrim.path)
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
