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
"""Tests for Isaac robot schema helpers and utilities."""
import os
import tempfile
from unittest import mock

import omni.kit.app
import omni.kit.test
import omni.usd
import usd.schema.isaac as isaac_schema
from pxr import Gf, Sdf, UsdGeom, UsdPhysics
from usd.schema.isaac import robot_schema
from usd.schema.isaac.robot_schema import utils as robot_utils


class TestRobotSchemaUtils(omni.kit.test.AsyncTestCase):
    """Async tests for robot schema helper utilities."""

    async def setUp(self) -> None:
        """Set up a fresh USD stage for each test."""
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = omni.usd.get_context().get_stage()

    def _create_robot_with_joint(self) -> tuple[UsdGeom.Xform, UsdGeom.Xform, UsdPhysics.Joint]:
        robot_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot")
        UsdPhysics.RigidBodyAPI.Apply(robot_prim.GetPrim())
        UsdPhysics.ArticulationRootAPI.Apply(robot_prim.GetPrim())

        link_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot/Link1")
        UsdPhysics.RigidBodyAPI.Apply(link_prim.GetPrim())

        joint = UsdPhysics.Joint.Define(self._stage, "/World/Robot/joint1")
        joint.CreateBody0Rel().SetTargets([robot_prim.GetPrim().GetPath()])
        joint.CreateBody1Rel().SetTargets([link_prim.GetPrim().GetPath()])
        joint.CreateLocalPos0Attr().Set(Gf.Vec3f(1.0, 0.0, 0.0))
        joint.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        joint.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

        return robot_prim, link_prim, joint

    def _apply_limit(self, joint_prim, axis_token, low=-1.0, high=1.0) -> None:
        limit_api = UsdPhysics.LimitAPI.Apply(joint_prim, axis_token)
        limit_api.CreateLowAttr().Set(low)
        limit_api.CreateHighAttr().Set(high)

    async def test_apply_robot_api_populates_relationships(self) -> None:
        """Verify ApplyRobotAPI creates links and joints relationships."""
        robot_xform, link_xform, joint = self._create_robot_with_joint()
        robot_prim = robot_xform.GetPrim()
        link_prim = link_xform.GetPrim()
        joint_prim = joint.GetPrim()

        robot_schema.ApplyRobotAPI(robot_prim)

        self.assertTrue(robot_prim.HasAPI(robot_schema.Classes.ROBOT_API.value))
        self.assertTrue(robot_prim.GetAttribute(robot_schema.Attributes.DESCRIPTION.name))
        self.assertTrue(robot_prim.GetAttribute(robot_schema.Attributes.NAMESPACE.name))

        robot_links = robot_prim.GetRelationship(robot_schema.Relations.ROBOT_LINKS.name).GetTargets()
        robot_joints = robot_prim.GetRelationship(robot_schema.Relations.ROBOT_JOINTS.name).GetTargets()

        self.assertIn(robot_prim.GetPath(), robot_links)
        self.assertIn(link_prim.GetPath(), robot_links)
        self.assertIn(joint_prim.GetPath(), robot_joints)

        self.assertTrue(link_prim.HasAPI(robot_schema.Classes.LINK_API.value))
        self.assertTrue(joint_prim.HasAPI(robot_schema.Classes.JOINT_API.value))

    async def test_update_deprecated_joint_dof_order(self) -> None:
        """Verify deprecated DOF offset attributes are migrated."""
        _, _, joint = self._create_robot_with_joint()
        joint_prim = joint.GetPrim()

        self._apply_limit(joint_prim, UsdPhysics.Tokens.transX, low=-1.0, high=1.0)
        self._apply_limit(joint_prim, UsdPhysics.Tokens.rotX, low=-1.0, high=1.0)
        self._apply_limit(joint_prim, UsdPhysics.Tokens.transY, low=-1.0, high=1.0)
        self._apply_limit(joint_prim, UsdPhysics.Tokens.rotY, low=1.0, high=-1.0)

        joint_prim.CreateAttribute("isaac:physics:Tr_X:DoFOffset", Sdf.ValueTypeNames.Int).Set(0)
        joint_prim.CreateAttribute("isaac:physics:Rot_X:DoFOffset", Sdf.ValueTypeNames.Int).Set(0)
        joint_prim.CreateAttribute("isaac:physics:Tr_Y:DoFOffset", Sdf.ValueTypeNames.Int).Set(1)

        updated = robot_utils.UpdateDeprecatedJointDofOrder(joint_prim)
        self.assertTrue(updated)

        dof_attr = joint_prim.GetAttribute("isaac:physics:DofOffsetOpOrder")
        self.assertEqual(list(dof_attr.Get()), ["TransX", "RotX", "TransY"])

        self.assertFalse(robot_utils.UpdateDeprecatedJointDofOrder(joint_prim))

    async def test_get_all_robot_links_and_joints_warns_on_missing(self) -> None:
        """Warn when links or joints are missing from schema relationships."""
        robot_xform, link_xform, joint = self._create_robot_with_joint()
        robot_prim = robot_xform.GetPrim()

        robot_prim.AddAppliedSchema(robot_schema.Classes.ROBOT_API.value)

        with mock.patch("usd.schema.isaac.robot_schema.utils.carb.log_warn") as log_warn:
            links = robot_utils.GetAllRobotLinks(self._stage, robot_prim)
            joints = robot_utils.GetAllRobotJoints(self._stage, robot_prim)

            self.assertEqual({str(prim.GetPath()) for prim in links}, {"/World/Robot", "/World/Robot/Link1"})
            self.assertEqual({str(prim.GetPath()) for prim in joints}, {"/World/Robot/joint1"})

            warnings = [call.args[0] for call in log_warn.call_args_list]
            self.assertTrue(any("links missing from schema relationship" in msg for msg in warnings))
            self.assertTrue(any("joints missing from schema relationship" in msg for msg in warnings))

    async def test_generate_robot_link_tree_and_get_links_from_joint(self) -> None:
        """Verify link tree generation and joint link retrieval."""
        robot_xform, link_xform, joint = self._create_robot_with_joint()
        robot_prim = robot_xform.GetPrim()
        joint_prim = joint.GetPrim()

        robot_schema.ApplyRobotAPI(robot_prim)

        tree_root = robot_utils.GenerateRobotLinkTree(self._stage, robot_prim)
        self.assertIsNotNone(tree_root)

        before_links, after_links = robot_utils.GetLinksFromJoint(tree_root, joint_prim)
        before_paths = {str(prim.GetPath()) for prim in before_links}
        after_paths = {str(prim.GetPath()) for prim in after_links}

        self.assertIn("/World/Robot", before_paths)
        self.assertIn("/World/Robot/Link1", after_paths)

    async def test_get_joint_pose_and_body_relationship(self) -> None:
        """Verify joint pose extraction and body relationship lookup."""
        robot_xform, _, joint = self._create_robot_with_joint()
        robot_prim = robot_xform.GetPrim()
        joint_prim = joint.GetPrim()

        body_path = robot_utils.GetJointBodyRelationship(joint_prim, 0)
        self.assertEqual(body_path, robot_prim.GetPath())

        joint.GetExcludeFromArticulationAttr().Set(True)
        self.assertIsNone(robot_utils.GetJointBodyRelationship(joint_prim, 0))

        joint.GetExcludeFromArticulationAttr().Set(False)
        pose = robot_utils.GetJointPose(robot_prim, joint_prim)
        self.assertIsNotNone(pose)
        translation = pose.ExtractTranslation()
        self.assertAlmostEqual(translation[0], 1.0)
        self.assertAlmostEqual(translation[1], 0.0)
        self.assertAlmostEqual(translation[2], 0.0)

    async def test_update_deprecated_schemas(self) -> None:
        """Verify deprecated schema migration to current versions."""
        robot_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot").GetPrim()
        reference_prim = UsdGeom.Xform.Define(self._stage, "/World/Robot/Ref").GetPrim()
        reference_prim.AddAppliedSchema(robot_schema.Classes.REFERENCE_POINT_API.value)

        joint = UsdPhysics.Joint.Define(self._stage, "/World/Robot/joint1")
        joint_prim = joint.GetPrim()
        joint_prim.AddAppliedSchema(robot_schema.Classes.JOINT_API.value)

        self._apply_limit(joint_prim, UsdPhysics.Tokens.transX, low=-1.0, high=1.0)
        joint_prim.CreateAttribute("isaac:physics:Tr_X:DoFOffset", Sdf.ValueTypeNames.Int).Set(0)

        robot_utils.UpdateDeprecatedSchemas(robot_prim)

        self.assertFalse(reference_prim.HasAPI(robot_schema.Classes.REFERENCE_POINT_API.value))
        self.assertTrue(reference_prim.HasAPI(robot_schema.Classes.SITE_API.value))

        dof_attr = joint_prim.GetAttribute("isaac:physics:DofOffsetOpOrder")
        self.assertTrue(dof_attr and dof_attr.HasAuthoredValueOpinion())

    async def test_register_plugin_path_skips_already_registered(self) -> None:
        """Skip registration when plugins are already registered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plug_info = os.path.join(temp_dir, "plugInfo.json")
            with open(plug_info, "w") as handle:
                handle.write('# comment\n{"Plugins": [{"Name": "TestPlugin"}]}')

            with mock.patch.object(isaac_schema.Plug, "Registry") as registry_cls:
                registry = registry_cls.return_value
                plugin = mock.Mock()
                plugin.name = "TestPlugin"
                registry.GetAllPlugins.return_value = [plugin]

                isaac_schema._register_plugin_path(temp_dir)

                registry.RegisterPlugins.assert_not_called()

    async def test_register_plugin_path_registers_when_missing(self) -> None:
        """Register plugins when not yet present in the registry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plug_info = os.path.join(temp_dir, "plugInfo.json")
            with open(plug_info, "w") as handle:
                handle.write('# comment\n{"Plugins": [{"Name": "NewPlugin"}]}')

            with mock.patch.object(isaac_schema.Plug, "Registry") as registry_cls:
                registry = registry_cls.return_value
                registry.GetAllPlugins.return_value = []
                registry.RegisterPlugins.return_value = True

                isaac_schema._register_plugin_path(temp_dir)

                registry.RegisterPlugins.assert_called_once_with(temp_dir)
