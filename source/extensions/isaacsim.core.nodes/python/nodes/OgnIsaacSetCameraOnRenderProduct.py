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
from isaacsim.core.utils.render_product import set_camera_prim_path


class OgnIsaacSetCameraOnRenderProduct:
    """
    Isaac Sim Set Camera On Render Product
    """

    @staticmethod
    def compute(db) -> bool:
        if len(db.inputs.cameraPrim) == 0:
            db.log_error(f"Camera prim must be specified")
            return False
        set_camera_prim_path(db.inputs.renderProductPath, db.inputs.cameraPrim[0].GetString())
        db.outputs.execOut = omni.graph.core.ExecutionAttributeState.ENABLED
        return True
