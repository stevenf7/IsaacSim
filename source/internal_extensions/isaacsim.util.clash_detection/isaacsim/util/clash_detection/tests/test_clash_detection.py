# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the clash detection engine."""

import carb
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.test
from isaacsim.core.experimental.objects import GroundPlane
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.storage.native import get_assets_root_path_async
from isaacsim.util.clash_detection import ClashDetector
from pxr import Gf, Usd, UsdGeom


class TestClashDetection(omni.kit.test.AsyncTestCase):
    """Test suite for the clash detection engine."""

    # Before running each test
    async def setUp(self) -> None:
        """Set up the test environment with a new stage."""
        await stage_utils.create_new_stage_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await app_utils.update_app_async()
        await app_utils.update_app_async()
        self._stage = stage_utils.get_current_stage()
        self._assets_root_path = await get_assets_root_path_async()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        await app_utils.update_app_async()

    # After running each test
    async def tearDown(self) -> None:
        """Clean up after each test by waiting for stage loading to complete."""
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await app_utils.update_app_async()
        await app_utils.update_app_async()

    async def add_carters_view(self) -> None:
        """Add multiple Carter robots to the stage for prim view testing."""
        asset_path = self._assets_root_path + "/Isaac/Robots/NVIDIA/Carter/carter_v1.usd"
        locations = [0.0, 0.1, 0.4]
        for idx, location in enumerate(locations):
            carter_prim_path = f"/World/Carter_{idx}"
            stage_utils.add_reference_to_stage(usd_path=asset_path, path=carter_prim_path)
            translations = np.array([[10 * location, 10 * location, location]])
            XformPrim(carter_prim_path, reset_xform_op_properties=True).set_local_poses(translations=translations)
        await app_utils.update_app_async()
        self._carter_prim_view = XformPrim("/World/Carter_.*")

    async def add_mesh_cube(self, position: tuple[float, float, float] | list[float]) -> Usd.Prim:
        """Add a mesh cube at the given position and return its prim.

        Args:
            position: Translation to apply to the mesh cube.

        Returns:
            Created USD cube prim.
        """
        # run a test without Isaac Core dependence
        result, cube_path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
        cube_prim = self._stage.GetPrimAtPath(cube_path)
        xform = UsdGeom.Xformable(cube_prim)
        transform = xform.AddTransformOp()
        mat = Gf.Matrix4d()
        mat.SetTranslateOnly(Gf.Vec3d(position))
        transform.Set(mat)
        await app_utils.update_app_async()
        return cube_prim

    async def test_carter_prim_view_clash(self) -> None:
        """Test clash detection with Carter robot prim views."""
        GroundPlane("/World/GroundPlane")
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=False)
        await self.add_carters_view()
        clashes = clash_detector.detect_prim_view_clashes(self._carter_prim_view)
        self.assertEqual(len(clashes), 2)

    async def test_mesh_cubes_clash(self) -> None:
        """Test clash detection between overlapping and non-overlapping mesh cubes."""
        clash_detector = ClashDetector(stage=self._stage, logging=False, clash_data_layer=False)
        cube_prim_0 = await self.add_mesh_cube([0.0, 0.0, 0.0])
        self.assertFalse(clash_detector.is_prim_clashing(cube_prim_0))
        cube_prim_1 = await self.add_mesh_cube([0.0, 0.9, 0.0])
        self.assertTrue(clash_detector.is_prim_clashing(cube_prim_1))
        cube_prim_2 = await self.add_mesh_cube([10.0, 10.0, 10.0])
        self.assertFalse(clash_detector.is_prim_clashing(cube_prim_2))

    async def test_clash_data_layer_query_prim(self) -> None:
        """Test clash data layer query tracking for individual prims."""
        GroundPlane("/World/GroundPlane")
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

    async def test_clash_data_layer_query_prim_view(self) -> None:
        """Test clash data layer query tracking for prim views."""
        GroundPlane("/World/GroundPlane")
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
