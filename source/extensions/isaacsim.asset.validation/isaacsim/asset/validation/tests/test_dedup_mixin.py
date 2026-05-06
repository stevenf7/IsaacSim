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

"""Standalone unit tests for DedupMixin and _resolve_at in util.py.

No USD/Kit dependencies — all USD objects are replaced by duck-typed stubs.
"""

import unittest

from isaacsim.asset.validation.util import DedupMixin, _resolve_at

# ---------------------------------------------------------------------------
# Stubs — no pxr required
# ---------------------------------------------------------------------------


class _StubBase:
    """Minimal stand-in for BaseRuleChecker that records forwarded calls."""

    def __init__(self):
        self.calls = []

    def _AddError(self, message, **kwargs):
        self.calls.append(("error", message, kwargs.get("at")))

    def _AddWarning(self, message, **kwargs):
        self.calls.append(("warning", message, kwargs.get("at")))

    def _AddInfo(self, message, **kwargs):
        self.calls.append(("info", message, kwargs.get("at")))


class _TestRule(DedupMixin, _StubBase):
    """Concrete rule that inherits dedup via MRO: DedupMixin → _StubBase."""

    pass


class _StubStage:
    """Duck-type stub for Usd.Stage (has GetRootLayer)."""

    def __init__(self, identifier):
        self._identifier = identifier

    def GetRootLayer(self):
        class _Layer:
            def __init__(self, ident):
                self.identifier = ident

        return _Layer(self._identifier)


class _StubPrim:
    """Duck-type stub for Usd.Prim (has GetPath but not GetRootLayer)."""

    def __init__(self, path):
        self._path = path

    def GetPath(self):
        return self._path  # str is fine; _resolve_at calls str() on it


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestResolveAt(unittest.TestCase):
    """Unit tests for the _resolve_at helper."""

    def test_none_returns_empty_string(self):
        self.assertEqual(_resolve_at(None), "")

    def test_stage_uses_root_layer_identifier(self):
        stage = _StubStage("/tmp/asset.usd")
        self.assertEqual(_resolve_at(stage), "/tmp/asset.usd")

    def test_prim_uses_get_path(self):
        prim = _StubPrim("/World/Cube")
        self.assertEqual(_resolve_at(prim), "/World/Cube")

    def test_unknown_type_falls_back_to_str(self):
        self.assertEqual(_resolve_at(42), "42")
        self.assertEqual(_resolve_at("some/path"), "some/path")


class TestDedupMixinError(unittest.TestCase):
    """_AddError deduplication."""

    def test_duplicate_error_emits_once(self):
        """Identical _AddError calls on the same key → forwarded once."""
        rule = _TestRule()
        prim = _StubPrim("/World/Cube")
        rule._AddError("mesh missing", at=prim)
        rule._AddError("mesh missing", at=prim)
        rule._AddError("mesh missing", at=prim)
        self.assertEqual(len(rule.calls), 1)
        self.assertEqual(rule.calls[0], ("error", "mesh missing", prim))

    def test_different_messages_both_emitted(self):
        """Same prim, different messages → both forwarded."""
        rule = _TestRule()
        prim = _StubPrim("/World/Cube")
        rule._AddError("mesh missing", at=prim)
        rule._AddError("normals bad", at=prim)
        self.assertEqual(len(rule.calls), 2)


class TestDedupMixinWarning(unittest.TestCase):
    """_AddWarning deduplication."""

    def test_duplicate_warning_emits_once(self):
        """Identical _AddWarning calls → forwarded once."""
        rule = _TestRule()
        rule._AddWarning("soft warning", at=None)
        rule._AddWarning("soft warning", at=None)
        self.assertEqual(len(rule.calls), 1)
        self.assertEqual(rule.calls[0][0], "warning")


class TestDedupMixinInfo(unittest.TestCase):
    """_AddInfo deduplication."""

    def test_duplicate_info_emits_once(self):
        """Identical _AddInfo calls → forwarded once."""
        rule = _TestRule()
        rule._AddInfo("fyi note", at=None)
        rule._AddInfo("fyi note", at=None)
        self.assertEqual(len(rule.calls), 1)
        self.assertEqual(rule.calls[0][0], "info")


class TestDedupMixinInstanceIsolation(unittest.TestCase):
    """Per-instance _seen sets."""

    def test_two_instances_have_independent_seen_sets(self):
        """Each rule instance tracks its own _seen; a call on rule_b doesn't
        suppress the same call on rule_a and vice-versa."""
        rule_a = _TestRule()
        rule_b = _TestRule()
        prim = _StubPrim("/World/Mesh")

        rule_a._AddError("duplicate issue", at=prim)
        rule_a._AddError("duplicate issue", at=prim)  # suppressed in a

        rule_b._AddError("duplicate issue", at=prim)
        rule_b._AddError("duplicate issue", at=prim)  # suppressed in b

        self.assertEqual(len(rule_a.calls), 1, "rule_a should have 1 forwarded call")
        self.assertEqual(len(rule_b.calls), 1, "rule_b should have 1 forwarded call")


class TestResolveAtInKey(unittest.TestCase):
    """`at=` variants produce the correct key component."""

    def test_at_none_key_component_is_empty_string(self):
        """at=None → key built with "" → subsequent call suppressed."""
        rule = _TestRule()
        rule._AddError("msg", at=None)
        rule._AddError("msg", at=None)
        self.assertEqual(len(rule.calls), 1)

    def test_at_stage_mock_uses_root_layer_identifier(self):
        """at= with GetRootLayer → identifier used in key."""
        stage_a = _StubStage("/a.usd")
        stage_b = _StubStage("/b.usd")
        rule = _TestRule()
        rule._AddError("msg", at=stage_a)
        rule._AddError("msg", at=stage_a)  # duplicate → suppressed
        rule._AddError("msg", at=stage_b)  # different identifier → forwarded
        self.assertEqual(len(rule.calls), 2)

    def test_at_prim_mock_uses_get_path(self):
        """at= with GetPath → str(path) used in key."""
        prim_a = _StubPrim("/World/A")
        prim_b = _StubPrim("/World/B")
        rule = _TestRule()
        rule._AddError("msg", at=prim_a)
        rule._AddError("msg", at=prim_a)  # duplicate → suppressed
        rule._AddError("msg", at=prim_b)  # different path → forwarded
        self.assertEqual(len(rule.calls), 2)

    def test_at_unknown_type_falls_back_to_str(self):
        """at= unknown type → str(at) used in key."""
        rule = _TestRule()
        rule._AddError("msg", at=99)
        rule._AddError("msg", at=99)  # same str → suppressed
        rule._AddError("msg", at=100)  # different str → forwarded
        self.assertEqual(len(rule.calls), 2)


class TestSeverityDoesNotCrossContaminate(unittest.TestCase):
    """Severity string is part of the key, so error/warning/info are distinct."""

    def test_same_message_different_severity_all_forwarded(self):
        rule = _TestRule()
        rule._AddError("shared msg", at=None)
        rule._AddWarning("shared msg", at=None)
        rule._AddInfo("shared msg", at=None)
        self.assertEqual(len(rule.calls), 3)


if __name__ == "__main__":
    unittest.main()
