#!/usr/bin/env python3
# Copyright (c) 2021-2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""Classify pipeline test outcomes from downloaded GitLab logs.

This script scans a folder produced by `download_pipeline_logs.py` and reports:
  - tests that timed out
  - tests that crashed
  - tests that failed (non-timeout, non-crash)

Primary evidence comes from each job's `job_trace.log` markers, including:
  - [TEST PROCESS FAILED: ...]
  - [EXTENSION TEST FAILED: ...]
  - timed out lines
  - crash reporter lines
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


TEST_PROCESS_FAILED_RE = re.compile(r"\[TEST PROCESS FAILED:\s*([^\]]+)\]")
EXTENSION_TEST_FAILED_RE = re.compile(r"\[EXTENSION TEST FAILED:\s*([^\]]+)\]")

TIMEOUT_WITH_TEST_RE = [
    re.compile(r"\[ERROR\]\s+(.+?)\s+timed out\.", re.IGNORECASE),
    re.compile(r"Test\s+(.+?)\s+timed out after\s+\d+\s+seconds", re.IGNORECASE),
    re.compile(r"\|\s+(.+?)\s+\|\s+TIMEOUT\s+\|", re.IGNORECASE),
]

CRASH_MARKER_RE = re.compile(
    r"A crash has occurred|Segmentation fault|Fatal Python error|Access violation|core dumped",
    re.IGNORECASE,
)
CRASH_OR_TIMEOUT_AMBIGUOUS_RE = re.compile(r"Process might have crashed or timed out", re.IGNORECASE)
EXPLICIT_TIMEOUT_MARKER_RE = re.compile(
    r"Process timed out|timed out after\s+\d+\s+seconds|\[ERROR\]\s+.+\s+timed out\.|\|\s+.+\s+\|\s+TIMEOUT\s+\|",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FailureRecord:
    category: str
    test_name: str
    job_id: int | None
    job_name: str
    stage: str
    status: str
    evidence: str
    file: str
    line: int


@dataclass(frozen=True)
class FailedTestOccurrence:
    test_name: str
    line: int
    evidence: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze downloaded pipeline logs for crash/timeout/failure tests")
    parser.add_argument(
        "--logs-dir",
        required=True,
        help="Pipeline logs directory from download_pipeline_logs.py (e.g. pipeline_43966473_logs)",
    )
    parser.add_argument(
        "--include-success-jobs",
        action="store_true",
        help="Also scan successful jobs (default scans only failed/canceled jobs)",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Output JSON path (default: <logs-dir>/test_failure_analysis.json)",
    )
    return parser.parse_args()


def _load_job_metadata(job_dir: Path) -> dict:
    metadata_file = job_dir / "job_metadata.json"
    if not metadata_file.exists():
        return {}
    try:
        return json.loads(metadata_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _extract_timeout_tests(lines: list[str]) -> list[tuple[str, int, str]]:
    timeout_tests: list[tuple[str, int, str]] = []
    for idx, line in enumerate(lines, start=1):
        for regex in TIMEOUT_WITH_TEST_RE:
            match = regex.search(line)
            if match:
                timeout_tests.append((match.group(1).strip(), idx, line.strip()))
                break
    return timeout_tests


def _extract_failed_test_occurrences(lines: list[str]) -> list[FailedTestOccurrence]:
    occurrences: list[FailedTestOccurrence] = []
    for idx, line in enumerate(lines, start=1):
        for regex in (TEST_PROCESS_FAILED_RE, EXTENSION_TEST_FAILED_RE):
            match = regex.search(line)
            if match:
                occurrences.append(
                    FailedTestOccurrence(
                        test_name=match.group(1).strip(),
                        line=idx,
                        evidence=line.strip(),
                    )
                )
                break
    return occurrences


def _collect_marker_lines(lines: list[str], regex: re.Pattern[str]) -> set[int]:
    marker_lines: set[int] = set()
    for idx, line in enumerate(lines, start=1):
        if regex.search(line):
            marker_lines.add(idx)
    return marker_lines


def _near_marker(line: int, markers: set[int], window: int) -> bool:
    return any(abs(line - marker) <= window for marker in markers)


def _classify_failed_tests(
    lines: list[str],
    job_meta: dict,
    trace_path: Path,
) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    occurrences = _extract_failed_test_occurrences(lines)
    timeout_tests = _extract_timeout_tests(lines)

    timeout_marker_lines = _collect_marker_lines(lines, EXPLICIT_TIMEOUT_MARKER_RE)
    crash_marker_lines = _collect_marker_lines(lines, CRASH_MARKER_RE)
    ambiguous_crash_timeout_lines = _collect_marker_lines(lines, CRASH_OR_TIMEOUT_AMBIGUOUS_RE)

    seen_key: set[tuple[str, str]] = set()

    for occ in occurrences:
        category = "failed"
        reason = occ.evidence

        matched_timeout = next((t for t in timeout_tests if t[0] == occ.test_name), None)
        if matched_timeout or _near_marker(occ.line, timeout_marker_lines, window=30):
            category = "timed_out"
            if matched_timeout:
                reason = matched_timeout[2]
        elif _near_marker(occ.line, crash_marker_lines, window=600):
            category = "crashed"
        elif _near_marker(occ.line, ambiguous_crash_timeout_lines, window=30):
            category = "crashed"

        dedupe_key = (category, occ.test_name)
        if dedupe_key in seen_key:
            continue
        seen_key.add(dedupe_key)

        records.append(
            FailureRecord(
                category=category,
                test_name=occ.test_name,
                job_id=job_meta.get("job_id"),
                job_name=job_meta.get("name", trace_path.parent.name),
                stage=job_meta.get("stage", ""),
                status=job_meta.get("status", ""),
                evidence=reason,
                file=str(trace_path),
                line=occ.line,
            )
        )

    # Add timeout-only tests that did not emit a failed-test marker.
    seen_timeout_names = {r.test_name for r in records if r.category == "timed_out"}
    for test_name, line_no, evidence in timeout_tests:
        if test_name in seen_timeout_names:
            continue
        records.append(
            FailureRecord(
                category="timed_out",
                test_name=test_name,
                job_id=job_meta.get("job_id"),
                job_name=job_meta.get("name", trace_path.parent.name),
                stage=job_meta.get("stage", ""),
                status=job_meta.get("status", ""),
                evidence=evidence,
                file=str(trace_path),
                line=line_no,
            )
        )

    return records


def _analyze_job(job_dir: Path, include_success_jobs: bool) -> list[FailureRecord]:
    job_meta = _load_job_metadata(job_dir)
    status = str(job_meta.get("status", "")).lower()
    if (not include_success_jobs) and status not in {"failed", "canceled"}:
        return []

    trace_path = job_dir / "job_trace.log"
    if not trace_path.exists():
        return []

    try:
        lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    return _classify_failed_tests(lines, job_meta, trace_path)


def _build_summary(all_records: list[FailureRecord]) -> dict:
    by_category = {
        "crashed": sorted({r.test_name for r in all_records if r.category == "crashed"}),
        "timed_out": sorted({r.test_name for r in all_records if r.category == "timed_out"}),
        "failed": sorted({r.test_name for r in all_records if r.category == "failed"}),
    }
    all_test_names = sorted({r.test_name for r in all_records})
    return {
        "all_test_names": all_test_names,
        "by_category": by_category,
    }


def _build_issue_lines(all_records: list[FailureRecord], repo_root: Path) -> list[dict]:
    issue_lines: list[dict] = []
    for record in sorted(all_records, key=lambda r: (r.category, r.test_name, r.file, r.line)):
        issue_path = Path(record.file)
        if not issue_path.is_absolute():
            issue_path = (repo_root / issue_path).resolve()
        terminal_link = f"{issue_path}:{record.line}"
        issue_lines.append(
            {
                "category": record.category,
                "test_name": record.test_name,
                "terminal_link": terminal_link,
                "job_name": record.job_name,
                "job_id": record.job_id,
                "evidence": record.evidence,
            }
        )
    return issue_lines


def main() -> None:
    args = _parse_args()
    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_dir():
        raise ValueError(f"Logs directory not found: {logs_dir}")

    all_records: list[FailureRecord] = []
    for job_dir in sorted(p for p in logs_dir.iterdir() if p.is_dir()):
        all_records.extend(_analyze_job(job_dir, args.include_success_jobs))

    summary = _build_summary(all_records)
    issue_lines = _build_issue_lines(all_records, Path.cwd())
    result = {
        "logs_dir": str(logs_dir),
        "counts": {
            "crashed": sum(1 for r in all_records if r.category == "crashed"),
            "timed_out": sum(1 for r in all_records if r.category == "timed_out"),
            "failed": sum(1 for r in all_records if r.category == "failed"),
            "total": len(all_records),
        },
        "summary": summary,
        "issue_lines": issue_lines,
        "crashed": [r.__dict__ for r in all_records if r.category == "crashed"],
        "timed_out": [r.__dict__ for r in all_records if r.category == "timed_out"],
        "failed": [r.__dict__ for r in all_records if r.category == "failed"],
    }

    output_path = Path(args.output_json) if args.output_json else logs_dir / "test_failure_analysis.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("Test failure classification complete")
    print(f"Output: {output_path}")
    print(
        f"Counts -> crashed: {result['counts']['crashed']}, "
        f"timed_out: {result['counts']['timed_out']}, "
        f"failed: {result['counts']['failed']}, total: {result['counts']['total']}"
    )
    print(f"Unique tests with issues: {len(summary['all_test_names'])}")
    for test_name in summary["all_test_names"]:
        print(f"  - {test_name}")
    print("Issue lines (category | test | file:line):")
    for item in issue_lines:
        print(f"  - {item['category']} | {item['test_name']} | {item['terminal_link']}")


if __name__ == "__main__":
    main()
