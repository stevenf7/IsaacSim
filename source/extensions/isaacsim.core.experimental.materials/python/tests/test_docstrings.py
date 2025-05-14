# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import isaacsim.core.utils.stage as stage_utils
import isaacsim.test.docstring
import omni.usd
from isaacsim.core.experimental.materials import (
    OmniGlassMaterial,
    OmniPbrMaterial,
    PhysicsMaterial,
    PreviewSurfaceMaterial,
    RigidBodyMaterial,
    VisualMaterial,
)
from isaacsim.core.simulation_manager import SimulationManager


class TestExtensionDocstrings(isaacsim.test.docstring.AsyncDocTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # create new stage
        await stage_utils.create_new_stage_async()
        SimulationManager.set_physics_sim_device("cpu")

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        super().tearDown()

    # --------------------------------------------------------------------

    async def test_physics_material_rigid_body_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(RigidBodyMaterial)
        await self.assertDocTests(PhysicsMaterial)

    # --------------------------------------------------------------------

    async def test_visual_material_omni_glass_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(OmniGlassMaterial)
        await self.assertDocTests(VisualMaterial)

    async def test_visual_material_omni_pbr_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(OmniPbrMaterial)
        await self.assertDocTests(VisualMaterial)

    async def test_visual_material_preview_surface_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(PreviewSurfaceMaterial)
        await self.assertDocTests(VisualMaterial)
