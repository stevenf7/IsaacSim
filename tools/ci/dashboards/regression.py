# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Regression analysis helpers for CI pipeline test reports.

Extracted from ``ci_dashboard.py`` — provides suite-level comparison, failure
classification (new vs. pre-existing), and baseline pipeline discovery via the
GitLab REST API.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.parse
from enum import Enum
from pathlib import Path

from .clients import GitLabClient


# ── Pipeline type detection ──────────────────────────────────────────────────────


class PipelineType(Enum):
    """GitLab CI pipeline type."""

    KIT_MR = "kit_mr"
    KIT_POST_MERGE = "kit_post_merge"
    KIT_NIGHTLY = "kit_nightly"
    ISAAC_NIGHTLY = "isaac_nightly"
    ISAAC_POST_MERGE = "isaac_post_merge"
    ISAAC_MR = "isaac_mr"
    UNKNOWN = "unknown"


def detect_pipeline_type(source_str: str) -> PipelineType:
    """Detect the pipeline type from $CI_PIPELINE_SOURCE and related env vars."""
    upstream = os.getenv("UPSTREAM_PIPELINE_SOURCE")
    if source_str == "pipeline":
        if not os.getenv("UPSTREAM_PIPELINE_ID"):
            return PipelineType.UNKNOWN
        if upstream == "nightly":
            return PipelineType.KIT_NIGHTLY
        if upstream == "merge_request":
            return PipelineType.KIT_MR
        if upstream == "post_merge":
            return PipelineType.KIT_POST_MERGE
        return PipelineType.UNKNOWN
    if source_str == "merge_request_event":
        return PipelineType.ISAAC_MR
    if source_str == "schedule":
        return PipelineType.ISAAC_NIGHTLY
    if source_str == "push":
        return PipelineType.ISAAC_POST_MERGE
    return PipelineType.UNKNOWN


# ── Regression-analysis helpers (adapted from tools/ci/slack/analyze_test_suites.py) ─

from .parsing import strip_inline_job_name as _strip_inline_job_name


def _normalize_suite_name_regr(suite_name: str) -> tuple[str, str]:
    """Normalize a suite name to *(platform, category_key)* for cross-pipeline matching."""
    suite_name = _strip_inline_job_name(suite_name)
    platform = "linux" if "linux" in suite_name.lower() else "windows"
    bracket = re.search(r"\[(.*?)\]", suite_name)
    if bracket:
        parts = [p.strip() for p in bracket.group(1).split(",") if p.strip() not in ("-b", "inline")]
        category_key = "-".join(parts[:2]) if len(parts) >= 2 else (parts[0] if parts else suite_name)
    else:
        found = False
        for i, part in enumerate(suite_name.split("-")):
            if any(kw in part for kw in ("pythontests", "benchmarks", "isaac-lab")):
                category_key = "-".join(suite_name.split("-")[i:])
                found = True
                break
        if not found:
            category_key = suite_name
    return platform, category_key


def _strip_common_prefix_suffix_regr(suite_names: list[str]) -> dict[str, str]:
    """Strip common 'test-' prefix and ', inline]' from suite names for display."""
    result: dict[str, str] = {}
    for name in suite_names:
        stripped = name
        if all(n.startswith("test-") for n in suite_names) and stripped.startswith("test-"):
            stripped = stripped[5:]
        stripped = _strip_inline_job_name(stripped)
        result[name] = stripped
    return result


def _analyze_suite_data(data: dict, quiet: bool = False) -> dict | None:
    """Analyze a GitLab pipeline test_report dict (from ``/pipelines/{id}/test_report``).

    Returns a dict with per-suite and aggregate pass/fail/error counts, or None on failure.
    """
    try:
        suite_counts: dict[str, int] = {}
        suite_unique: dict[str, int] = {}
        suite_pass: dict[str, int] = {}
        suite_fail: dict[str, int] = {}
        suite_error: dict[str, int] = {}
        suite_skip: dict[str, int] = {}
        all_names: set[str] = set()

        for suite in data.get("test_suites", []):
            sname = suite.get("name", "Unknown")
            cases = suite.get("test_cases", [])
            suite_counts[sname] = len(cases)
            suite_pass[sname] = suite.get("success_count", 0)
            suite_fail[sname] = suite.get("failed_count", 0)
            suite_error[sname] = suite.get("error_count", 0)
            suite_skip[sname] = suite.get("skipped_count", 0)
            unique_names = {tc.get("name", "") for tc in cases if tc.get("name")}
            suite_unique[sname] = len(unique_names)
            all_names.update(unique_names)

        return {
            "suite_counts": suite_counts,
            "suite_unique_counts": suite_unique,
            "suite_pass_counts": suite_pass,
            "suite_fail_counts": suite_fail,
            "suite_error_counts": suite_error,
            "suite_skip_counts": suite_skip,
            "unique_test_cases": len(all_names),
            "total_test_cases": sum(suite_counts.values()),
            "total_pass": sum(suite_pass.values()),
            "total_fail": sum(suite_fail.values()),
            "total_error": sum(suite_error.values()),
            "total_skip": sum(suite_skip.values()),
        }
    except Exception as exc:
        if not quiet:
            print(f"  Error analyzing suite data: {exc}")
        return None


def _generate_regression_comparison_text(baseline: dict, test: dict) -> tuple[str, str]:
    """Generate a suite-comparison table and mapping summary (both as strings)."""
    b_suites = baseline.get("suite_counts", {})
    b_pass = baseline.get("suite_pass_counts", {})
    b_fail = baseline.get("suite_fail_counts", {})
    b_error = baseline.get("suite_error_counts", {})
    t_suites = test.get("suite_counts", {})
    t_pass = test.get("suite_pass_counts", {})
    t_fail = test.get("suite_fail_counts", {})
    t_error = test.get("suite_error_counts", {})

    all_names = list(set(b_suites) | set(t_suites))
    name_map = _strip_common_prefix_suffix_regr(all_names)
    max_w = min(max((len(v) for v in name_map.values()), default=60) + 2, 60)

    b_map: dict[tuple, str] = {}
    t_map: dict[tuple, str] = {}
    for sn in b_suites:
        b_map[_normalize_suite_name_regr(sn)] = sn
    for sn in t_suites:
        t_map[_normalize_suite_name_regr(sn)] = sn

    all_keys = sorted(set(b_map) | set(t_map), key=lambda x: (0 if x[0] == "linux" else 1, x[1]))

    lines = [
        "=" * (max_w + 52),
        "COMBINED TEST SUITE COMPARISON",
        "=" * (max_w + 52),
        f"{'Test Suite':{max_w}} {'Base':>4} {'Test':>4} {'':>4} {'Baseline':>20} {'Test':>20} {'Delta (P/F/E)':>18}",
        f"{'':{max_w}} {'Tot':>4} {'Tot':>4} {'Diff':>4} {'Pass':>6} {'Fail':>6} {'Err':>6} {'Pass':>6} {'Fail':>6} {'Err':>6} {'':>18}",
        f"{'-' * max_w} {'-' * 4} {'-' * 4} {'-' * 4} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}",
    ]
    for key in all_keys:
        bn = b_map.get(key, "")
        tn = t_map.get(key, "")
        orig = bn or tn
        disp = name_map.get(orig, orig)
        bt = b_suites.get(bn, 0) if bn else 0
        bp = b_pass.get(bn, 0) if bn else 0
        bf = b_fail.get(bn, 0) if bn else 0
        be = b_error.get(bn, 0) if bn else 0
        tt = t_suites.get(tn, 0) if tn else 0
        tp = t_pass.get(tn, 0) if tn else 0
        tf = t_fail.get(tn, 0) if tn else 0
        te = t_error.get(tn, 0) if tn else 0
        if bt > 0 and tt > 0:
            ds = f"{tt - bt:+d}" if tt != bt else ""
            dp, df, de = tp - bp, tf - bf, te - be
            delta = f"{dp:+d}/{df:+d}/{de:+d}" if any([dp, df, de]) else ""
        else:
            ds, delta = "-", "-"
        lines.append(
            f"{disp:{max_w}} {str(bt) if bt else '-':>4} {str(tt) if tt else '-':>4} {ds:>4} "
            f"{str(bp) if bt else '-':>6} {str(bf) if bt else '-':>6} {str(be) if bt else '-':>6} "
            f"{str(tp) if tt else '-':>6} {str(tf) if tt else '-':>6} {str(te) if tt else '-':>6} "
            f"{delta:>18}"
        )
    b_tot = baseline.get("total_test_cases", 0)
    b_p = baseline.get("total_pass", 0)
    b_f = baseline.get("total_fail", 0)
    b_e = baseline.get("total_error", 0)
    t_tot = test.get("total_test_cases", 0)
    t_p = test.get("total_pass", 0)
    t_f = test.get("total_fail", 0)
    t_e = test.get("total_error", 0)
    td = f"{t_tot - b_tot:+d}" if t_tot != b_tot else "0"
    tdelta = f"{t_p - b_p:+d}/{t_f - b_f:+d}/{t_e - b_e:+d}"
    lines += [
        f"{'-' * max_w} {'-' * 4} {'-' * 4} {'-' * 4} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 18}",
        f"{'TOTAL':{max_w}} {b_tot:>4} {t_tot:>4} {td:>4} {b_p:>6} {b_f:>6} {b_e:>6} {t_p:>6} {t_f:>6} {t_e:>6} {tdelta:>18}",
    ]

    matched = sum(1 for k in all_keys if b_map.get(k) and t_map.get(k))
    b_only = sum(1 for k in all_keys if b_map.get(k) and not t_map.get(k))
    t_only = sum(1 for k in all_keys if t_map.get(k) and not b_map.get(k))
    mapping = [
        "=" * 100, "MAPPING SUMMARY", "=" * 100,
        f"Matched suites (in both): {matched}",
        f"Baseline-only suites: {b_only}",
        f"Test-only suites: {t_only}",
    ]
    if b_only:
        mapping += ["", "Baseline-only:"] + [
            f"  - {b_map[k]}" for k in all_keys if b_map.get(k) and not t_map.get(k)
        ]
    if t_only:
        mapping += ["", "Test-only:"] + [
            f"  - {t_map[k]}" for k in all_keys if t_map.get(k) and not b_map.get(k)
        ]
    return "\n".join(lines), "\n".join(mapping)


def _find_regressions(
    baseline_data: dict,
    test_data: dict,
    output_file: str | None = None,
    test_pipeline_info: dict | None = None,
    baseline_pipeline_info: dict | None = None,
    baseline_analysis: dict | None = None,
    test_analysis: dict | None = None,
    quiet: bool = False,
) -> tuple[list, str, list]:
    """Collect all failing tests from *test_data* and classify each against *baseline_data*.

    Every failing test is tagged:
    - ``"new"``          -- passing (or absent) in baseline, failing now
    - ``"pre-existing"`` -- also failing/errored in baseline
    - ``"unknown"``      -- no baseline data available

    Returns *(all_failures, full_report_str, report_sections_list)*.
    """
    has_baseline = bool(baseline_data and baseline_data.get("test_suites"))
    baseline_map: dict[tuple, str] = {}
    if has_baseline:
        for suite in baseline_data.get("test_suites", []):
            sname = suite.get("name", "Unknown")
            for tc in suite.get("test_cases", []):
                name = tc.get("name", "")
                if name:
                    baseline_map[(sname, name)] = tc.get("status", "")

    all_failures: list[dict] = []
    for suite in test_data.get("test_suites", []):
        sname = suite.get("name", "Unknown")
        for tc in suite.get("test_cases", []):
            name = tc.get("name", "")
            status = tc.get("status", "")
            if not name or status not in ("failed", "error"):
                continue
            if not has_baseline:
                baseline_status, tag = "unknown", "unknown"
            else:
                baseline_status = baseline_map.get((sname, name), "not_in_baseline")
                tag = "pre-existing" if baseline_status in ("failed", "error") else "new"
            all_failures.append({
                "suite_name": sname,
                "test_name": name,
                "test_status": status,
                "baseline_status": baseline_status,
                "tag": tag,
                "system_output": tc.get("system_output", "") or "",
                "stack_trace": tc.get("stack_trace", "") or "",
            })

    new_failures = [f for f in all_failures if f["tag"] == "new"]
    pre_failures = [f for f in all_failures if f["tag"] == "pre-existing"]

    info_lines: list[str] = []
    if baseline_pipeline_info or test_pipeline_info:
        info_lines += ["PIPELINE INFORMATION", "-" * 50]
        for label, pinfo in (("Baseline", baseline_pipeline_info), ("Test", test_pipeline_info)):
            if not pinfo:
                continue
            info_lines.append(f"{label} Pipeline: #{pinfo.get('id')}")
            st, sv = pinfo.get("source_type"), pinfo.get("source_value")
            if st == "mr":
                info_lines.append(f"  Source: MR !{sv}")
            elif st == "branch":
                info_lines.append(f"  Source: Branch '{sv}'")
            if pinfo.get("web_url"):
                info_lines.append(f"  URL: {pinfo['web_url']}")
            info_lines.append("")
    info_section = "\n".join(info_lines)

    cmp_table = mapp_summary = ""
    if baseline_analysis and test_analysis:
        cmp_table, mapp_summary = _generate_regression_comparison_text(baseline_analysis, test_analysis)

    # Build file-friendly failure report
    reg_lines = [
        "=" * 100,
        "FAILING TESTS REPORT",
        "=" * 100,
        "",
        f"Total failures: {len(all_failures)}"
        + (f"  ({len(new_failures)} new, {len(pre_failures)} pre-existing)"
           if has_baseline else "  (no baseline — status unknown)"),
        "",
    ]
    for group_label, group in (("NEW FAILURES", new_failures),
                                ("PRE-EXISTING FAILURES", pre_failures),
                                ("FAILURES (no baseline)", all_failures if not has_baseline else [])):
        if not group:
            continue
        reg_lines += ["", f"{'─' * 60}", group_label, f"{'─' * 60}", ""]
        for i, f in enumerate(group, 1):
            reg_lines += [
                f"#{i}  Suite: {f['suite_name']}",
                f"    Test:  {f['test_name']}",
                f"    Status: {f['test_status'].upper()}"
                + (f"  (baseline: {f['baseline_status']})" if has_baseline else ""),
                "",
            ]
            if f["system_output"]:
                reg_lines += ["    System Output:", "    " + "-" * 46,
                              *("    " + ln for ln in f["system_output"].splitlines()), ""]
            if f["stack_trace"]:
                reg_lines += ["    Stack Trace:", "    " + "-" * 46,
                              *("    " + ln for ln in f["stack_trace"].splitlines()), ""]
    reg_section = "\n".join(reg_lines)

    parts = ["=" * 100, "TEST FAILURE REPORT", "=" * 100, ""]
    if info_section:
        parts += [info_section, ""]
    if cmp_table:
        parts += ["", cmp_table, ""]
    if mapp_summary:
        parts += ["", mapp_summary, ""]
    parts += ["", reg_section]
    full_report = "\n".join(parts)

    if output_file:
        with open(output_file, "w") as f:
            f.write(full_report)
        if not quiet:
            print(f"Found {len(all_failures)} failures "
                  f"({len(new_failures)} new, {len(pre_failures)} pre-existing). "
                  f"Output: {output_file}")

    return all_failures, full_report, [info_section, cmp_table, mapp_summary, reg_section]


def _format_failure_report(all_failures: list[dict], has_baseline: bool, max_listed: int = 30) -> str:
    """Return a Slack-formatted failure summary string.

    Each entry is tagged :new: (regression / not in baseline) or :repeat:
    (pre-existing failure).  When *has_baseline* is False all entries are
    listed without tagging.  *max_listed* caps the total lines shown (0 =
    unlimited); a truncation note is appended when the cap is hit.
    """
    if not all_failures:
        return ":white_check_mark: *No test failures found.*"

    total = len(all_failures)
    new_failures = [f for f in all_failures if f["tag"] == "new"] if has_baseline else []
    pre_failures = [f for f in all_failures if f["tag"] == "pre-existing"] if has_baseline else []

    if has_baseline:
        parts = [f"{len(new_failures)} :new: new"]
        if pre_failures:
            parts.append(f"{len(pre_failures)} :repeat: pre-existing")
        summary = ", ".join(parts)
        header = f":red_circle: *Failing Tests — {total} total ({summary})*"
    else:
        header = f":red_circle: *Failing Tests — {total} total (no baseline available)*"

    lines: list[str] = [header, ""]
    slots = max_listed if max_listed > 0 else 10 ** 9

    def _emit(title: str, group: list[dict]) -> None:
        nonlocal slots
        if not group or slots <= 0:
            return
        lines.append(title)
        for f in group:
            if slots <= 0:
                break
            status = f["test_status"].upper()
            lines.append(f"• `{f['suite_name']}` — {f['test_name']} [{status}]")
            slots -= 1
        lines.append("")

    if has_baseline:
        _emit(f":new: *New failures ({len(new_failures)}):*", new_failures)
        _emit(f":repeat: *Pre-existing failures ({len(pre_failures)}):*", pre_failures)
        remaining_unk = [f for f in all_failures if f["tag"] == "unknown"]
        if remaining_unk:
            _emit(f"*Unknown status ({len(remaining_unk)}):*", remaining_unk)
    else:
        _emit("*Failures:*", all_failures)

    if max_listed > 0 and total > max_listed:
        lines.append(f"_… and {total - max_listed} more — see attached report for full details_")

    return "\n".join(lines)


# ── Regression-analysis API helpers (using GitLabClient) ───────────────────────

def _fetch_pipeline_test_report_api(
    client: "GitLabClient", project_enc: str, pipeline_id: int | str,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> dict | None:
    """Fetch the GitLab test-report JSON for a pipeline via the REST API.

    When *include_patterns* or *exclude_patterns* are provided, jobs are listed
    first and only matching jobs' per-job test reports are fetched and merged.
    This avoids mixing results from unrelated test suites (e.g. IsaacSim tests
    appearing in an IsaacLab regression report).
    """
    if not include_patterns and not exclude_patterns:
        # Fast path: fetch the pipeline-level aggregate report
        try:
            return client.get_json(f"/projects/{project_enc}/pipelines/{pipeline_id}/test_report")
        except Exception as exc:
            print(f"ERROR: Failed to fetch test report for pipeline #{pipeline_id}: {exc}")
            return None

    # Filtered path: list jobs, filter, fetch per-job reports, merge
    try:
        jobs = list(client.get_paginated(f"/projects/{project_enc}/pipelines/{pipeline_id}/jobs"))
    except Exception as exc:
        print(f"ERROR: Failed to list jobs for pipeline #{pipeline_id}: {exc}")
        return None

    def _matches(name: str) -> bool:
        if include_patterns and not any(p in name for p in include_patterns):
            return False
        if exclude_patterns and any(p in name for p in exclude_patterns):
            return False
        return True

    matched_jobs = [j for j in jobs if j.get("status") in ("success", "failed") and _matches(j.get("name", ""))]
    if not matched_jobs:
        print(f"Warning: no jobs matched filters in pipeline #{pipeline_id}", file=sys.stderr)
        return None

    merged: dict = {"total_time": 0, "total_count": 0, "success_count": 0,
                    "failed_count": 0, "skipped_count": 0, "error_count": 0,
                    "test_suites": []}
    for job in matched_jobs:
        try:
            report = client.get_json(f"/projects/{project_enc}/jobs/{job['id']}/test_report")
        except Exception:
            continue
        merged["total_time"] += report.get("total_time", 0)
        merged["total_count"] += report.get("total_count", 0)
        merged["success_count"] += report.get("success_count", 0)
        merged["failed_count"] += report.get("failed_count", 0)
        merged["skipped_count"] += report.get("skipped_count", 0)
        merged["error_count"] += report.get("error_count", 0)
        merged["test_suites"].extend(report.get("test_suites", []))

    return merged if merged["test_suites"] else None


def _get_pipeline_for_analysis(
    client: "GitLabClient",
    project_enc: str,
    source_type: str,
    source_value: str,
    quiet: bool = False,
) -> tuple[dict | None, dict | None]:
    """Return *(pipeline_dict, pipeline_info_dict)* for the given source."""
    try:
        if source_type == "branch":
            items = client.get_json(
                f"/projects/{project_enc}/pipelines",
                params={"ref": source_value, "per_page": 1, "order_by": "id", "sort": "desc"},
            )
            if not items:
                if not quiet:
                    print(f"No pipelines found for branch: {source_value}")
                return None, None
            pl = items[0]
            return pl, {"id": pl["id"], "web_url": pl.get("web_url", ""),
                        "source_type": "branch", "source_value": source_value}

        if source_type == "mr":
            items = client.get_json(
                f"/projects/{project_enc}/merge_requests/{source_value}/pipelines",
                params={"per_page": 1, "order_by": "id", "sort": "desc"},
            )
            if not items:
                if not quiet:
                    print(f"No pipelines found for MR !{source_value}")
                return None, None
            pl = client.get_json(f"/projects/{project_enc}/pipelines/{items[0]['id']}")
            mr = client.get_json(f"/projects/{project_enc}/merge_requests/{source_value}")
            return pl, {"id": pl["id"], "web_url": pl.get("web_url", ""), "source_type": "mr",
                        "source_value": int(source_value), "mr_title": mr.get("title", "")}

        if source_type == "pipeline":
            pl = client.get_json(f"/projects/{project_enc}/pipelines/{source_value}")
            return pl, {"id": pl["id"], "web_url": pl.get("web_url", ""),
                        "source_type": "pipeline", "source_value": int(source_value)}

        print(f"ERROR: Invalid source type '{source_type}'. Must be 'branch', 'mr', or 'pipeline'.")
        return None, None
    except Exception as exc:
        print(f"ERROR: Failed to get pipeline for {source_type}={source_value}: {exc}")
        return None, None


def _run_regression_analysis(
    client: "GitLabClient",
    project_enc: str,
    source_type: str,
    source_value: str,
    baseline_type: str,
    baseline_value: str,
    output_file: str | None = None,
    quiet: bool = False,
    include_job_patterns: list[str] | None = None,
    exclude_job_patterns: list[str] | None = None,
) -> tuple[list, list] | None:
    """Fetch test reports and classify failures. Returns *(sections, all_failures)* or None."""
    baseline_pl, baseline_info = _get_pipeline_for_analysis(
        client, project_enc, baseline_type, baseline_value, quiet)
    if baseline_pl is None:
        return None
    baseline_data = _fetch_pipeline_test_report_api(
        client, project_enc, baseline_pl["id"],
        include_patterns=include_job_patterns, exclude_patterns=exclude_job_patterns)
    if not baseline_data:
        print("ERROR: Failed to fetch baseline test report")
        return None
    baseline_analysis = _analyze_suite_data(baseline_data, quiet=quiet)
    if not baseline_analysis:
        print("ERROR: Failed to analyze baseline data")
        return None

    test_pl, test_info = _get_pipeline_for_analysis(
        client, project_enc, source_type, source_value, quiet)
    if test_pl is None:
        return None
    test_data = _fetch_pipeline_test_report_api(
        client, project_enc, test_pl["id"],
        include_patterns=include_job_patterns, exclude_patterns=exclude_job_patterns)
    if not test_data:
        print("ERROR: Failed to fetch test pipeline test report")
        return None
    test_analysis = _analyze_suite_data(test_data, quiet=quiet)
    if not test_analysis:
        print("ERROR: Failed to analyze test pipeline data")
        return None

    all_failures, _, sections = _find_regressions(
        baseline_data, test_data,
        output_file=output_file,
        test_pipeline_info=test_info,
        baseline_pipeline_info=baseline_info,
        baseline_analysis=baseline_analysis,
        test_analysis=test_analysis,
        quiet=quiet,
    )
    return sections, all_failures


# ── Baseline finder (rewritten to use GitLabClient) ────────────────────────────

def _find_baseline_pipeline(
    client: "GitLabClient",
    project_enc: str,
    branch: str = "develop",
    skip_sources: list[str] | None = None,
    skip_commit_pattern: str = "Bumped version",
    max_pages: int = 10,
) -> dict | None:
    """Find the most recent suitable baseline pipeline on *branch*.

    Skips pipelines whose source is in *skip_sources* and those whose commit
    message contains *skip_commit_pattern*.
    """
    _skip = list(skip_sources or ["schedule"])
    for pipeline in client.get_paginated(
        f"/projects/{project_enc}/pipelines",
        params={"ref": branch, "scope": "finished", "order_by": "id", "sort": "desc"},
        max_pages=max_pages,
    ):
        if pipeline.get("status") not in ("success", "failed"):
            continue
        if pipeline.get("source", "") in _skip:
            continue
        sha = pipeline.get("sha", "")
        if sha and skip_commit_pattern:
            try:
                commit = client.get_json(f"/projects/{project_enc}/repository/commits/{sha}")
                if skip_commit_pattern in commit.get("message", ""):
                    continue
            except Exception:
                continue
        return pipeline
    return None
