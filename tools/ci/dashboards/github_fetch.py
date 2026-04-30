# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""GitHub data-fetching helpers for the CI dashboard.

This module contains all ``_gh_*`` helper functions, the per-run processors,
and the top-level :func:`fetch_github_data` entry point that orchestrates
fetching workflow runs from GitHub and caching them locally.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import sys
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .clients import GitHubClient, GITHUB_BASE_URL
from .parsing import (
    merge_section,
    merge_summaries,
    normalize_test_data,
    parse_junit_xml,
    SCHEMA_VERSION,
)

# ── Constants ──────────────────────────────────────────────────────────────────

COMPAT_VERSIONS = ["4.5.0", "5.0.0"]


# ── GitHub artifact helpers ────────────────────────────────────────────────────

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


# ── GitHub cache helpers ───────────────────────────────────────────────────────

def _gh_load_index(gh_dir: Path, workflow: str) -> dict | None:
    path = gh_dir / f"runs_{workflow}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def _gh_save_index(gh_dir: Path, workflow: str, data: dict) -> None:
    gh_dir.mkdir(parents=True, exist_ok=True)
    (gh_dir / f"runs_{workflow}.json").write_text(json.dumps(data, indent=2))


def _gh_load_test_data(gh_dir: Path, subdir: str, run_id: int) -> dict | None:
    """Load a per-run test_data JSON, retro-fitting the timeout-suite collapse.

    Cached files written before parse_junit_xml learned to collapse
    ``timeout_<X>`` testsuites still have those entries as standalone rows.
    Normalizing here lets the dashboard show one merged row per test
    regardless of when the cache entry was written. New entries are
    already-collapsed, so this is a no-op for them.
    """
    path = gh_dir / subdir / f"{run_id}.json"
    if not path.exists():
        return None
    return normalize_test_data(json.loads(path.read_text()))


def _gh_save_test_data(gh_dir: Path, subdir: str, run_id: int, data: dict) -> None:
    out_dir = gh_dir / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{run_id}.json").write_text(json.dumps(data, indent=2))


def _gh_merge_run_indexes(new_runs: list[dict], existing_runs_dict: dict) -> list[dict]:
    new_ids = {r["run_id"] for r in new_runs}
    merged = new_runs + [r for r in existing_runs_dict.values() if r["run_id"] not in new_ids]
    merged.sort(key=lambda r: r["run_id"], reverse=True)
    return merged


# ── GitHub per-run processors ─────────────────────────────────────────────────

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
                summary, sections = parse_junit_xml(xml_bytes)
                # Save under the canonical "sections" key (matches what
                # parse_junit_xml returns and what the dashboard JS reads).
                # Older caches used "suites" here for the same dict; the
                # load-time normalize_test_data hoists those for backward
                # compat.
                _gh_save_test_data(gh_dir, "tests_build", run_id, {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "summary": summary,
                    "sections": sections,
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

    # Re-fetch can fail (artifact gone, malformed XML) on a run we already
    # have good data for — keep the existing on-disk file in that case rather
    # than marking the run as missing.
    if not data_fetched and already_cached:
        data_fetched = True
        print(
            f"    ↩  Re-fetch failed for run {run_id}; keeping prior cached data",
            file=sys.stderr,
        )
    elif not data_fetched and artifact_id is None:
        print(
            f"    ⚠  No combined-test-results artifact for build run {run_id}; "
            "data missing",
            file=sys.stderr,
        )

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
        # Per-version artifacts (``isaaclab-tasks-compat-results-X`` and
        # ``general-tests-compat-results-X``) are the canonical source. When
        # they are present we synthesize the aggregate ourselves and skip the
        # ``daily-compat-*-combined-test-results`` artifact entirely — its
        # producer (the IsaacLab ``combine-compat-results`` job) is
        # consistently failing and uploading malformed XML, and the data it
        # would carry is just a re-aggregation of what we already have.
        versions_data: dict = {}
        expired_artifacts: list[str] = []
        combined_failure: str | None = None
        for version in COMPAT_VERSIONS:
            version_xml_list = []
            for art_name in [f"isaaclab-tasks-compat-results-{version}", f"general-tests-compat-results-{version}"]:
                art = artifacts_by_name.get(art_name)
                if not art:
                    continue
                zip_bytes = _gh_download_artifact_zip(client, art["id"])
                if zip_bytes is None:
                    expired_artifacts.append(art_name)
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

        aggregate_summary, aggregate_suites = None, {}
        if versions_data:
            agg_suites: dict = {}
            agg_summaries: list = []
            for v_data in versions_data.values():
                agg_summaries.append(v_data["summary"])
                # When two versions report the same canonical section (e.g.
                # one ran normally while another timed out and parse_junit_xml
                # collapsed its ``timeout_<X>`` synthetic suite into ``X``),
                # combine their per-case rows and re-roll the worst_status so
                # the aggregate reflects both versions' contributions instead
                # of the last-write-wins behaviour of dict.update.
                for sec_name, sec_data in (v_data.get("suites") or {}).items():
                    if sec_name in agg_suites:
                        merge_section(agg_suites[sec_name], sec_data)
                    else:
                        agg_suites[sec_name] = copy.deepcopy(sec_data)
            aggregate_summary = merge_summaries(agg_summaries)
            aggregate_suites = agg_suites
        else:
            # Per-version data is gone — the malformed combined artifact is
            # the only remaining source for an aggregate. Recovery in
            # parse_junit_xml lets us salvage usable suites from it.
            combined_art = artifacts_by_name.get(f"daily-compat-{run_id}-combined-test-results")
            if combined_art:
                zip_bytes = _gh_download_artifact_zip(client, combined_art["id"])
                if zip_bytes is None:
                    combined_failure = "combined artifact expired"
                    print(f"    ⚠  daily-compat-{run_id}-combined-test-results expired", file=sys.stderr)
                else:
                    try:
                        xml_bytes = _gh_extract_xml_from_zip(zip_bytes, "combined-compat-results.xml")
                        aggregate_summary, aggregate_suites = parse_junit_xml(xml_bytes)
                    except Exception as e:
                        combined_failure = f"combined artifact parse failed: {e}"
                        print(f"    ⚠  Combined compat XML failed: {e}", file=sys.stderr)
            else:
                combined_failure = "no combined artifact"

        data_fetched = bool(versions_data or aggregate_summary)
        if data_fetched:
            # Don't downgrade: if a prior fetch captured per-version data
            # while those artifacts were still alive, but this fetch only
            # got the combined-recovery aggregate, keep the richer cached
            # entry rather than overwriting it.
            if not versions_data and already_cached:
                cached = _gh_load_test_data(gh_dir, "tests_compat", run_id) or {}
                cached_versions = cached.get("versions") or {}
                if cached_versions:
                    print(
                        f"    ↩  Re-fetch produced only aggregate; keeping cached "
                        f"data with {len(cached_versions)} version(s) for run {run_id}",
                        file=sys.stderr,
                    )
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
                        "data_fetched": True,
                    }
            test_data = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "versions": versions_data,
            }
            if aggregate_summary:
                test_data["aggregate"] = {"summary": aggregate_summary, "suites": aggregate_suites}
            _gh_save_test_data(gh_dir, "tests_compat", run_id, test_data)
            if verbose:
                agg = test_data.get("aggregate", {}).get("summary", {})
                print(f"    ✅ Compat parsed: {agg.get('passed','?')}/{agg.get('total','?')} passed", file=sys.stderr)
        elif already_cached:
            # Both fetch sources failed but we have known-good data on disk
            # from a prior successful fetch; preserve it rather than marking
            # the run as missing.
            data_fetched = True
            print(
                f"    ↩  Re-fetch failed for run {run_id}; keeping prior cached data",
                file=sys.stderr,
            )
        else:
            reasons = []
            if expired_artifacts:
                reasons.append(f"{len(expired_artifacts)} per-version artifact(s) expired")
            if combined_failure:
                reasons.append(combined_failure)
            if not reasons:
                reasons.append("no compat artifacts found")
            print(
                f"    ⚠  No data fetched for compat run {run_id}: {'; '.join(reasons)}",
                file=sys.stderr,
            )

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


# ── Workflow-level fetch orchestration ─────────────────────────────────────────

def _fetch_github_workflow_runs(
    client: GitHubClient, workflow_id: int, max_runs: int, max_cached_id: int,
    force_refetch: bool, process_fn: Callable, gh_dir: Path, verbose: bool,
) -> list[dict]:
    runs_data = []
    url = f"{client.base_url}/actions/workflows/{workflow_id}/runs"
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


def fetch_github_data(args: argparse.Namespace, gh_dir: str | Path,
                      config: dict | None = None) -> tuple[dict, dict]:
    """Fetch/update GitHub build+compat data and return (build_index, compat_index).

    Data is cached under *gh_dir* using the same structure as IsaacLab's
    ``tools/dashboard/data/`` directory.  Only new runs (beyond what is already
    cached) are fetched unless ``--force-refetch`` is set.

    When *config* is provided the ``ingestion.github.repo`` and
    ``ingestion.github.workflows`` values from it are used instead of the
    built-in IsaacLab defaults.  This allows reusing the same function for
    different GitHub repositories (e.g. ``isaac-sim/IsaacSim``).
    """
    gh_cfg = (config or {}).get("ingestion", {}).get("github", {})
    repo = gh_cfg.get("repo") or "isaac-sim/IsaacLab"
    base_url = f"https://api.github.com/repos/{repo}"
    client = GitHubClient(token=args.github_token or None, verbose=args.verbose,
                          base_url=base_url)
    gh_dir = Path(gh_dir)
    force = args.force_refetch
    max_runs = gh_cfg.get("max_runs", args.github_max_runs)

    # Workflow definitions: from config or fall back to IsaacLab defaults.
    workflow_defs = gh_cfg.get("workflows") or [
        {"name": "build",  "path": ".github/workflows/build.yml"},
        {"name": "compat", "path": ".github/workflows/daily-compatibility.yml"},
    ]

    # Map workflow name → processor function (extend as needed)
    _PROCESSORS: dict[str, Callable] = {
        "build":  _process_build_run_gh,
        "compat": _process_compat_run_gh,
    }

    indexes = {}
    for wf_def in workflow_defs:
        wf_name = wf_def.get("name", "")
        wf_path = wf_def.get("path", "")
        if not wf_name or not wf_path:
            print(f"Warning: skipping workflow definition with missing name/path: {wf_def}",
                  file=sys.stderr)
            continue
        process_fn = _PROCESSORS.get(wf_name, _process_build_run_gh)
        idx = _fetch_and_save_github_workflow(
            client, wf_name, wf_path,
            process_fn, max_runs, force, gh_dir, args.verbose,
        )
        indexes[wf_name] = idx

    # Return the two canonical indexes for backward compatibility
    return indexes.get("build", {}), indexes.get("compat", {})
