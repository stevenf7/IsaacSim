# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Tests for pure-logic functions in isaac_lab_dashboard.py and test_isaac_lab.py."""
from __future__ import annotations

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest

# Add tools/ci to path so we can import the dashboards package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dashboards.parsing import (
    get_testcase_status,
    merge_summaries,
    parse_junit_xml,
    parse_test_report_api,
    worst_status,
)


# ── get_testcase_status ───────────────────────────────────────────────────────

class TestGetTestcaseStatus:
    def _tc(self, *child_tags, message=""):
        tc = ET.Element("testcase")
        for tag in child_tags:
            child = ET.SubElement(tc, tag)
            if message:
                child.set("message", message)
        return tc

    def test_no_children_is_pass(self):
        assert get_testcase_status(self._tc()) == "pass"

    def test_failure_child_is_fail(self):
        assert get_testcase_status(self._tc("failure")) == "fail"

    def test_error_child_is_error(self):
        assert get_testcase_status(self._tc("error")) == "error"

    def test_error_with_timed_out_message_is_timeout(self):
        assert get_testcase_status(self._tc("error", message="timed out after 120s")) == "timeout"

    def test_error_with_timeout_message_is_timeout(self):
        assert get_testcase_status(self._tc("error", message="timeout exceeded")) == "timeout"

    def test_skipped_child_is_skip(self):
        assert get_testcase_status(self._tc("skipped")) == "skip"

    def test_unknown_child_tag_is_pass(self):
        tc = ET.Element("testcase")
        ET.SubElement(tc, "system-out")
        assert get_testcase_status(tc) == "pass"


# ── worst_status ─────────────────────────────────────────────────────────────

class TestWorstStatus:
    def test_fail_beats_pass(self):
        assert worst_status("pass", "fail") == "fail"

    def test_timeout_beats_error(self):
        assert worst_status("error", "timeout") == "timeout"

    def test_error_beats_fail(self):
        assert worst_status("fail", "error") == "error"

    def test_single_value(self):
        assert worst_status("pass") == "pass"

    def test_unknown_status_loses(self):
        assert worst_status("pass", "unknown_status") == "pass"

    def test_all_statuses_ordered(self):
        assert worst_status("pass", "skip", "fail", "error", "timeout") == "timeout"


# ── parse_junit_xml ───────────────────────────────────────────────────────────

def _build_xml(suites):
    """Helper: build JUnit XML bytes from a list of (suite_name, cases) tuples.

    Each case is a tuple of ``(name, tag, message)`` or
    ``(name, tag, message, classname)``.  ``tag`` is ``None`` for a pass.
    """
    root = ET.Element("testsuites")
    for suite_name, cases in suites:
        suite = ET.SubElement(root, "testsuite", name=suite_name)
        for case in cases:
            case_name, tag, message = case[:3]
            classname = case[3] if len(case) > 3 else ""
            attrs = {"name": case_name}
            if classname:
                attrs["classname"] = classname
            tc = ET.SubElement(suite, "testcase", **attrs)
            if tag:
                child = ET.SubElement(tc, tag)
                if message:
                    child.set("message", message)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


class TestParseJunitXml:
    def test_empty_testsuites(self):
        xml = b'<?xml version="1.0"?><testsuites></testsuites>'
        summary, sections = parse_junit_xml(xml)
        assert summary["total"] == 0
        assert summary["pass_rate"] == 0.0
        assert sections == {}

    def test_single_pass(self):
        xml = _build_xml([("suite1", [("test_foo", None, "")])])
        summary, sections = parse_junit_xml(xml)
        assert summary["total"] == 1
        assert summary["passed"] == 1
        assert summary["failed"] == 0
        assert summary["pass_rate"] == 1.0
        assert list(sections.keys()) == ["suite1"]
        assert list(sections["suite1"]["suites"].keys()) == ["test_foo"]

    def test_fail(self):
        xml = _build_xml([("suite1", [("test_foo", "failure", "")])])
        summary, _ = parse_junit_xml(xml)
        assert summary["failed"] == 1
        assert summary["passed"] == 0

    def test_error(self):
        xml = _build_xml([("suite1", [("test_foo", "error", "some error")])])
        summary, _ = parse_junit_xml(xml)
        assert summary["errored"] == 1

    def test_timeout_via_message(self):
        xml = _build_xml([("suite1", [("test_foo", "error", "timed out after 60s")])])
        summary, _ = parse_junit_xml(xml)
        assert summary["timed_out"] == 1
        assert summary["errored"] == 0

    def test_skip(self):
        xml = _build_xml([("suite1", [("test_foo", "skipped", "")])])
        summary, _ = parse_junit_xml(xml)
        assert summary["skipped"] == 1

    def test_timeout_suite_promotes_errors(self):
        """Suite named timeout_* should promote 'error' status to 'timeout'."""
        xml = _build_xml([("timeout_tests", [("test_foo", "error", "generic error")])])
        summary, sections = parse_junit_xml(xml)
        assert summary["timed_out"] == 1
        assert summary["errored"] == 0
        assert sections["timeout_tests"]["summary"]["worst_status"] == "timeout"
        assert sections["timeout_tests"]["suites"]["test_foo"]["worst_status"] == "timeout"

    def test_multiple_testsuites_become_sections(self):
        xml = _build_xml([
            ("suite_a", [("pass1", None, ""), ("fail1", "failure", "")]),
            ("suite_b", [("pass2", None, "")]),
        ])
        summary, sections = parse_junit_xml(xml)
        assert summary["total"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        # One section per <testsuite>
        assert set(sections.keys()) == {"suite_a", "suite_b"}
        # One suite row per <testcase> inside a section
        assert set(sections["suite_a"]["suites"].keys()) == {"pass1", "fail1"}
        assert set(sections["suite_b"]["suites"].keys()) == {"pass2"}

    def test_pass_rate_with_mixed_results(self):
        xml = _build_xml([("s", [
            ("p1", None, ""), ("p2", None, ""), ("p3", None, ""),
            ("f1", "failure", ""),
        ])])
        summary, _ = parse_junit_xml(xml)
        assert summary["total"] == 4
        assert round(summary["pass_rate"], 4) == 0.75

    def test_section_summary_worst_status(self):
        xml = _build_xml([("s", [
            ("p1", None, ""),
            ("f1", "failure", ""),
            ("e1", "error", "msg"),
        ])])
        _, sections = parse_junit_xml(xml)
        assert sections["s"]["summary"]["worst_status"] == "error"

    def test_malformed_xml_raises(self):
        with pytest.raises(ET.ParseError):
            parse_junit_xml(b"<not valid xml")

    def test_root_testsuite_not_testsuites(self):
        """A bare <testsuite> root (not wrapped in <testsuites>) should be handled."""
        xml = b'<?xml version="1.0"?><testsuite name="s"><testcase name="t"/></testsuite>'
        summary, sections = parse_junit_xml(xml)
        assert summary["total"] == 1
        assert "s" in sections
        assert "t" in sections["s"]["suites"]

    def test_per_case_rows_preserve_every_case(self):
        """Every <testcase> becomes its own heatmap row within the section."""
        xml = _build_xml([("pytest", [
            ("test_a1", None, "", "tests.foo.TestA"),
            ("test_a2", "failure", "", "tests.foo.TestA"),
            ("test_a3", None, "", "tests.foo.TestA"),
            ("test_b1", None, "", "tests.foo.TestB"),
            ("test_b2", "skipped", "", "tests.foo.TestB"),
        ])])
        summary, sections = parse_junit_xml(xml)
        assert list(sections.keys()) == ["pytest"]
        assert set(sections["pytest"]["suites"].keys()) == {
            "test_a1", "test_a2", "test_a3", "test_b1", "test_b2",
        }
        assert sections["pytest"]["suites"]["test_a2"]["worst_status"] == "fail"
        assert sections["pytest"]["suites"]["test_b2"]["worst_status"] == "skip"
        assert summary["total"] == 5
        assert summary["passed"] == 3
        assert summary["failed"] == 1
        assert summary["skipped"] == 1

    def test_duplicate_case_names_in_section(self):
        """Parametrized tests can repeat case names; every row must still be unique."""
        xml = _build_xml([("pytest", [
            ("test_param", None, "", "tests.foo.TestA"),
            ("test_param", "failure", "", "tests.foo.TestA"),
        ])])
        _, sections = parse_junit_xml(xml)
        rows = sections["pytest"]["suites"]
        assert len(rows) == 2

    def test_duplicate_testsuite_names(self):
        """Sections with the same name are disambiguated with a numeric suffix."""
        xml = _build_xml([
            ("pytest", [("t1", None, "")]),
            ("pytest", [("t2", None, "")]),
        ])
        _, sections = parse_junit_xml(xml)
        assert set(sections.keys()) == {"pytest", "pytest#1"}

    def test_missing_classname_still_uses_case_name_as_key(self):
        """Row keys are driven by case name, so missing classname is fine."""
        xml = _build_xml([("my_suite", [("t", None, "")])])
        _, sections = parse_junit_xml(xml)
        assert "my_suite" in sections
        assert "t" in sections["my_suite"]["suites"]


# ── parse_test_report_api ─────────────────────────────────────────────────────

class TestParseTestReportApi:
    def _report(self, suites):
        """Build a GitLab test-report API response dict."""
        return {
            "test_suites": [
                {
                    "name": name,
                    "test_cases": [
                        {"name": n, "status": s, "execution_time": t}
                        for n, s, t in cases
                    ],
                }
                for name, cases in suites
            ]
        }

    def test_empty_report(self):
        summary, suites = parse_test_report_api({"test_suites": []})
        assert summary["total"] == 0
        assert summary["pass_rate"] == 0.0

    def test_success_maps_to_pass(self):
        report = self._report([("s", [("t", "success", 1.0)])])
        summary, _ = parse_test_report_api(report)
        assert summary["passed"] == 1

    def test_failed_maps_to_fail(self):
        report = self._report([("s", [("t", "failed", 0.5)])])
        summary, _ = parse_test_report_api(report)
        assert summary["failed"] == 1

    def test_skipped_maps_to_skip(self):
        report = self._report([("s", [("t", "skipped", 0.0)])])
        summary, _ = parse_test_report_api(report)
        assert summary["skipped"] == 1

    def test_error_maps_to_error(self):
        report = self._report([("s", [("t", "error", 0.0)])])
        summary, _ = parse_test_report_api(report)
        assert summary["errored"] == 1

    def test_timed_out_is_always_zero(self):
        """parse_test_report_api has no timeout detection; timed_out must be 0."""
        report = self._report([("s", [("t", "failed", 0.0)])])
        summary, _ = parse_test_report_api(report)
        assert summary["timed_out"] == 0

    def test_unknown_status_treated_as_pass(self, capsys):
        report = self._report([("s", [("t", "blocked", 0.0)])])
        summary, _ = parse_test_report_api(report)
        assert summary["passed"] == 1
        captured = capsys.readouterr()
        assert "unknown test case status" in captured.err

    def test_pass_rate_computed_from_totals(self):
        report = self._report([("s", [
            ("t1", "success", 0.0), ("t2", "success", 0.0), ("t3", "failed", 0.0),
        ])])
        summary, _ = parse_test_report_api(report)
        assert summary["total"] == 3
        assert round(summary["pass_rate"], 4) == round(2 / 3, 4)


# ── merge_summaries ───────────────────────────────────────────────────────────

class TestMergeSummaries:
    def _s(self, total, passed, failed=0, errored=0, skipped=0, timed_out=0, duration=0.0):
        pass_rate = passed / total if total > 0 else 0.0
        return {
            "total": total, "passed": passed, "failed": failed,
            "errored": errored, "skipped": skipped, "timed_out": timed_out,
            "pass_rate": round(pass_rate, 4),
            "total_duration_seconds": duration,
        }

    def test_empty_list(self):
        merged = merge_summaries([])
        assert merged["total"] == 0
        assert merged["pass_rate"] == 0.0

    def test_single_summary_preserved(self):
        s = self._s(10, 8, failed=2)
        merged = merge_summaries([s])
        assert merged["total"] == 10
        assert merged["passed"] == 8
        assert merged["failed"] == 2

    def test_two_summaries_add_counts(self):
        merged = merge_summaries([self._s(10, 10), self._s(5, 3, failed=2)])
        assert merged["total"] == 15
        assert merged["passed"] == 13
        assert merged["failed"] == 2

    def test_pass_rate_recomputed_from_totals(self):
        """pass_rate must be computed from merged totals, not averaged."""
        merged = merge_summaries([self._s(10, 10), self._s(10, 0, failed=10)])
        assert merged["total"] == 20
        assert merged["passed"] == 10
        assert merged["pass_rate"] == 0.5

    def test_duration_summed(self):
        merged = merge_summaries([self._s(1, 1, duration=30.0), self._s(1, 1, duration=60.5)])
        assert merged["total_duration_seconds"] == 90.5


# ── _combine_junit_xmls (from test_isaac_lab.py) ─────────────────────────────

# Import separately since test_isaac_lab.py uses omni.repo.ci which may not be available
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "test_isaac_lab",
    os.path.join(os.path.dirname(__file__), "..", "..", "test_isaac_lab.py"),
)
_mod = importlib.util.module_from_spec(_spec)
# Stub out the missing omni imports so the module can be loaded in isolation
import types as _types

_omni = _types.ModuleType("omni")
_omni_repo = _types.ModuleType("omni.repo")
_omni_repo_ci = _types.ModuleType("omni.repo.ci")
_omni_repo_ci.launch = lambda *a, **kw: None  # type: ignore[attr-defined]
_omni_repo_man = _types.ModuleType("omni.repo.man")
_omni_repo_man.find_and_extract_package = lambda *a, **kw: ("", "")  # type: ignore[attr-defined]
_omni.repo = _omni_repo  # type: ignore[attr-defined]
_omni_repo.ci = _omni_repo_ci  # type: ignore[attr-defined]
_omni_repo.man = _omni_repo_man  # type: ignore[attr-defined]
sys.modules.setdefault("omni", _omni)
sys.modules.setdefault("omni.repo", _omni_repo)
sys.modules.setdefault("omni.repo.ci", _omni_repo_ci)
sys.modules.setdefault("omni.repo.man", _omni_repo_man)
_spec.loader.exec_module(_mod)
_combine_junit_xmls = _mod._combine_junit_xmls
_reconcile_exit_code = _mod._reconcile_exit_code


class TestCombineJunitXmls:
    def _write_xml(self, path, suite_name="suite", n_tests=1):
        root = ET.Element("testsuite", name=suite_name)
        for i in range(n_tests):
            ET.SubElement(root, "testcase", name=f"test_{i}")
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def test_combines_multiple_files(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_xml(os.path.join(d, "a.xml"), "suite_a", n_tests=2)
            self._write_xml(os.path.join(d, "b.xml"), "suite_b", n_tests=3)
            out = os.path.join(d, "combined.xml")
            _combine_junit_xmls(d, out)
            root = ET.parse(out).getroot()
            assert root.tag == "testsuites"
            suite_names = {s.get("name") for s in root.findall("testsuite")}
            assert suite_names == {"suite_a", "suite_b"}

    def test_skips_output_file_if_in_directory(self):
        """Output file must not be read back as one of the inputs."""
        with tempfile.TemporaryDirectory() as d:
            self._write_xml(os.path.join(d, "a.xml"), "suite_a")
            out = os.path.join(d, "combined.xml")
            _combine_junit_xmls(d, out)
            # Run again — output file now exists in the dir, must be skipped
            _combine_junit_xmls(d, out)
            root = ET.parse(out).getroot()
            assert len(root.findall("testsuite")) == 1  # only suite_a, not itself

    def test_skips_unparseable_files(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            self._write_xml(os.path.join(d, "good.xml"), "good_suite")
            with open(os.path.join(d, "bad.xml"), "w") as f:
                f.write("<not valid xml")
            out = os.path.join(d, "combined.xml")
            _combine_junit_xmls(d, out)
            root = ET.parse(out).getroot()
            assert len(root.findall("testsuite")) == 1
            assert "Warning" in capsys.readouterr().err

    def test_empty_directory_produces_empty_testsuites(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "combined.xml")
            _combine_junit_xmls(d, out)
            root = ET.parse(out).getroot()
            assert root.tag == "testsuites"
            assert len(root.findall("testsuite")) == 0

    def test_only_xml_files_included(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_xml(os.path.join(d, "a.xml"), "suite_a")
            with open(os.path.join(d, "notes.txt"), "w") as f:
                f.write("not xml")
            out = os.path.join(d, "combined.xml")
            _combine_junit_xmls(d, out)
            root = ET.parse(out).getroot()
            assert len(root.findall("testsuite")) == 1


# ── _reconcile_exit_code (from test_isaac_lab.py) ────────────────────────────

class TestReconcileExitCode:
    def _write_report(self, path, *, failures=0, errors=0, wrap=False):
        suite = ET.Element("testsuite", name="suite", failures=str(failures), errors=str(errors))
        ET.SubElement(suite, "testcase", name="t0")
        root = ET.Element("testsuites") if wrap else suite
        if wrap:
            root.append(suite)
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def test_upgrades_rc_when_suite_has_failures(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.xml")
            self._write_report(p, failures=1)
            assert _reconcile_exit_code(0, p) == 1

    def test_upgrades_rc_when_suite_has_errors(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.xml")
            self._write_report(p, errors=2)
            assert _reconcile_exit_code(0, p) == 1

    def test_handles_testsuites_wrapper(self):
        """Combined reports use <testsuites> root; the helper must descend into children."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.xml")
            self._write_report(p, errors=1, wrap=True)
            assert _reconcile_exit_code(0, p) == 1

    def test_passes_through_zero_when_all_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.xml")
            self._write_report(p)
            assert _reconcile_exit_code(0, p) == 0

    def test_preserves_nonzero_rc_even_when_junit_clean(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.xml")
            self._write_report(p)
            assert _reconcile_exit_code(3, p) == 3

    def test_missing_junit_returns_rc_unchanged(self):
        assert _reconcile_exit_code(0, "/nonexistent/path/r.xml") == 0
        assert _reconcile_exit_code(5, "/nonexistent/path/r.xml") == 5
