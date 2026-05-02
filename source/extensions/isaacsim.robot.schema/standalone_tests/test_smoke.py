# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Standalone smoke tests for isaacsim-robot-schema."""

from __future__ import annotations

import sys
import unittest


class TestSmoke(unittest.TestCase):
    """Import and namespace validation."""

    def test_import_robot_schema(self) -> None:
        """Verify robot_schema is importable under usd.schema.isaac namespace."""
        import usd.schema.isaac.robot_schema as rs

        self.assertTrue(hasattr(rs, "__file__"))

    def test_no_omni_modules(self) -> None:
        """No omni.* modules should be loaded after import."""
        import usd.schema.isaac.robot_schema  # noqa: F401

        omni_mods = [m for m in sys.modules if m.startswith("omni.")]
        self.assertEqual(omni_mods, [], f"Unexpected omni modules: {omni_mods}")


class TestFunctional(unittest.TestCase):
    """Schema utility tests."""

    def test_utils_importable(self) -> None:
        """Verify utils module is importable and has UsdPhysics available."""
        from usd.schema.isaac.robot_schema import utils

        self.assertTrue(hasattr(utils, "UsdPhysics"))


if __name__ == "__main__":
    unittest.main()
