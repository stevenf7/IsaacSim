# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Test importer utils functionality."""

import omni.kit.test
import omni.usd
from isaacsim.asset.importer.utils.impl import importer_utils
from isaacsim.asset.importer.utils.impl.physx_types import PhysxAttr, PhysxSchema
from pxr import Usd, UsdGeom, UsdPhysics


class TestImporterUtils(omni.kit.test.AsyncTestCase):
    """Test helpers in :mod:`isaacsim.asset.importer.utils.impl.importer_utils`."""

    async def setUp(self) -> None:
        """Prepare a new USD stage for each test."""
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def test_delete_scope_reparents_children(self) -> None:
        """Reparent scope children to the parent prim before deleting the scope."""
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage, "/World")
        UsdGeom.Scope.Define(stage, "/World/Scope")
        UsdGeom.Xform.Define(stage, "/World/Scope/Child")

        importer_utils.delete_scope(stage, "/World/Scope")

        self.assertFalse(stage.GetPrimAtPath("/World/Scope").IsValid())
        self.assertTrue(stage.GetPrimAtPath("/World/Child").IsValid())

    async def test_add_joint_schemas(self) -> None:
        """Apply joint-related schemas to prismatic and revolute joints."""
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage, "/World")
        revolute = UsdPhysics.RevoluteJoint.Define(stage, "/World/Revolute").GetPrim()
        prismatic = UsdPhysics.PrismaticJoint.Define(stage, "/World/Prismatic").GetPrim()

        importer_utils.add_joint_schemas(stage)

        self.assertTrue(revolute.HasAPI(PhysxSchema.JOINT_API))
        self.assertTrue(revolute.HasAPI(UsdPhysics.DriveAPI, "angular"))
        self.assertTrue(revolute.HasAPI(PhysxSchema.JOINT_STATE_API, "angular"))

        self.assertTrue(prismatic.HasAPI(PhysxSchema.JOINT_API))
        self.assertTrue(prismatic.HasAPI(UsdPhysics.DriveAPI, "linear"))
        self.assertTrue(prismatic.HasAPI(PhysxSchema.JOINT_STATE_API, "linear"))

    async def test_add_rigid_body_schemas(self) -> None:
        """Apply MassAPI to rigid bodies discovered via USDRT."""
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage, "/World")
        body_prim = stage.DefinePrim("/World/Body", "Xform")
        UsdPhysics.RigidBodyAPI.Apply(body_prim)
        importer_utils.add_rigid_body_schemas(stage)

        self.assertTrue(body_prim.HasAPI(UsdPhysics.RigidBodyAPI))
        self.assertTrue(body_prim.HasAPI(UsdPhysics.MassAPI))

    async def test_enable_self_collision_applies_articulation_api(self) -> None:
        """Enable self-collision on the default prim when missing roots.

        The PhysX-specific ``PhysxArticulationAPI`` is intentionally not
        authored here; the runtime consumes ``NewtonArticulationRootAPI``
        directly.
        """
        stage = Usd.Stage.CreateInMemory()
        default_prim = UsdGeom.Xform.Define(stage, "/World").GetPrim()
        stage.SetDefaultPrim(default_prim)

        updated = importer_utils.enable_self_collision(stage, enabled=True)

        self.assertEqual(updated, 1)
        self.assertTrue(default_prim.HasAPI("PhysicsArticulationRootAPI"))
        self.assertFalse(default_prim.HasAPI(PhysxSchema.ARTICULATION_API))
        self.assertTrue(default_prim.HasAPI("NewtonArticulationRootAPI"))

        newton_attr = default_prim.GetAttribute("newton:selfCollisionEnabled")
        self.assertTrue(newton_attr.IsValid())
        self.assertTrue(newton_attr.Get())
