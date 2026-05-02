# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Standalone smoke tests for isaacsim-asset-importer-utils."""

from __future__ import annotations

import sys
import unittest


class TestSmoke(unittest.TestCase):
    """Import and namespace validation."""

    def test_import_physx_types(self) -> None:
        """Verify physx_types enums are importable."""
        from isaacsim.asset.importer.utils.impl.physx_types import (
            PhysxAttr,
            PhysxMimicAttr,
            PhysxMimicRel,
            PhysxSchema,
        )

        self.assertTrue(len(PhysxAttr) > 0)
        self.assertTrue(len(PhysxSchema) > 0)
        self.assertTrue(len(PhysxMimicAttr) > 0)
        self.assertTrue(len(PhysxMimicRel) > 0)

    def test_no_omni_modules(self) -> None:
        """No omni.* modules should be loaded after import."""
        from isaacsim.asset.importer.utils.impl.physx_types import PhysxAttr  # noqa: F401

        omni_mods = [m for m in sys.modules if m.startswith("omni.")]
        self.assertEqual(omni_mods, [], f"Unexpected omni modules: {omni_mods}")


class TestFunctional(unittest.TestCase):
    """PhysX type enum correctness tests."""

    def test_physx_attr_names(self) -> None:
        """Verify PhysxAttr enum values have correct attribute name format."""
        from isaacsim.asset.importer.utils.impl.physx_types import PhysxAttr

        for attr in PhysxAttr:
            self.assertIn(":", attr.name, f"{attr} missing colon in name")
            self.assertIsNotNone(attr.type, f"{attr} has None type")

    def test_physx_schema_values(self) -> None:
        """Verify PhysxSchema enum values are correct API names."""
        from isaacsim.asset.importer.utils.impl.physx_types import PhysxSchema

        self.assertEqual(PhysxSchema.JOINT_API.value, "PhysxJointAPI")
        self.assertEqual(PhysxSchema.ARTICULATION_API.value, "PhysxArticulationAPI")
        self.assertEqual(PhysxSchema.MIMIC_JOINT_API.value, "PhysxMimicJointAPI")

    def test_physx_mimic_format(self) -> None:
        """Verify mimic attr/rel format methods produce correct strings."""
        from isaacsim.asset.importer.utils.impl.physx_types import PhysxMimicAttr, PhysxMimicRel

        self.assertEqual(PhysxMimicAttr.GEARING.format("rotZ"), "physxMimicJoint:rotZ:gearing")
        self.assertEqual(PhysxMimicAttr.OFFSET.format("rotX"), "physxMimicJoint:rotX:offset")
        self.assertEqual(PhysxMimicRel.REFERENCE_JOINT.format("rotZ"), "physxMimicJoint:rotZ:referenceJoint")

    def test_create_physx_attrs_on_stage(self) -> None:
        """Verify PhysxAttr enums can create real USD attributes."""
        from isaacsim.asset.importer.utils.impl.physx_types import PhysxAttr
        from pxr import Sdf, Usd, UsdGeom, UsdPhysics

        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage, "/World")
        joint = UsdPhysics.RevoluteJoint.Define(stage, "/World/joint")
        prim = joint.GetPrim()

        prim.CreateAttribute(PhysxAttr.JOINT_ARMATURE.name, PhysxAttr.JOINT_ARMATURE.type).Set(0.1)
        prim.CreateAttribute(PhysxAttr.JOINT_FRICTION.name, PhysxAttr.JOINT_FRICTION.type).Set(0.5)
        prim.CreateAttribute(PhysxAttr.JOINT_MAX_VELOCITY.name, PhysxAttr.JOINT_MAX_VELOCITY.type).Set(180.0)

        self.assertAlmostEqual(prim.GetAttribute(PhysxAttr.JOINT_ARMATURE.name).Get(), 0.1)
        self.assertAlmostEqual(prim.GetAttribute(PhysxAttr.JOINT_FRICTION.name).Get(), 0.5)
        self.assertAlmostEqual(prim.GetAttribute(PhysxAttr.JOINT_MAX_VELOCITY.name).Get(), 180.0)


if __name__ == "__main__":
    unittest.main()
