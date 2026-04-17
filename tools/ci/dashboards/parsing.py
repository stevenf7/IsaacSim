# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""JUnit XML and GitLab test-report parsing utilities for CI dashboards."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET


# ── Constants ───────────────────────────────────────────────────────────────────

# Job names that produce the IsaacLab JUnit XML artifact
ISAACLAB_JOB_NAMES = {
    "test-linux-x86_64-isaac-lab-integration",
    "test-linux-x86_64-isaac-lab-integration-nightly",
    # Legacy names (renamed circa 2026-04 — keep until historical data ages out)
    "test-linux-x86_64-isaaclab-integration",
    "test-linux-x86_64-isaaclab-integration-nightly",
}

# Stop searching for pipelines after this many consecutive misses (no matching
# test jobs found).  Prevents exhausting all API pages when the job name has
# changed or the branch has never had the expected jobs.
MAX_CONSECUTIVE_MISSES = 20

# Path of the JUnit XML file within the artifact archive
ARTIFACT_PATH = "_isaaclab/tests/full_report.xml"

# GitLab pipeline status → our conclusion field
_CONCLUSION_MAP = {
    "success": "success",
    "failed":  "failure",
    "canceled": "cancelled",
}

SCHEMA_VERSION = 1

STATUS_PRIORITY = {"timeout": 5, "error": 4, "fail": 3, "skip": 2, "pass": 1}


def strip_inline_job_name(name: str) -> str:
    """Strip ', inline]' suffix so inline and after_script job names match."""
    return name.replace(", inline]", "]") if ", inline]" in name else name


# ── JUnit XML parsing ────────────────────────────────────────────────────────────

def get_testcase_status(tc: ET.Element) -> str:
    """Determine status for a single <testcase> element."""
    children = list(tc)
    if not children:
        return "pass"
    for child in children:
        tag = child.tag.lower()
        if tag == "failure":
            return "fail"
        if tag == "error":
            msg = (child.get("message") or "").lower()
            if "timed out" in msg or "timeout" in msg:
                return "timeout"
            return "error"
        if tag == "skipped":
            return "skip"
    return "pass"


def worst_status(*statuses: str) -> str:
    return max(statuses, key=lambda s: STATUS_PRIORITY.get(s, 0))


def _status_counts(status: str) -> tuple[int, int, int, int, int, int]:
    """Return (total, passed, failed, errored, skipped, timed_out) for one status."""
    return (
        1,
        1 if status == "pass" else 0,
        1 if status == "fail" else 0,
        1 if status == "error" else 0,
        1 if status == "skip" else 0,
        1 if status == "timeout" else 0,
    )


def parse_junit_xml(xml_bytes: bytes) -> tuple[dict, dict]:
    """Parse JUnit XML bytes into the dashboard's sections format.

    Each top-level ``<testsuite>`` becomes a section (a collapsible group in
    the dashboard).  Within each section, every ``<testcase>`` becomes its
    own suite row so the heatmap shows one row per test — but the per-suite
    ``getSections`` expansion that used to happen in JS is now done here,
    once, at ingest time.  This preserves visual grouping without the
    per-cell rebuild cost that made the IsaacLab dashboard sluggish.

    Returns:
        (summary dict, sections dict) where ``sections`` has the same shape
        as sections-mode ingest:
        ``{section_name: {job_id, job_url, summary, suites}}``.
    """
    root = ET.fromstring(xml_bytes)

    if root.tag == "testsuites":
        suites_elems = [s for s in root if s.tag == "testsuite"]
    elif root.tag == "testsuite":
        suites_elems = [root]
    else:
        suites_elems = list(root.iter("testsuite"))

    sections: dict = {}
    total = passed = failed = errored = skipped = timed_out = 0
    total_duration = 0.0

    for suite in suites_elems:
        suite_name = suite.get("name", "unknown")
        is_timeout_suite = suite_name.startswith("timeout_")

        per_case_suites: dict = {}
        s_total = s_passed = s_failed = s_errored = s_skipped = s_timed_out = 0
        s_duration = 0.0
        s_worst = "pass"
        used_keys: set[str] = set()

        for tc in suite.findall("testcase"):
            status = get_testcase_status(tc)
            if is_timeout_suite and status == "error":
                status = "timeout"
            duration = round(float(tc.get("time", 0) or 0), 3)
            case_name = tc.get("name", "")
            classname = tc.get("classname", "")

            # Give every case a unique row key.  Prefer the test name, fall
            # back to ``classname::name``, then to a numeric suffix when even
            # that collides (parametrized tests can repeat).
            key = case_name or "unnamed"
            if key in used_keys:
                key = f"{classname}::{case_name}" if classname else f"{case_name}#{len(used_keys)}"
                n = 1
                while key in used_keys:
                    key = f"{classname}::{case_name}#{n}" if classname else f"{case_name}#{n}"
                    n += 1
            used_keys.add(key)

            c_tot, c_pass, c_fail, c_err, c_skip, c_to = _status_counts(status)
            per_case_suites[key] = {
                "total": c_tot,
                "passed": c_pass,
                "failed": c_fail,
                "errored": c_err,
                "skipped": c_skip,
                "timed_out": c_to,
                "duration_seconds": duration,
                "worst_status": status,
                "cases": [{
                    "name": case_name,
                    "classname": classname,
                    "duration_seconds": duration,
                    "status": status,
                }],
            }

            s_total += c_tot
            s_passed += c_pass
            s_failed += c_fail
            s_errored += c_err
            s_skipped += c_skip
            s_timed_out += c_to
            s_duration += duration
            s_worst = worst_status(s_worst, status)

        if not per_case_suites:
            continue

        # Disambiguate section names when an XML has duplicates (rare).
        sec_key = suite_name
        n = 1
        while sec_key in sections:
            sec_key = f"{suite_name}#{n}"
            n += 1

        sections[sec_key] = {
            "job_id": None,
            "job_url": None,
            "summary": {
                "total": s_total,
                "passed": s_passed,
                "failed": s_failed,
                "errored": s_errored,
                "skipped": s_skipped,
                "timed_out": s_timed_out,
                "pass_rate": round(s_passed / s_total, 4) if s_total else 0.0,
                "total_duration_seconds": round(s_duration, 2),
                "worst_status": s_worst,
            },
            "suites": per_case_suites,
        }

        total += s_total
        passed += s_passed
        failed += s_failed
        errored += s_errored
        skipped += s_skipped
        timed_out += s_timed_out
        total_duration += s_duration

    pass_rate = passed / total if total > 0 else 0.0
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
        "timed_out": timed_out,
        "pass_rate": round(pass_rate, 4),
        "total_duration_seconds": round(total_duration, 2),
    }

    return summary, sections


def merge_summaries(summaries: list[dict]) -> dict:
    """Merge a list of summary dicts into one aggregate."""
    merged = {
        "total": 0, "passed": 0, "failed": 0, "errored": 0,
        "skipped": 0, "timed_out": 0, "total_duration_seconds": 0.0,
    }
    for s in summaries:
        for k in merged:
            merged[k] += s.get(k, 0)
    total = merged["total"]
    merged["pass_rate"] = round(merged["passed"] / total, 4) if total > 0 else 0.0
    merged["total_duration_seconds"] = round(merged["total_duration_seconds"], 2)
    return merged


# ── GitLab test-report API parser ─────────────────────────────────────────────

def parse_test_report_api(report: dict) -> tuple[dict, dict]:
    """Convert a GitLab pipeline test_report API response to (summary, suites).

    Used as a fallback when the JUnit XML artifact has expired.  GitLab stores
    the processed test-report data server-side independently of artifact
    retention, so it survives the 2-week artifact expiry window.

    GitLab test-case statuses: "success" | "failed" | "skipped" | "error"
    """
    _STATUS = {"success": "pass", "failed": "fail", "skipped": "skip", "error": "error"}

    def _is_timeout(tc: dict) -> bool:
        """Check if a test case represents a timeout based on its output text."""
        for field in ("system_output", "stack_trace"):
            text = (tc.get(field) or "").lower()
            if "timed out" in text or "timeout" in text:
                return True
        return False

    suites_data = {}
    total = passed = failed = errored = skipped = timed_out = 0
    total_duration = 0.0

    for suite in report.get("test_suites", []):
        # Group test cases by classname within each suite so the dashboard
        # shows one row per test class (matching the JUnit XML granularity)
        # rather than one giant row per CI job.
        classname_groups: dict[str, list[dict]] = {}
        for tc in suite.get("test_cases", []):
            raw_status = tc.get("status", "")
            st = _STATUS.get(raw_status)
            if st is None:
                print(f"Warning: unknown test case status {raw_status!r}, treating as pass", file=sys.stderr)
                st = "pass"
            # Promote errors/failures with timeout indicators to "timeout" status
            if st in ("error", "fail") and _is_timeout(tc):
                st = "timeout"
            duration = float(tc.get("execution_time") or 0)
            key = tc.get("classname", "") or suite.get("name", "unknown")
            classname_groups.setdefault(key, []).append({
                "name": tc.get("name", ""),
                "classname": key,
                "duration_seconds": round(duration, 3),
                "status": st,
            })

        for cls_name, cases in classname_groups.items():
            s_pass = sum(1 for c in cases if c["status"] == "pass")
            s_fail = sum(1 for c in cases if c["status"] == "fail")
            s_err = sum(1 for c in cases if c["status"] == "error")
            s_skip = sum(1 for c in cases if c["status"] == "skip")
            s_timeout = sum(1 for c in cases if c["status"] == "timeout")
            s_dur = sum(c["duration_seconds"] for c in cases)
            s_total = s_pass + s_fail + s_err + s_skip + s_timeout
            s_worst = "pass"
            for c in cases:
                s_worst = worst_status(s_worst, c["status"])

            suites_data[cls_name] = {
                "total": s_total,
                "passed": s_pass,
                "failed": s_fail,
                "errored": s_err,
                "skipped": s_skip,
                "timed_out": s_timeout,
                "duration_seconds": round(s_dur, 2),
                "worst_status": s_worst,
                "cases": cases,
            }

            total += s_total
            passed += s_pass
            failed += s_fail
            errored += s_err
            skipped += s_skip
            timed_out += s_timeout
            total_duration += s_dur

    pass_rate = passed / total if total > 0 else 0.0
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
        "timed_out": timed_out,
        "pass_rate": round(pass_rate, 4),
        "total_duration_seconds": round(total_duration, 2),
    }
    return summary, suites_data
