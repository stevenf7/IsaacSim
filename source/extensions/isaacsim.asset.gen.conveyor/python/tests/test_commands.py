# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for the deprecated CreateConveyorBelt command."""

import omni.kit.commands
import omni.kit.test
from pxr import Gf, UsdGeom, UsdPhysics


class TestCreateConveyorBeltCommand(omni.kit.test.AsyncTestCase):
    """Test the deprecated CreateConveyorBelt omni.kit.commands command."""

    async def setUp(self) -> None:
        """Set up the test environment."""
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        scene = UsdPhysics.Scene.Define(self._stage, "/physics")
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(9.81)
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self) -> None:
        """Clean up after each test."""
        await omni.kit.app.get_app().next_update_async()

    async def test_create_conveyor_belt_command(self) -> None:
        """Test creating a conveyor belt via the deprecated command."""
        cubeGeom = UsdGeom.Cube.Define(self._stage, "/cube")
        cube_prim = self._stage.GetPrimAtPath("/cube")
        cubeGeom.CreateSizeAttr(1.0)
        cubeGeom.AddTranslateOp().Set((0, 0, 0))
        UsdPhysics.RigidBodyAPI.Apply(cube_prim)
        UsdPhysics.CollisionAPI.Apply(cube_prim)

        success, og_prim = omni.kit.commands.execute("CreateConveyorBelt", conveyor_prim=cube_prim)
        self.assertTrue(success)
        self.assertIsNotNone(og_prim)
        self.assertTrue(og_prim.IsValid())

    async def test_create_conveyor_belt_command_without_physics(self) -> None:
        """Test creating a conveyor belt via the deprecated command on a prim without RigidBodyAPI."""
        cubeGeom = UsdGeom.Cube.Define(self._stage, "/cube_no_physics")
        cube_prim = self._stage.GetPrimAtPath("/cube_no_physics")
        cubeGeom.CreateSizeAttr(1.0)
        cubeGeom.AddTranslateOp().Set((0, 0, 0))
        UsdPhysics.CollisionAPI.Apply(cube_prim)

        success, og_prim = omni.kit.commands.execute("CreateConveyorBelt", conveyor_prim=cube_prim)
        self.assertTrue(success)
        self.assertIsNotNone(og_prim)
        self.assertTrue(og_prim.IsValid())
