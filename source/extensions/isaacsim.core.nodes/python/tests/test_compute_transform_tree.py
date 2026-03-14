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

import asyncio

import omni.graph.core as og
import omni.graph.core.tests as ogts
import omni.kit.test
import omni.usd
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from pxr import UsdGeom
from usdrt import Sdf


async def _add_rigid_prim(stage, path, positions, orientations=None, size=1.0):
    """Add a rigid body prim at path so IsaacComputeTransformTree's discovery does not log errors."""
    cube_geom = UsdGeom.Cube.Define(stage, path)
    cube_geom.CreateSizeAttr(size)
    await omni.kit.app.get_app().next_update_async()
    RigidPrim(
        path,
        positions=positions,
        orientations=orientations,
        masses=1.0,
        reset_xform_op_properties=True,
    )
    await omni.kit.app.get_app().next_update_async()
    GeomPrim(path, apply_collision_apis=True)
    await omni.kit.app.get_app().next_update_async()


class TestIsaacComputeTransformTree(ogts.OmniGraphTestCase):
    GRAPH_PATH = "/ActionGraph"
    NODE_NAME = "ComputeTransformTree"
    NODE_TYPE = "isaacsim.core.nodes.IsaacComputeTransformTree"

    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()

    async def tearDown(self):
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await asyncio.sleep(0.5)
        await omni.kit.app.get_app().next_update_async()

    def _create_graph(self, target_prim_paths, parent_prim_path=None):
        set_values = [
            (f"{self.NODE_NAME}.inputs:targetPrims", [Sdf.Path(p) for p in target_prim_paths]),
        ]
        if parent_prim_path:
            set_values.append((f"{self.NODE_NAME}.inputs:parentPrim", [Sdf.Path(parent_prim_path)]))

        og.Controller.edit(
            {"graph_path": self.GRAPH_PATH, "evaluator_name": "execution"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    (self.NODE_NAME, self.NODE_TYPE),
                ],
                og.Controller.Keys.SET_VALUES: set_values,
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", f"{self.NODE_NAME}.inputs:execIn"),
                ],
            },
        )

    def _get_outputs(self):
        return {
            "parentFrames": og.Controller.get(f"{self.GRAPH_PATH}/{self.NODE_NAME}.outputs:parentFrames"),
            "childFrames": og.Controller.get(f"{self.GRAPH_PATH}/{self.NODE_NAME}.outputs:childFrames"),
            "translations": og.Controller.get(f"{self.GRAPH_PATH}/{self.NODE_NAME}.outputs:translations"),
            "orientations": og.Controller.get(f"{self.GRAPH_PATH}/{self.NODE_NAME}.outputs:orientations"),
        }

    async def _step(self, num_steps=1):
        for _ in range(num_steps):
            await omni.kit.app.get_app().next_update_async()

    async def test_single_xform_prim(self):
        """Single rigid prim at known translation; verify parent frame is 'world' and translation matches."""
        cube_path = "/World/Cube"
        await _add_rigid_prim(self._stage, cube_path, [2.0, 3.0, 4.0])
        await self._step(2)

        self._create_graph([cube_path])
        await self._step()

        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        self.assertGreater(len(out["childFrames"]), 0, "Expected at least one transform pair")
        # The parent frame should be 'world' (no parentPrim specified)
        self.assertEqual(out["parentFrames"][0], "world", "Parent frame should be 'world'")
        # Child frame name should match the prim name
        self.assertEqual(out["childFrames"][0], "Cube", "Child frame should be 'Cube'")
        # Translation should be close to the set position
        trans = out["translations"][0]
        self.assertAlmostEqual(trans[0], 2.0, delta=0.1, msg="Translation x")
        self.assertAlmostEqual(trans[1], 3.0, delta=0.1, msg="Translation y")
        self.assertAlmostEqual(trans[2], 4.0, delta=0.1, msg="Translation z")
        # Orientation should be near identity (x,y,z,w) = (0,0,0,1)
        ori = out["orientations"][0]
        self.assertAlmostEqual(ori[3], 1.0, delta=0.01, msg="Orientation w should be ~1")

        self._timeline.stop()

    async def test_relative_to_parent_prim(self):
        """Child prim at a known offset from parent; translation should be relative offset."""
        parent_path = "/World/Parent"
        child_path = "/World/Parent/Child"
        await _add_rigid_prim(self._stage, parent_path, [10.0, 0.0, 0.0])
        await _add_rigid_prim(self._stage, child_path, [15.0, 0.0, 0.0])
        await self._step(2)

        self._create_graph([child_path], parent_prim_path=parent_path)
        await self._step()

        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        self.assertGreater(len(out["childFrames"]), 0, "Expected at least one transform pair")
        trans = out["translations"][0]
        # Child is 5 units from parent along X
        self.assertAlmostEqual(trans[0], 5.0, delta=0.2, msg="Relative translation x should be ~5")
        self.assertAlmostEqual(trans[1], 0.0, delta=0.1, msg="Relative translation y should be ~0")
        self.assertAlmostEqual(trans[2], 0.0, delta=0.1, msg="Relative translation z should be ~0")

        self._timeline.stop()

    async def test_no_target_prims_logs_error(self):
        """With no targetPrims, compute should fail (no execOut)."""
        og.Controller.edit(
            {"graph_path": self.GRAPH_PATH, "evaluator_name": "execution"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    (self.NODE_NAME, self.NODE_TYPE),
                ],
                og.Controller.Keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", f"{self.NODE_NAME}.inputs:execIn"),
                ],
            },
        )
        await self._step()
        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        # Without target prims, outputs should be empty
        self.assertEqual(len(out["childFrames"]), 0, "childFrames should be empty with no target prims")

        self._timeline.stop()

    async def test_multiple_prims_produce_multiple_pairs(self):
        """Two separate rigid prims result in two output transform pairs."""
        paths = ["/World/PrimA", "/World/PrimB"]
        for i, p in enumerate(paths):
            await _add_rigid_prim(self._stage, p, [float(i), 0.0, 0.0])
        await self._step(2)

        self._create_graph(paths)
        await self._step()

        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        self.assertEqual(len(out["childFrames"]), 2, "Expected two transform pairs for two target prims")
        self.assertEqual(len(out["translations"]), 2, "Expected two translation entries")
        self.assertEqual(len(out["orientations"]), 2, "Expected two orientation entries")

        self._timeline.stop()

    async def test_outputs_are_consistent_lengths(self):
        """All four output arrays must have the same length."""
        cube_path = "/World/Cube"
        await _add_rigid_prim(self._stage, cube_path, [0.0, 0.0, 1.0])
        await self._step(2)

        self._create_graph([cube_path])
        await self._step()

        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        n = len(out["parentFrames"])
        self.assertEqual(len(out["childFrames"]), n, "childFrames length mismatch")
        self.assertEqual(len(out["translations"]), n, "translations length mismatch")
        self.assertEqual(len(out["orientations"]), n, "orientations length mismatch")
        self.assertGreater(n, 0, "Expected at least one output pair")

        self._timeline.stop()

    async def test_orientation_is_unit_quaternion(self):
        """Output quaternion (x,y,z,w) should be unit-length."""
        import math

        cube_path = "/World/Cube"
        # Apply a 45-degree rotation around Z (w, x, y, z)
        await _add_rigid_prim(
            self._stage,
            cube_path,
            [0.0, 0.0, 0.0],
            orientations=[[0.9238795, 0.0, 0.0, 0.3826834]],
        )
        await self._step(2)

        self._create_graph([cube_path])
        await self._step()

        self._timeline.play()
        await self._step(5)
        await og.Controller.evaluate(self.GRAPH_PATH)

        out = self._get_outputs()
        if len(out["orientations"]) > 0:
            ori = out["orientations"][0]  # (x, y, z, w)
            norm_sq = sum(float(v) * float(v) for v in ori)
            self.assertAlmostEqual(norm_sq, 1.0, delta=0.01, msg="Quaternion should be unit length")

        self._timeline.stop()
