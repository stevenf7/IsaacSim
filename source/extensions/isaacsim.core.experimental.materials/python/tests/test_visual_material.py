# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Literal

import isaacsim.core.utils.stage as stage_utils
import omni.kit.test
import omni.usd
from isaacsim.core.experimental.materials import (
    OmniGlassMaterial,
    OmniPbrMaterial,
    PreviewSurfaceMaterial,
    VisualMaterial,
)


async def populate_stage(max_num_prims: int, operation: Literal["wrap", "create"]) -> None:
    # create new stage
    await stage_utils.create_new_stage_async()
    # define prims
    if operation == "wrap":
        for i in range(max_num_prims):
            omni.kit.commands.execute(
                "CreatePrimWithDefaultXform",
                prim_type="SphereLight",
                prim_path=f"/World/A_{i}",
                attributes={"inputs:intensity": 30000},
                select_new_prim=False,
            )


class TestVisualMaterial(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_fetch_instances(self):
        await stage_utils.create_new_stage_async()
        # create materials
        OmniGlassMaterial("/World/material_01")
        OmniPbrMaterial("/World/material_02")
        PreviewSurfaceMaterial("/World/material_03")
        # fetch instances
        instances = VisualMaterial.fetch_instances(
            [
                "/World",
                "/World/material_01",
                "/World/material_02",
                "/World/material_03",
            ]
        )
        # check
        self.assertEqual(len(instances), 4)
        self.assertIsNone(instances[0])
        self.assertIsInstance(instances[1], OmniGlassMaterial)
        self.assertIsInstance(instances[2], OmniPbrMaterial)
        self.assertIsInstance(instances[3], PreviewSurfaceMaterial)
