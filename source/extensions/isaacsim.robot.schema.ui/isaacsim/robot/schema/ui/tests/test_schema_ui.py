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
"""Tests for the robot schema UI extension."""
import asyncio
from unittest import mock

import omni.kit.test
import omni.usd
from isaacsim.robot.schema.ui import utils as ui_utils
from omni.ui.tests.test_base import OmniUiTest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
from usd.schema.isaac import robot_schema

"""Tests for the robot schema UI extension."""

import omni.kit.test
import omni.usd
from isaacsim.storage.native import get_assets_root_path_async
from omni.ui.tests.test_base import OmniUiTest


class TestSchemaUI(OmniUiTest):
    """UI tests covering robot hierarchy visualization."""

    async def setUp(self) -> None:
        """Set up a fresh USD stage for each test."""
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = omni.usd.get_context().get_stage()

    async def tearDown(self) -> None:
        """Wait for stage loads to finish and clean up."""
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

    def _build_simple_robot(self) -> tuple[Usd.Prim, Usd.Prim, Usd.Prim]:
        """Build a minimal articulated robot for hierarchy tests.

        Returns:
            Tuple of (robot_prim, link_prim, joint_prim).
        """
        robot_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot").GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(robot_prim)
        UsdPhysics.ArticulationRootAPI.Apply(robot_prim)

        link_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot/Link1").GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(link_prim)

        joint = UsdPhysics.D6Joint.Define(self._stage, "/World/Robot/joint1")
        joint.CreateBody0Rel().SetTargets([robot_prim.GetPath()])
        joint.CreateBody1Rel().SetTargets([link_prim.GetPath()])
        joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0.1, 0.0, 0.0))
        joint.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        joint.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

        robot_schema.ApplyRobotAPI(robot_prim)
        return robot_prim, link_prim, joint.GetPrim()

    async def test_robot_hierarchy_creation(self) -> None:
        """Generate hierarchy stage and verify mappings."""
        robot_prim, link_prim, joint_prim = self._build_simple_robot()
        await omni.kit.app.get_app().next_update_async()

        hierarchy_stage, path_map, joint_connections = ui_utils.generate_robot_hierarchy_stage()

        self.assertIsNotNone(hierarchy_stage)
        self.assertIsNotNone(path_map.get_hierarchy_path(robot_prim.GetPath()))
        self.assertIsNotNone(path_map.get_hierarchy_path(link_prim.GetPath()))
        self.assertEqual(len(joint_connections), 1)
        self.assertEqual(joint_connections[0].joint_prim_path, joint_prim.GetPath())


class TestSchemaUiUtils(omni.kit.test.AsyncTestCase):
    """Unit tests for robot schema UI utilities."""

    async def test_path_map_round_trip(self) -> None:
        """Verify PathMap insert, lookup, and clear round-trip."""
        path_map = ui_utils.PathMap()
        original = Sdf.Path("/World/Robot")
        hierarchy = Sdf.Path("/Hierarchy/Robot")
        path_map.insert(original, hierarchy)

        self.assertEqual(path_map.get_hierarchy_path(original), hierarchy)
        self.assertEqual(path_map.get_original_path(hierarchy), original)

        path_map.clear()
        self.assertIsNone(path_map.get_hierarchy_path(original))

    async def test_vector_helpers(self) -> None:
        """Test to_vec3d and to_float_list conversion helpers."""
        self.assertIsNone(ui_utils.to_vec3d(None))
        self.assertEqual(ui_utils.to_vec3d((1, 2, 3)), Gf.Vec3d(1, 2, 3))
        self.assertEqual(ui_utils.to_float_list(Gf.Vec3d(1, 2, 3)), [1.0, 2.0, 3.0])

    async def test_world_to_screen_position_fallback(self) -> None:
        """Fall back to identity when no active viewport is available."""
        with mock.patch("isaacsim.robot.schema.ui.utils.get_active_viewport", return_value=None):
            self.assertEqual(ui_utils.world_to_screen_position((1, 2, 3)), (1.0, 2.0, 3.0))

    async def test_joint_has_both_bodies(self) -> None:
        """Verify joint body detection with zero and two targets."""
        stage = Usd.Stage.CreateInMemory()
        joint = UsdPhysics.RevoluteJoint.Define(stage, "/Joint")
        joint_prim = joint.GetPrim()
        self.assertFalse(ui_utils.joint_has_both_bodies(joint_prim))

        joint.CreateBody0Rel().SetTargets(["/Body0"])
        joint.CreateBody1Rel().SetTargets(["/Body1"])
        self.assertTrue(ui_utils.joint_has_both_bodies(joint_prim))

    async def test_is_in_front_of_camera(self) -> None:
        """Test front-of-camera check with forward and backward points."""
        camera_position = Gf.Vec3d(0.0, 0.0, 0.0)
        camera_forward = Gf.Vec3d(0.0, 0.0, 1.0)
        self.assertTrue(ui_utils.is_in_front_of_camera((0.0, 0.0, 1.0), camera_position, camera_forward))
        self.assertFalse(ui_utils.is_in_front_of_camera((0.0, 0.0, -1.0), camera_position, camera_forward))


class TestSchemaUI(OmniUiTest):
    """UI tests covering robot hierarchy visualization."""

    async def setUp(self) -> None:
        """Set up a fresh USD stage for each test."""
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = omni.usd.get_context().get_stage()

    async def tearDown(self) -> None:
        """Wait for stage loads to finish and clean up."""
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

    async def test_robot_hierarchy_creation(self) -> None:
        """Test creation of robot hierarchy."""
        # Add robot to stage (Franka)
        robot_path = "/World/test_robot"
        robot_prim = self._stage.DefinePrim(robot_path, "Xform")
        assets_root_path = await get_assets_root_path_async()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        robot_prim.GetReferences().AddReference(
            assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
        )
        await omni.kit.app.get_app().next_update_async()
