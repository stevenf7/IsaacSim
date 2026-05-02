# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Standalone smoke tests for isaacsim-asset-exporter-urdf."""

from __future__ import annotations

import sys
import unittest


class TestSmoke(unittest.TestCase):
    """Import and namespace validation."""

    def test_import_public_api(self) -> None:
        """Verify URDF exporter class is importable."""
        from isaacsim.asset.exporter.urdf import UsdToUrdfConverter

        self.assertTrue(callable(UsdToUrdfConverter))

    def test_import_joint_reader(self) -> None:
        """Verify joint_reader functions are importable."""
        from isaacsim.asset.exporter.urdf.converter.joint_reader import (
            _read_armature,
            _read_physx_friction,
            _read_physx_max_velocity,
        )

        self.assertTrue(callable(_read_armature))
        self.assertTrue(callable(_read_physx_friction))
        self.assertTrue(callable(_read_physx_max_velocity))

    def test_no_omni_modules(self) -> None:
        """No omni.* modules should be loaded after import."""
        from isaacsim.asset.exporter.urdf import UsdToUrdfConverter  # noqa: F401

        omni_mods = [m for m in sys.modules if m.startswith("omni.")]
        self.assertEqual(omni_mods, [], f"Unexpected omni modules: {omni_mods}")


if __name__ == "__main__":
    unittest.main()
