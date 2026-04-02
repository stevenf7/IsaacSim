# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Manage the IsaacLab integration test dashboard.

Subcommands:

ci — called by the ``generate-isaac-lab-dashboard`` GitLab job.
Processes the current pipeline's JUnit XML, updates the cache, and generates
dashboard output::

    python tools/ci/isaac_lab_dashboard.py ci \\
        --junit-xml        _isaaclab/tests/full_report.xml \\
        --isaac-lab-branch "${ISAAC_LAB_BRANCH:-develop}" \\
        --data-dir         _dashboard_cache
    # --pipeline-id, --pipeline-url, --commit-sha, --isaac-sim-branch default
    # from $CI_PIPELINE_ID, $CI_PIPELINE_URL, $CI_COMMIT_SHA, and
    # $CI_MERGE_REQUEST_TARGET_BRANCH_NAME / $CI_COMMIT_REF_NAME respectively.

fetch-gitlab — pull historical data from GitLab into the local cache.
Tokens are resolved automatically from environment variables
(``GITLAB_AUTH_TOKEN`` → ``GITLAB_TOKEN`` → ``GITLAB_API_TOKEN``).
Run via the manual ``get-isaaclab-historical-data`` CI job or locally::

    export GITLAB_AUTH_TOKEN=glpat-...
    python tools/ci/isaac_lab_dashboard.py fetch-gitlab \\
        --isaac-sim-branch develop \\
        --isaac-lab-branch develop \\
        --data-dir    _dashboard_cache

    # Add --force-refetch to re-download runs already in the cache.
    # Add --verbose for per-pipeline progress.

fetch-github — pull IsaacLab GitHub Actions build/compat data into the local cache.
Token resolved from ``GITHUB_NVIDIA_DEV_TOKEN`` → ``GITHUB_TOKEN`` → ``GITHUB_API_TOKEN``::

    export GITHUB_NVIDIA_DEV_TOKEN=ghp-...   # optional but recommended
    python tools/ci/isaac_lab_dashboard.py fetch-github \\
        --data-dir _dashboard_cache

generate — rebuild dashboard HTML from the local cache, no network calls::

    python tools/ci/isaac_lab_dashboard.py generate \\
        --data-dir   _dashboard_cache
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable, Generator
from datetime import datetime, timezone
from pathlib import Path

# Optional: requests is only needed in fetch mode
try:
    import requests as _requests
except ImportError:
    _requests = None

# Token resolution: check env vars in priority order and record which one was used.
_GITLAB_TOKEN_VARS: tuple[str, ...] = ("GITLAB_AUTH_TOKEN", "GITLAB_TOKEN", "GITLAB_API_TOKEN")
_GITHUB_TOKEN_VARS: tuple[str, ...] = ("GITHUB_NVIDIA_DEV_TOKEN", "GITHUB_TOKEN", "GITHUB_API_TOKEN")


def _resolve_token(var_names: tuple[str, ...]) -> tuple[str, str | None]:
    """Return (value, var_name) for the first non-empty env var in *var_names*."""
    for var in var_names:
        val = os.environ.get(var, "")
        if val:
            return val, var
    return "", None


# ── Constants ───────────────────────────────────────────────────────────────────

# Job names that produce the IsaacLab JUnit XML artifact
ISAACLAB_JOB_NAMES = {
    "test-linux-x86_64-isaaclab-integration",
    "test-linux-x86_64-isaaclab-integration-nightly",
}

# Path of the JUnit XML file within the artifact archive
ARTIFACT_PATH = "_isaaclab/tests/full_report.xml"

# GitLab pipeline status → our conclusion field
_CONCLUSION_MAP = {
    "success": "success",
    "failed":  "failure",
    "canceled": "cancelled",
}

# GitHub API settings
GITHUB_BASE_URL = "https://api.github.com/repos/isaac-sim/IsaacLab"
COMPAT_VERSIONS = ["4.5.0", "5.0.0"]
SCHEMA_VERSION = 1


# ── JUnit XML parsing (verbatim from IsaacLab collect_data.py lines 151-288) ──

STATUS_PRIORITY = {"timeout": 5, "error": 4, "fail": 3, "skip": 2, "pass": 1}


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


def parse_junit_xml(xml_bytes: bytes) -> tuple[dict, dict]:
    """Parse JUnit XML bytes.

    Returns:
        (summary dict, suites dict)
    """
    root = ET.fromstring(xml_bytes)

    if root.tag == "testsuites":
        suites_elems = [s for s in root if s.tag == "testsuite"]
    elif root.tag == "testsuite":
        suites_elems = [root]
    else:
        suites_elems = list(root.iter("testsuite"))

    suites_data = {}
    total = passed = failed = errored = skipped = timed_out = 0
    total_duration = 0.0

    for suite in suites_elems:
        suite_name = suite.get("name", "unknown")
        is_timeout_suite = suite_name.startswith("timeout_")

        suite_total = suite_passed = suite_failed = suite_errored = 0
        suite_skipped = suite_timed_out = 0
        suite_duration = 0.0
        suite_worst = "pass"
        cases = []

        for tc in suite.findall("testcase"):
            status = get_testcase_status(tc)
            if is_timeout_suite and status == "error":
                status = "timeout"

            duration = float(tc.get("time", 0) or 0)
            suite_duration += duration
            suite_total += 1

            if status == "pass":
                suite_passed += 1
            elif status == "fail":
                suite_failed += 1
            elif status == "error":
                suite_errored += 1
            elif status == "skip":
                suite_skipped += 1
            elif status == "timeout":
                suite_timed_out += 1

            suite_worst = worst_status(suite_worst, status)
            cases.append({
                "name": tc.get("name", ""),
                "classname": tc.get("classname", ""),
                "duration_seconds": round(duration, 3),
                "status": status,
            })

        if suite_duration == 0:
            suite_duration = float(suite.get("time", 0) or 0)

        suites_data[suite_name] = {
            "total": suite_total,
            "passed": suite_passed,
            "failed": suite_failed,
            "errored": suite_errored,
            "skipped": suite_skipped,
            "timed_out": suite_timed_out,
            "duration_seconds": round(suite_duration, 2),
            "worst_status": suite_worst,
            "cases": cases,
        }

        total += suite_total
        passed += suite_passed
        failed += suite_failed
        errored += suite_errored
        skipped += suite_skipped
        timed_out += suite_timed_out
        total_duration += suite_duration

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


# ── Cache helpers ───────────────────────────────────────────────────────────────

def load_runs_index(data_dir: str | Path) -> dict:
    path = Path(data_dir) / "runs.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"Warning: runs.json at {path} is corrupt ({exc}); starting fresh.", file=sys.stderr)
    return {"schema_version": 1, "last_updated": "", "runs": []}


def save_runs_index(data_dir: str | Path, index: dict) -> None:
    path = Path(data_dir) / "runs.json"
    path.write_text(json.dumps(index, indent=2))


def cached_pipeline_ids(runs_index: dict) -> set[int]:
    """Return the set of pipeline IDs that already have test data fetched.

    Runs recorded with data_fetched=False are intentionally excluded so that a
    subsequent fetch-gitlab call will retry them (e.g. to hit the test-report API
    fallback added after the initial fetch).
    """
    return {r["pipeline_id"] for r in runs_index["runs"] if r.get("data_fetched")}


def _branch_subdir(data_dir: str | Path, branch: str) -> Path:
    """Return the branch-specific subdirectory, sanitizing the branch name."""
    safe = branch.replace("/", "-").replace("\\", "-")
    return Path(data_dir) / safe


def _collect_all_branch_runs(data_dir: str | Path) -> dict:
    """Scan data_dir subdirectories for runs.json files.

    Returns a dict mapping workflow key (e.g. ``"isaaclab_develop"``) to
    ``(branch_dir: Path, runs_index: dict)`` for each branch subdir found.
    Skips known non-branch directories (``github``, ``output``, ``tests``).
    """
    branch_runs = {}
    data_dir = Path(data_dir)
    _SKIP = {"github", "output", "tests"}
    for subdir in sorted(data_dir.iterdir()):
        if not subdir.is_dir() or subdir.name in _SKIP:
            continue
        runs_file = subdir / "runs.json"
        if runs_file.exists():
            try:
                runs_index = json.loads(runs_file.read_text())
            except json.JSONDecodeError as exc:
                print(f"Warning: skipping corrupt runs.json in {subdir}: {exc}", file=sys.stderr)
                continue
            workflow_key = f"isaaclab_{subdir.name}"
            branch_runs[workflow_key] = (subdir, runs_index)
    return branch_runs


def _add_branch_placeholders(branch_runs: dict, extra_branches: list[str]) -> dict:
    """Add empty placeholder entries for configured branches absent from the cache.

    Placeholder entries use ``None`` as the branch directory; ``generate_output``
    handles them by emitting an empty ``{"runs": [], "test_data": {}}`` block so
    the branch appears in the dashboard dropdown even with no cached data.
    """
    result = dict(branch_runs)
    for branch in extra_branches:
        branch = branch.strip()
        if not branch:
            continue
        safe = branch.replace("/", "-").replace("\\", "-")
        key = f"isaaclab_{safe}"
        if key not in result:
            result[key] = (None, {"runs": []})
    return result


# ── GitHub API client ───────────────────────────────────────────────────────────

class GitHubClient:
    def __init__(self, token: str | None = None, verbose: bool = False) -> None:
        if _requests is None:
            print("Error: 'requests' package is required for the fetch-github subcommand.", file=sys.stderr)
            print("Install it with:  pip install requests", file=sys.stderr)
            sys.exit(1)
        self.session = _requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            print(
                "\n⚠  WARNING: No GitHub token provided.\n"
                "   Rate limit: 60 req/hr (unauthenticated) vs 5000/hr (authenticated).\n"
                "   Set GITHUB_NVIDIA_DEV_TOKEN, GITHUB_TOKEN, or GITHUB_API_TOKEN for full throughput.\n",
                file=sys.stderr,
            )
        self.verbose = verbose

    def _check_rate_limit(self, response: _requests.Response) -> None:
        remaining = int(response.headers.get("X-RateLimit-Remaining", 999))
        if remaining <= 5:
            reset_ts = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(0, reset_ts - time.time()) + 2
            print(f"⏳ GitHub rate limit low ({remaining} remaining). Sleeping {wait:.0f}s…", file=sys.stderr)
            time.sleep(wait)

    def get(self, path: str, **kwargs) -> _requests.Response:
        url = path if path.startswith("http") else f"{GITHUB_BASE_URL}{path}"
        if self.verbose:
            print(f"  GH GET {url}", file=sys.stderr)
        resp = self.session.get(url, **kwargs)
        self._check_rate_limit(resp)
        resp.raise_for_status()
        return resp

    def get_json(self, path: str, **kwargs) -> dict:
        return self.get(path, **kwargs).json()


# ── GitHub artifact helpers ─────────────────────────────────────────────────────

def _gh_find_workflow_id(client: GitHubClient, workflow_path: str) -> int:
    workflows = client.get_json("/actions/workflows")
    for wf in workflows.get("workflows", []):
        if wf["path"] == workflow_path:
            return wf["id"]
    raise ValueError(f"Workflow not found: {workflow_path}")


def _gh_get_run_duration(client: GitHubClient, run_id: int) -> int | None:
    try:
        jobs = client.get_json(f"/actions/runs/{run_id}/jobs")
        started_times, completed_times = [], []
        for job in jobs.get("jobs", []):
            if job.get("started_at"):
                started_times.append(datetime.fromisoformat(job["started_at"].replace("Z", "+00:00")))
            if job.get("completed_at"):
                completed_times.append(datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00")))
        if started_times and completed_times:
            return int((max(completed_times) - min(started_times)).total_seconds())
    except Exception as exc:
        print(f"    duration unavailable for run {run_id}: {exc}", file=sys.stderr)
    return None


def _gh_download_artifact_zip(client: GitHubClient, artifact_id: int) -> bytes | None:
    """Download artifact ZIP bytes. Returns None on 410 Gone (expired)."""
    try:
        resp = client.get(f"/actions/artifacts/{artifact_id}/zip", allow_redirects=True)
        return resp.content
    except Exception as e:
        if hasattr(e, "response") and e.response is not None and e.response.status_code == 410:
            return None
        raise


def _gh_extract_xml_from_zip(zip_bytes: bytes, filename: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        if filename in names:
            return zf.read(filename)
        for name in names:
            if name.lower() == filename.lower():
                return zf.read(name)
        for name in names:
            if os.path.basename(name) == filename:
                return zf.read(name)
        raise FileNotFoundError(f"{filename!r} not in ZIP. Contents: {names}")


def _gh_extract_all_xmls_from_zip(zip_bytes: bytes) -> list[bytes]:
    results = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                results.append(zf.read(name))
    return results


# ── GitHub cache helpers ────────────────────────────────────────────────────────

def _gh_load_index(gh_dir: Path, workflow: str) -> dict | None:
    path = gh_dir / f"runs_{workflow}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def _gh_save_index(gh_dir: Path, workflow: str, data: dict) -> None:
    gh_dir.mkdir(parents=True, exist_ok=True)
    (gh_dir / f"runs_{workflow}.json").write_text(json.dumps(data, indent=2))


def _gh_load_test_data(gh_dir: Path, subdir: str, run_id: int) -> dict | None:
    path = gh_dir / subdir / f"{run_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def _gh_save_test_data(gh_dir: Path, subdir: str, run_id: int, data: dict) -> None:
    out_dir = gh_dir / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{run_id}.json").write_text(json.dumps(data, indent=2))


def _gh_merge_run_indexes(new_runs: list[dict], existing_runs_dict: dict) -> list[dict]:
    new_ids = {r["run_id"] for r in new_runs}
    merged = new_runs + [r for r in existing_runs_dict.values() if r["run_id"] not in new_ids]
    merged.sort(key=lambda r: r["run_id"], reverse=True)
    return merged


# ── GitHub per-run processors ───────────────────────────────────────────────────

def _process_build_run_gh(
    client: GitHubClient, run: dict, force_refetch: bool, gh_dir: Path, verbose: bool, label: str = ""
) -> dict:
    run_id = run["id"]
    pr_number = run["pull_requests"][0]["number"] if run.get("pull_requests") else None
    conclusion = run.get("conclusion", "unknown")
    print(f"  {label}Build run {run_id} (PR #{pr_number}, {conclusion})", file=sys.stderr)

    duration = _gh_get_run_duration(client, run_id)
    artifacts_resp = client.get_json(f"/actions/runs/{run_id}/artifacts")
    artifact_id = None
    for art in artifacts_resp.get("artifacts", []):
        name = art["name"]
        if pr_number and name == f"pr-{pr_number}-combined-test-results":
            artifact_id = art["id"]
            break
        if "combined-test-results" in name and artifact_id is None:
            artifact_id = art["id"]

    data_fetched = False
    already_cached = _gh_load_test_data(gh_dir, "tests_build", run_id) is not None

    if artifact_id and (force_refetch or not already_cached):
        zip_bytes = _gh_download_artifact_zip(client, artifact_id)
        if zip_bytes is not None:
            try:
                xml_bytes = _gh_extract_xml_from_zip(zip_bytes, "combined-results.xml")
                summary, suites = parse_junit_xml(xml_bytes)
                _gh_save_test_data(gh_dir, "tests_build", run_id, {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "summary": summary,
                    "suites": suites,
                })
                data_fetched = True
                print(
                    f"    ✅ Parsed: {summary['passed']}/{summary['total']} passed "
                    f"({summary['pass_rate']*100:.1f}%)",
                    file=sys.stderr
                )
            except Exception as e:
                print(f"    ⚠  XML parse failed for run {run_id}: {e}", file=sys.stderr)
        else:
            print(f"    ⚠  Artifact {artifact_id} expired for run {run_id}", file=sys.stderr)
    elif already_cached:
        data_fetched = True
        if verbose:
            print(f"    ↩  Using cached data for run {run_id}", file=sys.stderr)

    return {
        "run_id": run_id,
        "run_number": run["run_number"],
        "pr_number": pr_number,
        "head_sha": run["head_sha"],
        "head_branch": run.get("head_branch", ""),
        "event": run.get("event", ""),
        "conclusion": conclusion,
        "created_at": run["created_at"],
        "duration_seconds": duration,
        "artifact_id": artifact_id,
        "data_file": f"tests_build/{run_id}.json",
        "data_fetched": data_fetched,
    }


def _process_compat_run_gh(
    client: GitHubClient, run: dict, force_refetch: bool, gh_dir: Path, verbose: bool, label: str = ""
) -> dict:
    run_id = run["id"]
    conclusion = run.get("conclusion", "unknown")
    print(f"  {label}Compat run {run_id} ({conclusion})", file=sys.stderr)

    duration = _gh_get_run_duration(client, run_id)
    artifacts_resp = client.get_json(f"/actions/runs/{run_id}/artifacts")
    artifacts_by_name = {art["name"]: art for art in artifacts_resp.get("artifacts", [])}

    already_cached = _gh_load_test_data(gh_dir, "tests_compat", run_id) is not None

    if not force_refetch and already_cached:
        data_fetched = True
        if verbose:
            print(f"    ↩  Using cached data for run {run_id}", file=sys.stderr)
    else:
        versions_data = {}
        for version in COMPAT_VERSIONS:
            version_xml_list = []
            for art_name in [f"isaaclab-tasks-compat-results-{version}", f"general-tests-compat-results-{version}"]:
                art = artifacts_by_name.get(art_name)
                if not art:
                    continue
                zip_bytes = _gh_download_artifact_zip(client, art["id"])
                if zip_bytes is None:
                    if verbose:
                        print(f"    ⚠  {art_name} expired", file=sys.stderr)
                    continue
                try:
                    version_xml_list.extend(_gh_extract_all_xmls_from_zip(zip_bytes))
                except Exception as e:
                    print(f"    ⚠  Failed to read {art_name}: {e}", file=sys.stderr)

            if version_xml_list:
                v_summaries, v_suites = [], {}
                for xml_bytes in version_xml_list:
                    try:
                        s, suites = parse_junit_xml(xml_bytes)
                        v_summaries.append(s)
                        v_suites.update(suites)
                    except Exception as e:
                        print(f"    ⚠  XML parse error ({version}): {e}", file=sys.stderr)
                if v_summaries:
                    versions_data[version] = {
                        "summary": merge_summaries(v_summaries),
                        "suites": v_suites,
                    }

        combined_art = artifacts_by_name.get(f"daily-compat-{run_id}-combined-test-results")
        aggregate_summary, aggregate_suites = None, {}
        if combined_art:
            zip_bytes = _gh_download_artifact_zip(client, combined_art["id"])
            if zip_bytes is not None:
                try:
                    xml_bytes = _gh_extract_xml_from_zip(zip_bytes, "combined-compat-results.xml")
                    aggregate_summary, aggregate_suites = parse_junit_xml(xml_bytes)
                except Exception as e:
                    print(f"    ⚠  Combined compat XML failed: {e}", file=sys.stderr)

        data_fetched = bool(versions_data or aggregate_summary)
        if data_fetched:
            test_data = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "versions": versions_data}
            if aggregate_summary:
                test_data["aggregate"] = {"summary": aggregate_summary, "suites": aggregate_suites}
            elif versions_data:
                agg_suites, agg_summaries = {}, []
                for v_data in versions_data.values():
                    agg_summaries.append(v_data["summary"])
                    agg_suites.update(v_data["suites"])
                test_data["aggregate"] = {
                    "summary": merge_summaries(agg_summaries),
                    "suites": agg_suites,
                }
            _gh_save_test_data(gh_dir, "tests_compat", run_id, test_data)
            if verbose:
                agg = test_data.get("aggregate", {}).get("summary", {})
                print(f"    ✅ Compat parsed: {agg.get('passed','?')}/{agg.get('total','?')} passed", file=sys.stderr)

    return {
        "run_id": run_id,
        "run_number": run["run_number"],
        "head_sha": run["head_sha"],
        "head_branch": run.get("head_branch", ""),
        "event": run.get("event", ""),
        "conclusion": conclusion,
        "created_at": run["created_at"],
        "duration_seconds": duration,
        "isaacsim_versions": COMPAT_VERSIONS,
        "data_file": f"tests_compat/{run_id}.json",
        "data_fetched": data_fetched,
    }


def _fetch_github_workflow_runs(
    client: GitHubClient, workflow_id: int, max_runs: int, max_cached_id: int,
    force_refetch: bool, process_fn: Callable, gh_dir: Path, verbose: bool,
) -> list[dict]:
    runs_data = []
    url = f"{GITHUB_BASE_URL}/actions/workflows/{workflow_id}/runs"
    params = {"per_page": 100, "status": "completed"}
    fetched = 0
    stop = False

    while not stop and fetched < max_runs:
        resp = client.get(url, params=params)
        data = resp.json()
        params = {}

        for run in data.get("workflow_runs", []):
            run_id = run["id"]
            if run_id <= max_cached_id and not force_refetch:
                stop = True
                break
            if fetched >= max_runs:
                stop = True
                break
            label = f"[{fetched+1}/{max_runs}] "
            runs_data.append(process_fn(client, run, force_refetch, gh_dir, verbose, label))
            fetched += 1

        next_url = resp.links.get("next", {}).get("url")
        if not next_url or stop:
            break
        url = next_url

    return runs_data


def _fetch_and_save_github_workflow(
    client: GitHubClient, workflow_name: str, workflow_path: str, process_fn: Callable,
    max_runs: int, force: bool, gh_dir: Path, verbose: bool,
) -> dict:
    """Fetch one GitHub workflow, merge with existing cache, save index, and return the index."""
    print(f"🔍 Fetching GitHub {workflow_name} workflow runs…", file=sys.stderr)
    wf_id = _gh_find_workflow_id(client, workflow_path)
    existing = _gh_load_index(gh_dir, workflow_name)
    max_cached = existing["max_cached_run_id"] if existing else 0
    existing_runs = {r["run_id"]: r for r in existing.get("runs", [])} if existing else {}

    new_runs = _fetch_github_workflow_runs(
        client, wf_id, max_runs,
        max_cached if not force else 0,
        force, process_fn, gh_dir, verbose,
    )
    merged = _gh_merge_run_indexes(new_runs, existing_runs)
    index = {
        "schema_version": SCHEMA_VERSION,
        "workflow": workflow_name,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "max_cached_run_id": merged[0]["run_id"] if merged else 0,
        "runs": merged,
    }
    _gh_save_index(gh_dir, workflow_name, index)
    fetched_count = sum(1 for r in merged if r.get("data_fetched"))
    print(f"✅ GitHub {workflow_name}: {len(merged)} runs, {fetched_count} with test data", file=sys.stderr)
    return index


def fetch_github_data(args: argparse.Namespace, gh_dir: str | Path) -> tuple[dict, dict]:
    """Fetch/update GitHub build+compat data and return (build_index, compat_index).

    Data is cached under *gh_dir* using the same structure as IsaacLab's
    ``tools/dashboard/data/`` directory.  Only new runs (beyond what is already
    cached) are fetched unless ``--force-refetch`` is set.
    """
    client = GitHubClient(token=args.github_token or None, verbose=args.verbose)
    gh_dir = Path(gh_dir)
    force = args.force_refetch

    build_index = _fetch_and_save_github_workflow(
        client, "build", ".github/workflows/build.yml",
        _process_build_run_gh, args.github_max_runs, force, gh_dir, args.verbose,
    )
    compat_index = _fetch_and_save_github_workflow(
        client, "compat", ".github/workflows/daily-compatibility.yml",
        _process_compat_run_gh, args.github_max_runs, force, gh_dir, args.verbose,
    )
    return build_index, compat_index


# ── Output generation (shared by all modes) ─────────────────────────────────────

def _load_github_from_cache(gh_dir: str | Path) -> dict:
    """Load GitHub build/compat indexes and test data from *gh_dir* cache.

    Returns a dict with 'build' and 'compat' keys ready for merging into
    dashboard_data, or an empty dict if no GitHub cache exists.
    """
    gh_dir = Path(gh_dir)
    result = {}
    for workflow in ("build", "compat"):
        index = _gh_load_index(gh_dir, workflow)
        if index is None:
            continue
        subdir = f"tests_{workflow}"
        test_data = {}
        for run in index.get("runs", []):
            if run.get("data_fetched"):
                td = _gh_load_test_data(gh_dir, subdir, run["run_id"])
                if td:
                    test_data[str(run["run_id"])] = td
        result[workflow] = {"runs": index.get("runs", []), "test_data": test_data}
        print(f"Loaded GitHub '{workflow}' cache: {len(test_data)} run(s) with test data")
    return result


def generate_output(branch_runs: dict, output_dir: str | Path, github_data_dir: str | Path | None = None) -> None:
    """Write data/data.js and copy index.html into output_dir.

    Args:
        branch_runs: dict mapping workflow key (e.g. "isaaclab_develop") to
                     (branch_dir: Path, runs_index: dict) tuples.
        output_dir: directory to write dashboard files into.
        github_data_dir: optional path to GitHub cache directory.
    """
    output_dir = Path(output_dir)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    output_dir.mkdir(parents=True, exist_ok=True)
    data_out_dir = output_dir / "data"
    data_out_dir.mkdir(parents=True, exist_ok=True)

    dashboard_data = {"generated_at": now}
    total_runs = 0
    for workflow_key, (bdir, runs_index) in branch_runs.items():
        if bdir is None:
            # Placeholder for a configured branch with no cached data yet.
            dashboard_data[workflow_key] = {"runs": [], "test_data": {}}
            continue
        test_data = {}
        for run in runs_index["runs"]:
            pid = str(run["pipeline_id"])
            per_run_file = bdir / run["data_file"]
            if per_run_file.exists():
                try:
                    test_data[pid] = json.loads(per_run_file.read_text())
                except json.JSONDecodeError as exc:
                    print(f"Warning: skipping corrupt per-run JSON {per_run_file}: {exc}", file=sys.stderr)
        dashboard_data[workflow_key] = {"runs": runs_index["runs"], "test_data": test_data}
        total_runs += len(runs_index["runs"])

    # Merge GitHub build/compat data from the cache directory
    if github_data_dir:
        try:
            github_data = _load_github_from_cache(github_data_dir)
            dashboard_data.update(github_data)
        except Exception as exc:
            print(f"Warning: could not load GitHub cache from {github_data_dir}: {exc}", file=sys.stderr)

    data_js_path = data_out_dir / "data.js"
    data_js_path.write_text(
        "window.DASHBOARD_DATA = " + json.dumps(dashboard_data, separators=(",", ":")) + ";\n"
    )
    branch_summary = ", ".join(f"{k}: {len(v['runs'])}" for k, v in dashboard_data.items()
                               if k not in ("generated_at", "build", "compat"))
    print(f"Generated {data_js_path} ({total_runs} GitLab run(s) — {branch_summary})")

    script_dir = Path(__file__).parent
    html_src = script_dir.parent / "dashboard" / "isaac_lab" / "index.html"
    html_dst = output_dir / "isaac_lab_test_dashboard.html"
    if html_src.exists():
        shutil.copy2(html_src, html_dst)
        print(f"Copied dashboard HTML to {html_dst}")
    else:
        print(f"Error: dashboard HTML not found at {html_src}", file=sys.stderr)
        sys.exit(1)

    print(f"Dashboard output ready in {output_dir}/")


# ── GitLab API client ───────────────────────────────────────────────────────────

class GitLabClient:
    def __init__(self, gitlab_url: str, token: str | None = None, verbose: bool = False) -> None:
        if _requests is None:
            print("Error: 'requests' package is required for the fetch-gitlab subcommand.", file=sys.stderr)
            print("Install it with:  pip install requests", file=sys.stderr)
            sys.exit(1)

        self.base_url = f"{gitlab_url.rstrip('/')}/api/v4"
        self.session = _requests.Session()
        if token:
            self.session.headers["PRIVATE-TOKEN"] = token
        else:
            print(
                "\n⚠  WARNING: No GitLab token provided.\n"
                "   Set GITLAB_AUTH_TOKEN, GITLAB_TOKEN, or GITLAB_API_TOKEN for authenticated access.\n"
                "   Without a token, most NVIDIA GitLab endpoints will return 401.\n",
                file=sys.stderr,
            )
        self.verbose = verbose

    def get(self, path: str, **kwargs) -> _requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if self.verbose:
            print(f"  GET {url}", file=sys.stderr)
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def get_json(self, path: str, **kwargs) -> dict:
        return self.get(path, **kwargs).json()

    def get_paginated(self, path: str, params: dict | None = None, max_pages: int = 20) -> Generator:
        """Yield all items from a paginated list endpoint."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        page = 1
        while page <= max_pages:
            params["page"] = page
            items = self.get_json(path, params=params)
            if not items:
                break
            yield from items
            if len(items) < params["per_page"]:
                break
            page += 1


# ── GitLab test-report API parser ──────────────────────────────────────────────

def parse_test_report_api(report: dict) -> tuple[dict, dict]:
    """Convert a GitLab pipeline test_report API response to (summary, suites).

    Used as a fallback when the JUnit XML artifact has expired.  GitLab stores
    the processed test-report data server-side independently of artifact
    retention, so it survives the 2-week artifact expiry window.

    GitLab test-case statuses: "success" | "failed" | "skipped" | "error"
    """
    _STATUS = {"success": "pass", "failed": "fail", "skipped": "skip", "error": "error"}

    suites_data = {}
    total = passed = failed = errored = skipped = 0
    total_duration = 0.0

    for suite in report.get("test_suites", []):
        suite_name = suite.get("name", "unknown")
        suite_passed = suite_failed = suite_errored = suite_skipped = 0
        suite_duration = 0.0
        suite_worst = "pass"
        cases = []

        for tc in suite.get("test_cases", []):
            raw_status = tc.get("status", "")
            status = _STATUS.get(raw_status)
            if status is None:
                print(f"Warning: unknown test case status {raw_status!r}, treating as pass", file=sys.stderr)
                status = "pass"
            duration = float(tc.get("execution_time") or 0)
            suite_duration += duration

            if status == "pass":    suite_passed += 1
            elif status == "fail":  suite_failed += 1
            elif status == "error": suite_errored += 1
            elif status == "skip":  suite_skipped += 1

            suite_worst = worst_status(suite_worst, status)
            cases.append({
                "name": tc.get("name", ""),
                "classname": tc.get("classname", ""),
                "duration_seconds": round(duration, 3),
                "status": status,
            })

        suite_total = suite_passed + suite_failed + suite_errored + suite_skipped
        suites_data[suite_name] = {
            "total": suite_total,
            "passed": suite_passed,
            "failed": suite_failed,
            "errored": suite_errored,
            "skipped": suite_skipped,
            "timed_out": 0,
            "duration_seconds": round(suite_duration, 2),
            "worst_status": suite_worst,
            "cases": cases,
        }

        total += suite_total
        passed += suite_passed
        failed += suite_failed
        errored += suite_errored
        skipped += suite_skipped
        total_duration += suite_duration

    pass_rate = passed / total if total > 0 else 0.0
    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errored": errored,
        "skipped": skipped,
        "timed_out": 0,
        "pass_rate": round(pass_rate, 4),
        "total_duration_seconds": round(total_duration, 2),
    }
    return summary, suites_data


# ── Fetch mode helpers ──────────────────────────────────────────────────────────

def _get_pipeline_duration(client: GitLabClient, project_enc: str, pipeline_id: int) -> int | None:
    """Return wall-clock duration in seconds, or None if unavailable."""
    try:
        detail = client.get_json(f"/projects/{project_enc}/pipelines/{pipeline_id}")
        # GitLab returns a 'duration' field (seconds) on finished pipelines
        if detail.get("duration"):
            return int(detail["duration"])
        # Fallback: compute from timestamps
        started = detail.get("started_at")
        finished = detail.get("finished_at")
        if started and finished:
            s = datetime.fromisoformat(started.replace("Z", "+00:00"))
            f = datetime.fromisoformat(finished.replace("Z", "+00:00"))
            return max(0, int((f - s).total_seconds()))
    except Exception as exc:
        print(f"    duration unavailable for pipeline {pipeline_id}: {exc}", file=sys.stderr)
    return None


def _find_isaaclab_job(client: GitLabClient, project_enc: str, pipeline_id: int) -> dict | None:
    """Return the first finished isaaclab job dict for this pipeline, or None."""
    try:
        jobs = list(client.get_paginated(
            f"/projects/{project_enc}/pipelines/{pipeline_id}/jobs"
        ))
    except Exception as exc:
        print(f"    could not list jobs for pipeline {pipeline_id}: {exc}", file=sys.stderr)
        return None

    for job in jobs:
        if job.get("name") in ISAACLAB_JOB_NAMES and job.get("status") in ("success", "failed"):
            return job
    return None


def _download_junit_xml(client: GitLabClient, project_enc: str, job_id: int) -> bytes | None:
    """Download the JUnit XML artifact bytes from a job, or return None."""
    try:
        artifact_url = f"/projects/{project_enc}/jobs/{job_id}/artifacts/{ARTIFACT_PATH}"
        resp = client.get(artifact_url)
        return resp.content
    except Exception as exc:
        print(f"    artifact download failed for job {job_id}: {exc}", file=sys.stderr)
        return None


def run_fetch_mode(args: argparse.Namespace) -> None:
    """Fetch historical pipeline data from GitLab and build the dashboard."""
    client = GitLabClient(args.gitlab_url, token=args.token, verbose=args.verbose)
    project_enc = urllib.parse.quote(args.project, safe="")

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    branch_dir = _branch_subdir(args.data_dir, args.isaac_sim_branch)
    branch_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = branch_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    runs_index = load_runs_index(branch_dir)
    already_cached = cached_pipeline_ids(runs_index)

    print(
        f"Fetching pipelines for {args.project} ref={args.isaac_sim_branch} "
        f"(max {args.max_runs} with isaaclab data, {len(already_cached)} already cached)…"
    )

    found = 0
    checked = 0
    new_records = []

    pipeline_params = {"ref": args.isaac_sim_branch, "scope": "finished", "order_by": "id", "sort": "desc"}

    for pipeline in client.get_paginated(
        f"/projects/{project_enc}/pipelines",
        params=pipeline_params,
        max_pages=50,
    ):
        if found >= args.max_runs:
            break

        pipeline_id = pipeline["id"]
        checked += 1

        # Skip already-cached runs unless --force-refetch
        if pipeline_id in already_cached and not args.force_refetch:
            if args.verbose:
                print(f"  [{checked}] Pipeline {pipeline_id}: already cached, skipping", file=sys.stderr)
            found += 1  # count it toward max_runs so we stop at the right depth
            continue

        label = f"[{checked}] Pipeline {pipeline_id}"
        job = _find_isaaclab_job(client, project_enc, pipeline_id)
        if job is None:
            if args.verbose:
                print(f"  {label}: no isaaclab job, skipping", file=sys.stderr)
            continue

        print(f"  {label}: found job '{job['name']}' ({job['status']})", file=sys.stderr)

        duration = _get_pipeline_duration(client, project_enc, pipeline_id)
        conclusion = _CONCLUSION_MAP.get(pipeline.get("status", ""), "unknown")

        # Try 1: download the raw JUnit XML artifact
        xml_bytes = _download_junit_xml(client, project_enc, job["id"])
        data_fetched = False
        summary, suites = {}, {}

        if xml_bytes:
            try:
                summary, suites = parse_junit_xml(xml_bytes)
                data_fetched = True
                print(f"    ✓ artifact  {summary['passed']}/{summary['total']} passed ({summary['pass_rate']*100:.1f}%)", file=sys.stderr)
            except Exception as exc:
                print(f"    ⚠  XML parse failed: {exc}", file=sys.stderr)

        # Try 2: fall back to GitLab's stored test-report (survives artifact expiry)
        if not data_fetched:
            if xml_bytes is None:
                print(f"    ⚠  artifact expired — trying test-report API…", file=sys.stderr)
            try:
                report = client.get_json(
                    f"/projects/{project_enc}/jobs/{job['id']}/test_report"
                )
                summary, suites = parse_test_report_api(report)
                if summary.get("total", 0) > 0:
                    data_fetched = True
                    print(
                        f"    ✓ test-report {summary['passed']}/{summary['total']} passed "
                        f"({summary['pass_rate']*100:.1f}%)",
                        file=sys.stderr
                    )
                else:
                    print(f"    ⚠  test-report returned no test cases", file=sys.stderr)
            except Exception as exc:
                print(f"    ⚠  test-report API failed: {exc}", file=sys.stderr)

        if not data_fetched:
            print(f"    ✗  no test data available for pipeline {pipeline_id}", file=sys.stderr)

        if data_fetched:
            failed_count = summary["failed"] + summary["errored"] + summary.get("timed_out", 0)
            conclusion = "success" if failed_count == 0 else "failure"

        # Save per-run JSON
        per_run_path = tests_dir / f"{pipeline_id}.json"
        per_run_path.write_text(json.dumps({"summary": summary, "suites": suites},
                                            separators=(",", ":")))

        # Determine isaac_lab_branch: prefer value stored in the pipeline's variables if
        # available; fall back to the CLI arg.  (GitLab doesn't expose trigger variables
        # on the pipeline list endpoint, so we just use the CLI arg here.)
        new_records.append({
            "pipeline_id": pipeline_id,
            "commit_sha": pipeline.get("sha", ""),
            "isaac_sim_branch": pipeline.get("ref", args.isaac_sim_branch),
            "isaac_lab_branch": args.isaac_lab_branch,
            "conclusion": conclusion,
            "created_at": pipeline.get("created_at", ""),
            "pipeline_url": pipeline.get("web_url", ""),
            "job_url": job.get("web_url", ""),
            "duration_seconds": duration,
            "data_file": f"tests/{pipeline_id}.json",
            "data_fetched": data_fetched,
        })
        found += 1

    if not new_records and not already_cached:
        print("No isaaclab pipelines found. Check --isaac-sim-branch and the project argument.", file=sys.stderr)
        sys.exit(1)

    # Merge new records into the index (replace any existing entry for the same pipeline_id)
    updated_ids = {r["pipeline_id"] for r in new_records}
    kept = [r for r in runs_index["runs"] if r["pipeline_id"] not in updated_ids]
    runs_index["runs"] = sorted(
        new_records + kept,
        key=lambda r: r["pipeline_id"],
        reverse=True,  # newest first
    )
    runs_index["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_runs_index(branch_dir, runs_index)
    print(f"Cache updated: {len(runs_index['runs'])} total run(s) ({len(new_records)} new/refreshed)")


def _generate_from_cache(data_dir: str | Path, output_dir: str | Path) -> None:
    """Collect all branch runs from *data_dir* and generate dashboard output."""
    gh_dir = Path(data_dir) / "github"
    branch_runs = _collect_all_branch_runs(data_dir)
    extra_branches = [
        b.strip()
        for b in os.environ.get("ISAAC_LAB_CI_REPORT_BRANCHES", "").splitlines()
        if b.strip()
    ]
    if extra_branches:
        branch_runs = _add_branch_placeholders(branch_runs, extra_branches)
    generate_output(branch_runs, output_dir,
                    github_data_dir=gh_dir if gh_dir.exists() else None)


def run_github_fetch_only(args: argparse.Namespace) -> None:
    """Fetch GitHub workflow data into the local cache."""
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    fetch_github_data(args, data_dir / "github")


# ── CI mode ─────────────────────────────────────────────────────────────────────

def _report_newly_failing_tests(current_suites: dict, prev_suites: dict) -> int:
    """Print tests that were passing in *prev_suites* but are failing now.

    Returns the count of newly failing tests.
    """
    newly_failing = []
    for suite_name, suite_data in current_suites.items():
        prev_suite = prev_suites.get(suite_name, {})
        prev_cases = {tc["name"]: tc["status"] for tc in prev_suite.get("cases", [])}
        for tc in suite_data.get("cases", []):
            status = tc.get("status", "pass")
            if status in ("fail", "error", "timeout"):
                if prev_cases.get(tc["name"]) == "pass":
                    newly_failing.append((suite_name, tc["name"], status))

    if newly_failing:
        print(f"\n⚠  {len(newly_failing)} newly failing test(s) (passed in previous run):")
        for suite_name, test_name, status in newly_failing:
            print(f"  [{status}] {suite_name} :: {test_name}")
    else:
        print("\n✓  No newly failing tests (no regression vs previous run).")

    return len(newly_failing)


def run_ci_mode(args: argparse.Namespace) -> None:
    """Process the current pipeline's JUnit XML and update the cache."""
    pipeline_id = int(args.pipeline_id)
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    branch_dir = _branch_subdir(args.data_dir, args.isaac_sim_branch)
    branch_dir.mkdir(parents=True, exist_ok=True)
    (branch_dir / "tests").mkdir(parents=True, exist_ok=True)

    junit_path = Path(args.junit_xml)
    if junit_path.exists():
        xml_bytes = junit_path.read_bytes()
        try:
            summary, suites = parse_junit_xml(xml_bytes)
        except ET.ParseError as exc:
            print(f"Warning: malformed JUnit XML at {junit_path}: {exc}; recording run without test data", file=sys.stderr)
            summary, suites = {}, {}
            conclusion = "failure"
            data_fetched = False
        else:
            failed_count = summary["failed"] + summary["errored"] + summary["timed_out"]
            conclusion = "success" if failed_count == 0 else "failure"
            data_fetched = True
            print(
                f"Parsed {summary['total']} tests: "
                f"{summary['passed']} passed, {summary['failed']} failed, "
                f"{summary['errored']} errored, {summary['timed_out']} timed out, "
                f"{summary['skipped']} skipped"
            )
    else:
        print(f"Warning: JUnit XML not found at {junit_path}, recording run without test data", file=sys.stderr)
        summary, suites = {}, {}
        conclusion = "failure"
        data_fetched = False

    runs_index = load_runs_index(branch_dir)
    runs_index["runs"] = [r for r in runs_index["runs"] if r.get("pipeline_id") != pipeline_id]

    per_run_path = branch_dir / "tests" / f"{pipeline_id}.json"
    per_run_path.write_text(json.dumps({"summary": summary, "suites": suites},
                                        separators=(",", ":")))

    # Report regressions: tests that were passing in the previous run but are failing now.
    if data_fetched and suites:
        prev_runs = [r for r in runs_index["runs"] if r.get("data_fetched")]
        if prev_runs:
            prev_run_file = branch_dir / prev_runs[0]["data_file"]
            try:
                prev_data = json.loads(prev_run_file.read_text())
                _report_newly_failing_tests(suites, prev_data.get("suites", {}))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Note: could not load previous run data for regression comparison: {exc}", file=sys.stderr)
        else:
            print("\nNo previous run in cache — skipping regression comparison.")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    runs_index["runs"].insert(0, {
        "pipeline_id": pipeline_id,
        "commit_sha": args.commit_sha,
        "isaac_sim_branch": args.isaac_sim_branch,
        "isaac_lab_branch": args.isaac_lab_branch,
        "conclusion": conclusion,
        "created_at": now,
        "pipeline_url": args.pipeline_url,
        "data_file": f"tests/{pipeline_id}.json",
        "data_fetched": data_fetched,
        "is_ci_run": True,
    })
    runs_index["last_updated"] = now
    save_runs_index(branch_dir, runs_index)
    print(f"Cache updated: {len(runs_index['runs'])} total run(s) in branch '{args.isaac_sim_branch}'")

    _generate_from_cache(data_dir, args.output_dir)


# ── Generate-only mode ──────────────────────────────────────────────────────────

def run_generate_only_mode(args: argparse.Namespace) -> None:
    """Rebuild data.js + HTML from the local cache without any network calls."""
    branch_runs = _collect_all_branch_runs(args.data_dir)
    if not branch_runs:
        print("Warning: no branch subdirectories with runs.json found in cache. "
              "Dashboard will be empty.", file=sys.stderr)
    else:
        for wk, (_, ri) in branch_runs.items():
            print(f"Loaded {len(ri['runs'])} run(s) from cache for '{wk}'.")
    _generate_from_cache(args.data_dir, args.output_dir)


# ── Argument parser & dispatch ──────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── ci ─────────────────────────────────────────────────────────────────────
    ci_p = subparsers.add_parser(
        "ci",
        help="Record current pipeline JUnit XML into cache and regenerate dashboard",
        description="Process the current pipeline's JUnit XML, update the cache, and generate dashboard output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ci_p.add_argument("--data-dir", default="_dashboard_cache",
                      help="Cache directory (default: _dashboard_cache)")
    ci_p.add_argument("--output-dir", default=None,
                      help="Output directory (default: <data-dir>/output)")
    ci_p.add_argument("--isaac-lab-branch", default="develop",
                      help="IsaacLab branch name (default: develop)")
    ci_p.add_argument("--junit-xml", required=True,
                      help="Path to the JUnit XML report produced by pytest")
    ci_p.add_argument("--pipeline-id",
                      default=os.environ.get("CI_PIPELINE_ID", ""),
                      help="GitLab CI pipeline ID (default: $CI_PIPELINE_ID)")
    ci_p.add_argument("--pipeline-url",
                      default=os.environ.get("CI_PIPELINE_URL", ""),
                      help="GitLab CI pipeline URL (default: $CI_PIPELINE_URL)")
    ci_p.add_argument("--commit-sha",
                      default=os.environ.get("CI_COMMIT_SHA", ""),
                      help="Git commit SHA (default: $CI_COMMIT_SHA)")
    ci_p.add_argument("--isaac-sim-branch",
                      default=(os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
                               or os.environ.get("CI_COMMIT_REF_NAME", "")),
                      help="Isaac Sim branch name "
                           "(default: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME if set, else $CI_COMMIT_REF_NAME)")

    # ── fetch-gitlab ────────────────────────────────────────────────────────────
    gl_p = subparsers.add_parser(
        "fetch-gitlab",
        help="Fetch historical IsaacLab test data from GitLab pipeline artifacts",
        description="Pull historical GitLab pipeline data into the local cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gl_p.add_argument(
        "--project", default="omniverse/isaac/omni_isaac_sim",
        help="GitLab project path (default: omniverse/isaac/omni_isaac_sim)")
    gl_p.add_argument("--data-dir", default="_dashboard_cache",
                      help="Cache directory (default: _dashboard_cache)")
    gl_p.add_argument("--isaac-sim-branch", required=True,
                      help="Isaac Sim branch to query")
    gl_p.add_argument("--isaac-lab-branch", default="develop",
                      help="IsaacLab branch name, stored in run records (default: develop)")
    gl_p.add_argument(
        "--gitlab-url", default="https://gitlab-master.nvidia.com",
        help="GitLab instance base URL (default: https://gitlab-master.nvidia.com)")
    _gl_token, _gl_token_source = _resolve_token(_GITLAB_TOKEN_VARS)
    gl_p.add_argument(
        "--token", default=_gl_token,
        help=(
            "GitLab personal access token. "
            "Resolved automatically from environment variables in priority order: "
            + ", ".join(f"${v}" for v in _GITLAB_TOKEN_VARS) + ". "
            + (f"Currently using ${_gl_token_source}."
               if _gl_token_source else
               "No token found in environment — set one of the above variables.")
        ))
    gl_p.add_argument(
        "--max-runs", type=int, default=50,
        help="Max pipelines with isaaclab data to collect (default: 50)")
    gl_p.add_argument(
        "--force-refetch", action="store_true",
        help="Re-download artifacts for runs already in the cache")
    gl_p.add_argument(
        "--verbose", action="store_true",
        help="Print per-pipeline progress details")

    # ── fetch-github ────────────────────────────────────────────────────────────
    gh_p = subparsers.add_parser(
        "fetch-github",
        help="Fetch IsaacLab GitHub Actions build/compat workflow data",
        description="Pull IsaacLab build and compat workflow data from GitHub into the local cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gh_p.add_argument("--data-dir", default="_dashboard_cache",
                      help="Cache directory (default: _dashboard_cache)")
    _gh_token, _gh_token_source = _resolve_token(_GITHUB_TOKEN_VARS)
    gh_p.add_argument(
        "--github-token", default=_gh_token,
        help=(
            "GitHub personal access token. "
            "Resolved automatically from environment variables in priority order: "
            + ", ".join(f"${v}" for v in _GITHUB_TOKEN_VARS) + ". "
            + (f"Currently using ${_gh_token_source}."
               if _gh_token_source else
               "No token found in environment — without a token rate-limit is 60 req/hr.")
        ))
    gh_p.add_argument(
        "--github-max-runs", type=int, default=50,
        help="Max new runs to fetch per workflow (default: 50)")
    gh_p.add_argument(
        "--force-refetch", action="store_true",
        help="Re-download artifacts for runs already in the cache")
    gh_p.add_argument(
        "--verbose", action="store_true",
        help="Print per-workflow progress details")

    # ── generate ────────────────────────────────────────────────────────────────
    gen_p = subparsers.add_parser(
        "generate",
        help="Rebuild dashboard HTML from the local cache without any network calls",
        description="Rebuild data.js and HTML from the local cache. No network calls.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gen_p.add_argument("--data-dir", default="_dashboard_cache",
                       help="Cache directory (default: _dashboard_cache)")
    gen_p.add_argument("--output-dir", default=None,
                       help="Output directory (default: <data-dir>/output)")

    args = parser.parse_args()

    if args.command == "ci":
        missing = [flag for flag, val in [
            ("--pipeline-id", args.pipeline_id),
            ("--pipeline-url", args.pipeline_url),
            ("--commit-sha", args.commit_sha),
            ("--isaac-sim-branch", args.isaac_sim_branch),
        ] if not val]
        if missing:
            parser.error(
                f"ci: missing required values (pass via flag or set the corresponding "
                f"CI environment variable): {', '.join(missing)}"
            )
        if not args.output_dir:
            args.output_dir = str(Path(args.data_dir) / "output")
        run_ci_mode(args)
    elif args.command == "fetch-gitlab":
        run_fetch_mode(args)
    elif args.command == "fetch-github":
        run_github_fetch_only(args)
    elif args.command == "generate":
        if not args.output_dir:
            args.output_dir = str(Path(args.data_dir) / "output")
        run_generate_only_mode(args)


if __name__ == "__main__":
    main()
