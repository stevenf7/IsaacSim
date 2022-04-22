# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni
import numpy as np
import random
from omni.isaac.core.utils.nucleus import get_assets_root_path
from pxr import UsdGeom

import omni.isaac.dr as dr

TRANSLATION_RANGE = 200.0
SCALE = 20.0


class RandomScenario:
    def __init__(self):
        self.stage = omni.usd.get_context().get_stage()

    def setup_world(self):
        # Add a distant light
        self.stage.DefinePrim("/World/Light", "DistantLight")

        # Create 10 randomly positioned and coloured spheres and cube
        # We will assign each a semantic label based on their shape (sphere/cube)
        prim_path_list = []
        for i in range(5):
            prim_type = random.choice(["Cube", "Sphere"])
            prim_path = f"/World/cube{i}"
            prim_path_list.append(prim_path)
            prim = self.stage.DefinePrim(prim_path, prim_type)
            translation = np.random.rand(3) * TRANSLATION_RANGE
            UsdGeom.XformCommonAPI(prim).SetTranslate(translation.tolist())
            UsdGeom.XformCommonAPI(prim).SetScale((SCALE, SCALE, SCALE))
            prim.GetAttribute("primvars:displayColor").Set([np.random.rand(3).tolist()])

            # Add semantic label based on prim type
            # sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
            # sem.CreateSemanticTypeAttr()
            # sem.CreateSemanticDataAttr()
            # sem.GetSemanticTypeAttr().Set("class")
            # sem.GetSemanticDataAttr().Set(prim_type)

    def add_simple_room_scene(self):
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            return
        omni.usd.get_context().close_stage_with_callback(
            lambda a, b: omni.usd.get_context().open_stage(
                assets_root_path + "/Samples/DR/Stage/simple_room_sample.usd", None
            )
        )

    def add_warehouse_scene(self):
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            return
        omni.usd.get_context().close_stage_with_callback(
            lambda a, b: omni.usd.get_context().open_stage(
                assets_root_path + "/Samples/Synthetic_Data/Stage/warehouse_with_sensors.usd", None
            )
        )

    def add_dr(self, idx):
        if idx == 0:
            dr.commands.CreateColorComponentCommand().do()
        elif idx == 1:
            self._assets_root_path = get_assets_root_path()
            dr.commands.CreateTextureComponentCommand(
                enable_project_uvw=True,
                texture_list=[
                    self._assets_root_path + "/Samples/DR/Materials/Textures/checkered.png",
                    self._assets_root_path + "/Samples/DR/Materials/Textures/marble_tile.png",
                    self._assets_root_path + "/Samples/DR/Materials/Textures/picture_a.png",
                    self._assets_root_path + "/Samples/DR/Materials/Textures/picture_b.png",
                    self._assets_root_path + "/Samples/DR/Materials/Textures/textured_wall.png",
                    self._assets_root_path + "/Samples/DR/Materials/Textures/checkered_color.png",
                ],
            ).do()
        elif idx == 2:
            camera_prim_path = "/World/Camera"
            self.stage.DefinePrim(camera_prim_path, "Camera")
            dr.commands.CreateMovementComponentCommand(prim_paths=[camera_prim_path]).do()
        elif idx == 3:
            dr.commands.CreateLightComponentCommand().do()
        elif idx == 4:
            dr.commands.CreateTransformComponentCommand().do()

    def preview_scene(self):
        dr.commands.ToggleManualModeCommand().do()
        dr.commands.RandomizeOnceCommand().do()
        dr.commands.ToggleManualModeCommand().do()
