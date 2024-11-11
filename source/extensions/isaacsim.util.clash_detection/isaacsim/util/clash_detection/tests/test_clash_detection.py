# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import numpy as np

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
from isaacsim.core.api.objects import GroundPlane
from isaacsim.core.prims import XFormPrim
from isaacsim.core.utils.stage import (
    add_reference_to_stage,
    create_new_stage_async,
    get_current_stage,
    update_stage_async,
)
from isaacsim.storage.native import get_assets_root_path_async
from isaacsim.util.clash_detection import ClashDetector
from pxr import Gf, UsdGeom


class TestClashDetection(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await create_new_stage_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await update_stage_async()
        await update_stage_async()
        self._stage = get_current_stage()
        self._assets_root_path = await get_assets_root_path_async()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        await update_stage_async()
        pass

    # After running each test
    async def tearDown(self):
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await update_stage_async()
        await update_stage_async()
        pass

    async def add_carters_view(self):
        asset_path = self._assets_root_path + "/Isaac/Robots/Carter/carter_v1.usd"
        locations = [0.0, 0.1, 0.4]
        for idx, location in enumerate(locations):
            carter_prim_path = f"/World/Carter_{idx}"
            add_reference_to_stage(usd_path=asset_path, prim_path=carter_prim_path)
            translations = np.array([[10 * location, 10 * location, location]])
            XFormPrim(carter_prim_path).set_local_poses(translations=translations)
        await update_stage_async()
        self._carter_prim_view = XFormPrim(prim_paths_expr="/World/Carter_*")
        pass

    async def add_mesh_cube(self, position):
        # run a test without Isaac Core dependence
        result, cube_path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
        cube_prim = self._stage.GetPrimAtPath(cube_path)
        xform = UsdGeom.Xformable(cube_prim)
        transform = xform.AddTransformOp()
        mat = Gf.Matrix4d()
        mat.SetTranslateOnly(Gf.Vec3d(position))
        transform.Set(mat)
        await update_stage_async()
        return cube_prim

    async def test_carter_prim_view_clash(self):
        plane = GroundPlane(prim_path="/World/GroundPlane", z_position=0)
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=False)
        await self.add_carters_view()
        clashes = clash_detector.detect_prim_view_clashes(self._carter_prim_view)
        self.assertEqual(len(clashes), 2)
        pass

    async def test_mesh_cubes_clash(self):
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=False)
        cube_prim_0 = await self.add_mesh_cube([0.0, 0.0, 0.0])
        self.assertFalse(clash_detector.is_prim_clashing(cube_prim_0))
        cube_prim_1 = await self.add_mesh_cube([0.0, 0.9, 0.0])
        self.assertTrue(clash_detector.is_prim_clashing(cube_prim_1))
        cube_prim_2 = await self.add_mesh_cube([10.0, 10.0, 10.0])
        self.assertFalse(clash_detector.is_prim_clashing(cube_prim_2))
        pass

    async def test_clash_data_layer_query_prim(self):
        plane = GroundPlane(prim_path="/World/GroundPlane", z_position=0)
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=True)
        # First query
        cube_prim_0 = await self.add_mesh_cube([0.0, 0.0, 0.0])
        cube_0_query_name = "cube_0"
        clash_detector.is_prim_clashing(cube_prim_0, query_name=cube_0_query_name)
        current_query_id = clash_detector.get_current_query_id()
        cube_0_query_id = clash_detector.get_query_id_by_query_name(cube_0_query_name)
        self.assertEqual(current_query_id, cube_0_query_id)
        # Second query
        cube_prim_1 = await self.add_mesh_cube([0.0, 0.9, 0.0])
        cube_1_query_name = "cube_1"
        clash_detector.is_prim_clashing(cube_prim_1, query_name=cube_1_query_name)
        current_query_id = clash_detector.get_current_query_id()
        cube_1_query_id = clash_detector.get_query_id_by_query_name(cube_1_query_name)
        self.assertEqual(current_query_id, cube_1_query_id)

    async def test_clash_data_layer_query_prim_view(self):
        plane = GroundPlane(prim_path="/World/GroundPlane", z_position=0)
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=True)
        await self.add_carters_view()
        prim_view_query_name = f"test_prim_view_query"
        clashes = clash_detector.detect_prim_view_clashes(
            self._carter_prim_view, prim_view_query_name=prim_view_query_name
        )
        prim_view_query_id = clash_detector.get_query_id_by_query_name(prim_view_query_name)
        current_prim_view_query_id = clash_detector.get_current_query_id()
        # Top level prim view query id
        self.assertEqual(prim_view_query_id, current_prim_view_query_id)
        # Individual prim ids
        prim_query_id = clash_detector.get_query_id_by_query_name(clashes[0].query_name)
        self.assertEqual(prim_query_id, 1)
        prim_query_id = clash_detector.get_query_id_by_query_name(clashes[1].query_name)
        self.assertEqual(prim_query_id, 2)
        pass
