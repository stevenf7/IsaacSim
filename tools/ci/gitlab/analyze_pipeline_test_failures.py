#!/usr/bin/env python3
# Copyright (c) 2021-2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""Analyze downloaded GitLab pipeline logs for actionable failure triage.

This script scans a folder produced by `download_pipeline_logs.py` and reports:
  - tests that timed out
  - tests that crashed
  - tests that failed (non-timeout, non-crash)
  - likely fixable diagnostic buckets such as import/API, signature, doc-build,
    and GitLab access/download issues

Primary evidence comes from each job's `job_trace.log` markers, including:
  - [TEST PROCESS FAILED: ...]
  - [EXTENSION TEST FAILED: ...]
  - timed out lines
  - crash reporter lines
  - import/API/doc warnings from build output
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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

MODULE_NOT_FOUND_RE = re.compile(r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]")
IMPORT_ERROR_RE = re.compile(r"ImportError:\s+(.+)")
ATTRIBUTE_ERROR_RE = re.compile(r"AttributeError:\s+module ['\"]([^'\"]+)['\"] has no attribute ['\"]([^'\"]+)['\"]")
GENERIC_ATTRIBUTE_ERROR_RE = re.compile(r"AttributeError:\s+(.+)")
AUTOSUMMARY_FAILED_IMPORT_RE = re.compile(r"autosummary:\s+failed to import\s+(.+?)\.?$", re.IGNORECASE)
AUTODOC_FAILED_IMPORT_RE = re.compile(
    r"autodoc:\s+failed to import\s+(?:function|class|module)\s+'([^']+)'\s+from module\s+'([^']+)'",
    re.IGNORECASE,
)
AUTOSUMMARY_IMPORT_CYCLE_RE = re.compile(r"\[autosummary\.import_cycle\]", re.IGNORECASE)
UNABLE_TO_RESOLVE_FUNCTION_RE = re.compile(r'Unable to resolve function "([^"]+)"', re.IGNORECASE)
INVALID_CPP_DECL_RE = re.compile(r"Invalid C\+\+ declaration:\s+(.+)", re.IGNORECASE)
DOCUTILS_ERROR_RE = re.compile(r"ERROR:\s+(.+)\.\s+\[docutils\]", re.IGNORECASE)
DUPLICATE_LABEL_RE = re.compile(r"duplicate label", re.IGNORECASE)
TOCTREE_RE = re.compile(
    r"document isn't included in any toctree|toctree contains reference to nonexisting document",
    re.IGNORECASE,
)

# Infrastructure / CI-config patterns (not test failures per se)
ARGPARSE_INVALID_CHOICE_RE = re.compile(r"error: argument .+: invalid choice: '([^']+)'")
REPO_CI_COMMAND_FAILED_RE = re.compile(
    r"\[ERROR\]\[omni\.repo\.\w+(?:\.\w+)*\]\s+command\s+'.*'\s+exited with code\s+(\d+)",
)
SYSTEM_MODULE_NOT_FOUND_RE = re.compile(r"/bin/python3?: No module named (\S+)")
APT_PERMISSION_DENIED_RE = re.compile(r"E: Could not open lock file .+ Permission denied|E: Unable to lock directory")
MISSING_DIRECTORY_RE = re.compile(r"ERROR: (\S+) directory not found")
HISTORICAL_FETCH_ERRORS_RE = re.compile(r"Historical fetch finished with (\d+) error")
JOB_FAILED_EXIT_RE = re.compile(
    r"ERROR: Job failed: (?:command (?:exited with|terminated with exit) code|exit status|real exit code:)\s*(\d+)"
)

# ANSI escape stripper
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\r")

ACTIONABLE_BUCKETS = {
    "gitlab_access": {
        "label": "GitLab/auth",
        "recommendation": "Confirm the GitLab token env var and that the token can access the project, pipeline, and job traces.",
    },
    "import_api_exposure": {
        "label": "Import/API exposure",
        "recommendation": "Check package exports, extension enablement, and the exact import path used by docs or tests.",
    },
    "signature_declaration": {
        "label": "Signature/declaration",
        "recommendation": "Fix the generated API signature or the documented C++ declaration so Sphinx/Doxygen can resolve it.",
    },
    "doc_build": {
        "label": "Doc build",
        "recommendation": "Fix the RST or docstring formatting issue and rerun the docs target.",
    },
    "crash_timeout": {
        "label": "Crash/timeout",
        "recommendation": "Reproduce the failing test locally with the matching test command and inspect the trace around the failure marker.",
    },
    "failed_tests": {
        "label": "Test failure",
        "recommendation": "Inspect the failing test marker and rerun the narrowest local test that covers the same code path.",
    },
    "infrastructure": {
        "label": "Infrastructure / CI config",
        "recommendation": "Fix the CI configuration, runner environment, or upstream dependency — these are not test-code bugs.",
    },
}


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


@dataclass(frozen=True)
class DiagnosticRecord:
    bucket: str
    category: str
    summary: str
    recommendation: str
    job_id: int | None
    job_name: str
    stage: str
    status: str
    evidence: str
    file: str
    line: int


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
    parser.add_argument(
        "--output-summary",
        default=None,
        help="Output Markdown summary path (default: <logs-dir>/test_failure_summary.md)",
    )
    return parser.parse_args()


def _load_download_report(logs_dir: Path) -> dict[str, Any]:
    report_path = logs_dir / "download_report.json"
    if not report_path.exists():
        return {}

    try:
        raw_data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"path": str(report_path), "errors": ["download_report.json is not valid JSON"], "jobs": []}

    if isinstance(raw_data, list):
        return {
            "path": str(report_path),
            "legacy_format": True,
            "jobs": raw_data,
            "counts": {
                "jobs_total": len(raw_data),
                "jobs_selected": len(raw_data),
                "jobs_with_errors": sum(1 for job in raw_data if job.get("errors")),
            },
        }

    if isinstance(raw_data, dict):
        raw_data["path"] = str(report_path)
        return raw_data

    return {"path": str(report_path), "errors": ["download_report.json has an unsupported format"], "jobs": []}


def _load_job_metadata(job_dir: Path) -> dict:
    metadata_file = job_dir / "job_metadata.json"
    if not metadata_file.exists():
        return {}
    try:
        return json.loads(metadata_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _job_context(job_meta: dict, fallback_name: str, fallback_file: Path, line_no: int) -> dict[str, Any]:
    return {
        "job_id": job_meta.get("job_id"),
        "job_name": job_meta.get("name", fallback_name),
        "stage": job_meta.get("stage", ""),
        "status": job_meta.get("status", ""),
        "file": str(fallback_file),
        "line": line_no,
    }


def _new_diagnostic(
    bucket: str,
    category: str,
    summary: str,
    recommendation: str,
    evidence: str,
    job_meta: dict,
    trace_path: Path,
    line_no: int,
) -> DiagnosticRecord:
    context = _job_context(job_meta, trace_path.parent.name, trace_path, line_no)
    return DiagnosticRecord(
        bucket=bucket,
        category=category,
        summary=summary,
        recommendation=recommendation,
        job_id=context["job_id"],
        job_name=context["job_name"],
        stage=context["stage"],
        status=context["status"],
        evidence=evidence,
        file=context["file"],
        line=context["line"],
    )


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


def _extract_diagnostics(lines: list[str], job_meta: dict, trace_path: Path) -> list[DiagnosticRecord]:
    records: list[DiagnosticRecord] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        record: DiagnosticRecord | None = None

        if match := MODULE_NOT_FOUND_RE.search(line):
            module_name = match.group(1)
            record = _new_diagnostic(
                "import_api_exposure",
                "module_not_found",
                f"Missing module `{module_name}`",
                f"Check whether `{module_name}` is installed, enabled, or re-exported from the package path used by docs/tests.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := ATTRIBUTE_ERROR_RE.search(line):
            module_name, attribute_name = match.groups()
            record = _new_diagnostic(
                "import_api_exposure",
                "missing_attribute",
                f"Module `{module_name}` is missing `{attribute_name}`",
                f"Check the package exports for `{module_name}` or update the caller to import `{attribute_name}` from its concrete submodule.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := GENERIC_ATTRIBUTE_ERROR_RE.search(line):
            record = _new_diagnostic(
                "import_api_exposure",
                "attribute_error",
                f"Attribute error: {match.group(1)}",
                "Check for API drift between the caller and callee, especially renamed or uninitialized attributes and lifecycle changes.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := IMPORT_ERROR_RE.search(line):
            record = _new_diagnostic(
                "import_api_exposure",
                "import_error",
                f"Import error: {match.group(1)}",
                "Check import ordering, optional dependencies, and whether the referenced symbol/module is exported where the caller expects it.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := AUTOSUMMARY_FAILED_IMPORT_RE.search(line):
            target = match.group(1)
            record = _new_diagnostic(
                "import_api_exposure",
                "autosummary_failed_import",
                f"Autosummary could not import `{target}`",
                f"Check the autosummary target `{target}` and whether the documented symbol is importable from the module as written.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := AUTODOC_FAILED_IMPORT_RE.search(line):
            symbol_name, module_name = match.groups()
            record = _new_diagnostic(
                "import_api_exposure",
                "autodoc_failed_import",
                f"Autodoc could not import `{symbol_name}` from `{module_name}`",
                f"Verify that `{symbol_name}` is exported from `{module_name}` or update the docs to import it from the concrete implementation module.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif AUTOSUMMARY_IMPORT_CYCLE_RE.search(line):
            record = _new_diagnostic(
                "doc_build",
                "autosummary_import_cycle",
                "Autosummary item includes the current module path",
                "Use names relative to the current module in the autosummary block instead of repeating the full current module path.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := UNABLE_TO_RESOLVE_FUNCTION_RE.search(line):
            function_name = match.group(1)
            record = _new_diagnostic(
                "signature_declaration",
                "unresolved_function",
                f"Doxygen could not resolve `{function_name}`",
                f"Check the generated API docs or Doxygen signature for `{function_name}` and ensure the documented overload matches the XML output.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := INVALID_CPP_DECL_RE.search(line):
            record = _new_diagnostic(
                "signature_declaration",
                "invalid_cpp_declaration",
                f"Invalid C++ declaration: {match.group(1)}",
                "Fix the documented C++ signature syntax so the parser can understand the declaration.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := DOCUTILS_ERROR_RE.search(line):
            record = _new_diagnostic(
                "doc_build",
                "docutils_error",
                f"Docutils error: {match.group(1)}",
                "Fix the RST or docstring structure near the reported object and rerun the docs build.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif DUPLICATE_LABEL_RE.search(line):
            record = _new_diagnostic(
                "doc_build",
                "duplicate_label",
                "Duplicate documentation label detected",
                "Rename the duplicate label/anchor so it is unique across the docs build.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif TOCTREE_RE.search(line):
            record = _new_diagnostic(
                "doc_build",
                "toctree_issue",
                "Toctree inclusion problem detected",
                "Fix the toctree entry or add the missing document to the correct toctree.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := ARGPARSE_INVALID_CHOICE_RE.search(line):
            bad_choice = match.group(1)
            record = _new_diagnostic(
                "infrastructure",
                "invalid_suite_or_arg",
                f"Invalid argument `{bad_choice}` — not a valid choice",
                f"Update .gitlab-ci.yml or the calling script: `{bad_choice}` is not a recognised option for this command.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := REPO_CI_COMMAND_FAILED_RE.search(line):
            exit_code = match.group(1)
            record = _new_diagnostic(
                "infrastructure",
                "repo_command_failed",
                f"Repo CI command exited with code {exit_code}",
                "Check the command arguments in the CI job definition and the repo.log for details.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := SYSTEM_MODULE_NOT_FOUND_RE.search(line):
            module_name = match.group(1)
            record = _new_diagnostic(
                "infrastructure",
                "system_module_missing",
                f"System Python missing module `{module_name}`",
                f"The CI runner's system Python lacks `{module_name}`. Install it in the runner image or use the repo's vendored Python.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif APT_PERMISSION_DENIED_RE.search(line):
            record = _new_diagnostic(
                "infrastructure",
                "apt_permission_denied",
                "apt package manager permission denied on runner",
                "The CI runner does not have permission to install packages via apt. Fix the runner image or job permissions.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := MISSING_DIRECTORY_RE.search(line):
            dir_name = match.group(1)
            record = _new_diagnostic(
                "infrastructure",
                "missing_directory",
                f"Expected directory `{dir_name}` not found",
                f"An upstream job likely failed to produce `{dir_name}`. Check that the dependency job succeeded and wrote its artifacts.",
                line,
                job_meta,
                trace_path,
                idx,
            )
        elif match := HISTORICAL_FETCH_ERRORS_RE.search(line):
            error_count = match.group(1)
            record = _new_diagnostic(
                "infrastructure",
                "historical_fetch_error",
                f"Historical data fetch finished with {error_count} error(s)",
                "GitLab API calls for historical pipeline data failed. Check token permissions and whether the target branches/pipelines still exist.",
                line,
                job_meta,
                trace_path,
                idx,
            )

        if record is None:
            continue

        dedupe_key = (record.bucket, record.category, record.summary, record.job_name)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        records.append(record)

    return records


def _read_trace_lines(job_dir: Path, include_success_jobs: bool) -> tuple[dict, Path, list[str]] | None:
    """Read and ANSI-strip a job trace, returning (meta, path, lines) or *None*."""
    job_meta = _load_job_metadata(job_dir)
    status = str(job_meta.get("status", "")).lower()
    if (not include_success_jobs) and status not in {"failed", "canceled"}:
        return None

    trace_path = job_dir / "job_trace.log"
    if not trace_path.exists():
        return None

    try:
        raw = trace_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    clean = _ANSI_ESCAPE_RE.sub("", raw)
    return job_meta, trace_path, clean.splitlines()


def _analyze_job(job_dir: Path, include_success_jobs: bool) -> list[FailureRecord]:
    result = _read_trace_lines(job_dir, include_success_jobs)
    if result is None:
        return []
    job_meta, trace_path, lines = result
    return _classify_failed_tests(lines, job_meta, trace_path)


def _analyze_job_diagnostics(job_dir: Path, include_success_jobs: bool) -> list[DiagnosticRecord]:
    result = _read_trace_lines(job_dir, include_success_jobs)
    if result is None:
        return []
    job_meta, trace_path, lines = result
    return _extract_diagnostics(lines, job_meta, trace_path)


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


def _build_diagnostic_issue_lines(records: list[DiagnosticRecord], repo_root: Path) -> list[dict[str, Any]]:
    issue_lines: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda r: (r.bucket, r.category, r.summary, r.job_name)):
        issue_path = Path(record.file)
        if not issue_path.is_absolute():
            issue_path = (repo_root / issue_path).resolve()
        terminal_link = f"{issue_path}:{record.line}"
        issue_lines.append(
            {
                "bucket": record.bucket,
                "category": record.category,
                "summary": record.summary,
                "terminal_link": terminal_link,
                "job_name": record.job_name,
                "job_id": record.job_id,
                "evidence": record.evidence,
                "recommendation": record.recommendation,
            }
        )
    return issue_lines


def _classify_download_error(error_text: str) -> tuple[str, str, str]:
    lowered = error_text.lower()
    if "401" in lowered or "403" in lowered or "private-token" in lowered or "forbidden" in lowered:
        return (
            "gitlab_access",
            "auth_error",
            "Confirm the token env var and that it has access to the project and pipeline.",
        )
    if "404" in lowered:
        return (
            "gitlab_access",
            "not_found",
            "Check that the pipeline, project, and job IDs are correct and visible to the token.",
        )
    if "timed out" in lowered or "connection" in lowered or "ssl" in lowered:
        return (
            "gitlab_access",
            "network_error",
            "Retry with a working network connection and verify the GitLab host is reachable.",
        )
    return (
        "gitlab_access",
        "download_error",
        "Inspect the GitLab API error text and retry after fixing the reported access or transport problem.",
    )


def _extract_download_diagnostics(download_report: dict[str, Any], logs_dir: Path) -> list[DiagnosticRecord]:
    records: list[DiagnosticRecord] = []
    report_path = Path(download_report.get("path", logs_dir / "download_report.json"))
    for error_text in download_report.get("errors", []):
        bucket, category, recommendation = _classify_download_error(str(error_text))
        records.append(
            DiagnosticRecord(
                bucket=bucket,
                category=category,
                summary=str(error_text),
                recommendation=recommendation,
                job_id=None,
                job_name="download_report",
                stage="",
                status="",
                evidence=str(error_text),
                file=str(report_path),
                line=1,
            )
        )

    for job in download_report.get("jobs", []):
        for error_text in job.get("errors", []):
            bucket, category, recommendation = _classify_download_error(str(error_text))
            records.append(
                DiagnosticRecord(
                    bucket=bucket,
                    category=category,
                    summary=f"Job download issue for `{job.get('name', 'unknown')}`",
                    recommendation=recommendation,
                    job_id=job.get("job_id"),
                    job_name=job.get("name", "unknown"),
                    stage=job.get("stage", ""),
                    status=job.get("status", ""),
                    evidence=str(error_text),
                    file=str(report_path),
                    line=1,
                )
            )
    return records


def _build_actionable_buckets(
    diagnostics: list[DiagnosticRecord],
    failures: list[FailureRecord],
) -> list[dict[str, Any]]:
    buckets: list[dict[str, Any]] = []
    grouped_diagnostics: dict[str, list[DiagnosticRecord]] = {}
    for record in diagnostics:
        grouped_diagnostics.setdefault(record.bucket, []).append(record)

    for bucket_name in ("gitlab_access", "infrastructure", "import_api_exposure", "signature_declaration", "doc_build"):
        bucket_records = grouped_diagnostics.get(bucket_name, [])
        if not bucket_records:
            continue
        unique_jobs = sorted({record.job_name for record in bucket_records})
        buckets.append(
            {
                "bucket": bucket_name,
                "label": ACTIONABLE_BUCKETS[bucket_name]["label"],
                "count": len(bucket_records),
                "jobs": unique_jobs,
                "recommendation": ACTIONABLE_BUCKETS[bucket_name]["recommendation"],
                "examples": [asdict(record) for record in bucket_records[:5]],
            }
        )

    crash_timeout_records = [record for record in failures if record.category in {"crashed", "timed_out"}]
    if crash_timeout_records:
        buckets.append(
            {
                "bucket": "crash_timeout",
                "label": ACTIONABLE_BUCKETS["crash_timeout"]["label"],
                "count": len(crash_timeout_records),
                "jobs": sorted({record.job_name for record in crash_timeout_records}),
                "recommendation": ACTIONABLE_BUCKETS["crash_timeout"]["recommendation"],
                "examples": [asdict(record) for record in crash_timeout_records[:5]],
            }
        )

    failed_only_records = [record for record in failures if record.category == "failed"]
    if failed_only_records:
        buckets.append(
            {
                "bucket": "failed_tests",
                "label": ACTIONABLE_BUCKETS["failed_tests"]["label"],
                "count": len(failed_only_records),
                "jobs": sorted({record.job_name for record in failed_only_records}),
                "recommendation": ACTIONABLE_BUCKETS["failed_tests"]["recommendation"],
                "examples": [asdict(record) for record in failed_only_records[:5]],
            }
        )

    return buckets


def _build_markdown_summary(
    logs_dir: Path,
    failure_counts: dict[str, int],
    diagnostic_records: list[DiagnosticRecord],
    actionable_buckets: list[dict[str, Any]],
    download_report: dict[str, Any],
) -> str:
    lines = [
        "# Pipeline Failure Summary",
        "",
        "## Overview",
        f"- Logs directory: `{logs_dir}`",
        f"- Failure counts: crashed={failure_counts['crashed']}, timed_out={failure_counts['timed_out']}, failed={failure_counts['failed']}, total={failure_counts['total']}",
        f"- Diagnostic matches: {len(diagnostic_records)}",
    ]

    selection = download_report.get("selection")
    if isinstance(selection, dict):
        lines.append(
            f"- Job selection: {selection.get('selected_count', 0)} selected, {selection.get('skipped_count', 0)} skipped"
        )

    lines.extend(["", "## Actionable Buckets"])
    if not actionable_buckets:
        lines.append("- No actionable buckets detected beyond the raw failure markers.")
    else:
        for bucket in actionable_buckets:
            lines.extend(
                [
                    "",
                    f"### {bucket['label']} ({bucket['count']})",
                    bucket["recommendation"],
                ]
            )
            for example in bucket["examples"][:3]:
                evidence = str(example.get("evidence", "")).strip()
                lines.append(f"- `{example.get('job_name', 'unknown')}`: {evidence}")

    return "\n".join(lines) + "\n"


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
    diagnostic_records: list[DiagnosticRecord] = []
    for job_dir in sorted(p for p in logs_dir.iterdir() if p.is_dir()):
        all_records.extend(_analyze_job(job_dir, args.include_success_jobs))
        diagnostic_records.extend(_analyze_job_diagnostics(job_dir, args.include_success_jobs))

    # Coverage gap detection: find failed jobs with zero detections and
    # emit a fallback diagnostic so nothing silently disappears.
    detected_job_ids: set[int] = set()
    for r in all_records:
        if r.job_id is not None:
            detected_job_ids.add(r.job_id)
    for r in diagnostic_records:
        if r.job_id is not None:
            detected_job_ids.add(r.job_id)

    for job_dir in sorted(p for p in logs_dir.iterdir() if p.is_dir()):
        job_meta = _load_job_metadata(job_dir)
        job_id = job_meta.get("job_id")
        status = str(job_meta.get("status", "")).lower()
        if status not in {"failed", "canceled"} or job_id in detected_job_ids:
            continue
        # Scan for the generic "ERROR: Job failed" line to use as evidence
        trace_path = job_dir / "job_trace.log"
        evidence = f"Job {job_id} ({job_meta.get('name', 'unknown')}) failed with no specific pattern detected"
        line_no = 1
        if trace_path.exists():
            try:
                lines = _ANSI_ESCAPE_RE.sub("", trace_path.read_text(encoding="utf-8", errors="replace")).splitlines()
                for idx, raw_line in enumerate(lines, start=1):
                    match = JOB_FAILED_EXIT_RE.search(raw_line)
                    if match:
                        evidence = raw_line.strip()
                        line_no = idx
            except OSError:
                pass
        diagnostic_records.append(
            DiagnosticRecord(
                bucket="infrastructure",
                category="unclassified_failure",
                summary=f"Unclassified failure in `{job_meta.get('name', 'unknown')}`",
                recommendation="Inspect the full job trace — the failure did not match any known pattern. It may be a CI config, environment, or upstream dependency issue.",
                job_id=job_id,
                job_name=job_meta.get("name", "unknown"),
                stage=job_meta.get("stage", ""),
                status=status,
                evidence=evidence,
                file=str(trace_path),
                line=line_no,
            )
        )

    download_report = _load_download_report(logs_dir)
    diagnostic_records.extend(_extract_download_diagnostics(download_report, logs_dir))
    summary = _build_summary(all_records)
    issue_lines = _build_issue_lines(all_records, Path.cwd())
    diagnostic_issue_lines = _build_diagnostic_issue_lines(diagnostic_records, Path.cwd())
    actionable_buckets = _build_actionable_buckets(diagnostic_records, all_records)
    diagnostic_counts = dict(Counter(record.bucket for record in diagnostic_records))
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
        "diagnostic_counts": diagnostic_counts,
        "diagnostic_issue_lines": diagnostic_issue_lines,
        "actionable_buckets": actionable_buckets,
        "download_report": {
            "path": download_report.get("path"),
            "counts": download_report.get("counts", {}),
            "selection": download_report.get("selection", {}),
        },
        "crashed": [r.__dict__ for r in all_records if r.category == "crashed"],
        "timed_out": [r.__dict__ for r in all_records if r.category == "timed_out"],
        "failed": [r.__dict__ for r in all_records if r.category == "failed"],
        "diagnostics": [asdict(record) for record in diagnostic_records],
    }

    output_path = Path(args.output_json) if args.output_json else logs_dir / "test_failure_analysis.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    summary_path = Path(args.output_summary) if args.output_summary else logs_dir / "test_failure_summary.md"
    summary_path.write_text(
        _build_markdown_summary(logs_dir, result["counts"], diagnostic_records, actionable_buckets, download_report),
        encoding="utf-8",
    )

    print("Test failure classification complete")
    print(f"Output: {output_path}")
    print(f"Summary: {summary_path}")
    print(
        f"Counts -> crashed: {result['counts']['crashed']}, "
        f"timed_out: {result['counts']['timed_out']}, "
        f"failed: {result['counts']['failed']}, total: {result['counts']['total']}"
    )
    print(f"Diagnostic buckets: {diagnostic_counts}")
    print(f"Unique tests with issues: {len(summary['all_test_names'])}")
    for test_name in summary["all_test_names"]:
        print(f"  - {test_name}")
    print("Issue lines (category | test | file:line):")
    for item in issue_lines:
        print(f"  - {item['category']} | {item['test_name']} | {item['terminal_link']}")


if __name__ == "__main__":
    main()
