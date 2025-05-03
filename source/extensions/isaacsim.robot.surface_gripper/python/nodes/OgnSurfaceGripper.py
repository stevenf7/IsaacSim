# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from math import radians

import isaacsim.robot.surface_gripper._surface_gripper as surface_gripper
import numpy as np
import omni
import omni.graph.core as og
import omni.physics.tensors
import omni.physx as _physx
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade


class OgnSurfaceGripper:

    @staticmethod
    def compute(db) -> bool:
        gripper_interface = surface_gripper.acquire_surface_gripper_interface()
        if db.inputs.enabled and len(db.inputs.SurfaceGripper) > 0:
            input_prim = db.inputs.SurfaceGripper[0].pathString
            status = gripper_interface.get_gripper_status(input_prim)
            if status == "Open":
                gripper_interface.close_gripper(input_prim)
            else:
                gripper_interface.open_gripper(input_prim)
