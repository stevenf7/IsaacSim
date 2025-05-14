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
from isaacsim.core.experimental.prims import Articulation, GeomPrim, Prim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path_async


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

    async def test_prim_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        for i in range(3):
            stage.DefinePrim(f"/World/prim_{i}", "Xform")
        # test case
        await self.assertDocTests(Prim)

    async def test_xform_prim_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        for i in range(3):
            stage.DefinePrim(f"/World/prim_{i}", "Xform")
        # test case
        await self.assertDocTests(XformPrim)

    async def test_geom_prim_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        for i in range(3):
            stage.DefinePrim(f"/World/prim_{i}", "Xform")
            stage.DefinePrim(f"/World/prim_{i}/Cube", "Cube")
        # test case
        await self.assertDocTests(GeomPrim)

    async def test_rigid_prim_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        for i in range(3):
            stage.DefinePrim(f"/World/prim_{i}", "Xform")
            stage.DefinePrim(f"/World/prim_{i}/Cube", "Cube")
        # test case
        await self.assertDocTests(RigidPrim)

    async def test_articulation_docstrings(self):
        # get assets root path
        assets_root_path = await get_assets_root_path_async()
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        for i in range(3):
            stage_utils.add_reference_to_stage(
                f"{assets_root_path}/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd",
                prim_path=f"/World/prim_{i}",
            ).GetVariantSet("Gripper").SetVariantSelection("AlternateFinger")
        # test case
        await self.assertDocTests(Articulation, stop_on_failure=False)
