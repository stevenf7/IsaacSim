# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import omni.graph.core as og
import omni.kit.commands
import pxr
from pxr import Usd, UsdGeom, UsdPhysics
from usd.schema.isaac import robot_schema


class CreateSurfaceGripper(omni.kit.commands.Command):
    """Creates Action graph containing a Surface Gripper node, and all prims to facilitate its creation

    Typical usage example:

    .. code-block:: python

        result, prim  = omni.kit.commands.execute(
                "CreateSurfaceGripper",
                prim_path="/SurfaceGripper",
            )
    """

    def __init__(self, prim_path: str = ""):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = None
        stage = omni.usd.get_context().get_stage()
        if prim_path == "":
            selection = omni.usd.get_context().get_selection()
            paths = selection.get_selected_prim_paths()
            if paths:
                prim_path = paths[0]
            else:
                default_prim = stage.GetDefaultPrim()
                if default_prim is None:
                    # If no default prim, create at root level
                    prim_path = "/"
                else:
                    prim_path = str(default_prim.GetPath())
        self._prim_path = omni.usd.get_stage_next_free_path(stage, prim_path + "/SurfaceGripper", False)
        pass

    def do(self):
        self._prim = robot_schema.CreateSurfaceGripper(self._stage, self._prim_path)
        return self._prim

    def undo(self):
        if self._prim:
            return self._stage.RemovePrim(self._prim_path)
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
