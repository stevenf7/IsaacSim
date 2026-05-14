# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Standalone smoke tests for isaacsim-asset-transformer-rules."""

from __future__ import annotations

import os
import sys
import unittest


class TestSmoke(unittest.TestCase):
    """Import and namespace validation."""

    def test_import_public_api(self) -> None:
        """Verify core public API is importable."""
        from isaacsim.asset.transformer.rules import DEFAULT_PROFILE_PATH, register_all_rules

        self.assertTrue(callable(register_all_rules))
        self.assertIsInstance(DEFAULT_PROFILE_PATH, str)

    def test_default_profile_exists(self) -> None:
        """Verify the shipped profile JSON exists on disk."""
        from isaacsim.asset.transformer.rules import DEFAULT_PROFILE_PATH

        self.assertTrue(os.path.isfile(DEFAULT_PROFILE_PATH), f"Missing: {DEFAULT_PROFILE_PATH}")

    def test_no_omni_modules(self) -> None:
        """No omni.* modules should be loaded after import."""
        from isaacsim.asset.transformer.rules import register_all_rules  # noqa: F401

        omni_mods = [m for m in sys.modules if m.startswith("omni.")]
        self.assertEqual(omni_mods, [], f"Unexpected omni modules: {omni_mods}")


class TestFunctional(unittest.TestCase):
    """Rule registration and profile loading tests."""

    def test_register_all_rules(self) -> None:
        """Verify register_all_rules populates the registry."""
        from isaacsim.asset.transformer import RuleRegistry
        from isaacsim.asset.transformer.rules import register_all_rules

        register_all_rules()
        registry = RuleRegistry()
        rules = registry.list_rules()
        self.assertGreaterEqual(len(rules), 12, f"Expected >= 12 rules, got {len(rules)}")

    def test_profile_json_parses(self) -> None:
        """Verify the shipped profile JSON is valid and loadable."""
        import json

        from isaacsim.asset.transformer.models import RuleProfile
        from isaacsim.asset.transformer.rules import DEFAULT_PROFILE_PATH

        with open(DEFAULT_PROFILE_PATH) as f:
            data = json.load(f)
        profile = RuleProfile.from_dict(data)
        self.assertGreater(len(profile.rules), 0)
        self.assertIsNotNone(profile.profile_name)


if __name__ == "__main__":
    unittest.main()
