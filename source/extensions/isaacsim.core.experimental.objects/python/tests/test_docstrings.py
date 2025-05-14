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
from isaacsim.core.experimental.objects import (
    Capsule,
    Cone,
    Cube,
    Cylinder,
    CylinderLight,
    DiskLight,
    DistantLight,
    DomeLight,
    Light,
    Mesh,
    RectLight,
    Shape,
    Sphere,
    SphereLight,
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

    async def test_mesh_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Mesh)

    # --------------------------------------------------------------------

    async def test_capsule_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Capsule)
        await self.assertDocTests(Shape)

    async def test_cone_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Cone)
        await self.assertDocTests(Shape)

    async def test_cube_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Cube)
        await self.assertDocTests(Shape)

    async def test_cylinder_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Cylinder)
        await self.assertDocTests(Shape)

    async def test_sphere_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(Sphere)
        await self.assertDocTests(Shape)

    # --------------------------------------------------------------------

    async def test_cylinder_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(CylinderLight)
        await self.assertDocTests(Light)

    async def test_disk_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(DiskLight)
        await self.assertDocTests(Light)

    async def test_distant_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(DistantLight)
        await self.assertDocTests(Light)

    async def test_dome_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(DomeLight)
        await self.assertDocTests(Light)

    async def test_rect_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(RectLight)
        await self.assertDocTests(Light)

    async def test_sphere_light_docstrings(self):
        # define prims
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim(f"/World", "Xform")
        # test case
        await self.assertDocTests(SphereLight)
        await self.assertDocTests(Light)
