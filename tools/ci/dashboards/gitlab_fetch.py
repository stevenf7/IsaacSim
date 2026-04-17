# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""GitLab fetch helpers for the CI dashboard.

Provides functions to download pipeline / job data from a GitLab instance
and the ``run_fetch_mode`` entry-point that implements the *fetch-gitlab*
subcommand.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from .parsing import (
    ISAACLAB_JOB_NAMES,
    ARTIFACT_PATH,
    _CONCLUSION_MAP,
    MAX_CONSECUTIVE_MISSES,
    parse_junit_xml,
    merge_summaries,
    parse_test_report_api,
)
from .clients import GitLabClient, _resolve_token, _GITLAB_TOKEN_VARS
from .cache import load_runs_index, save_runs_index, cached_pipeline_ids, _branch_subdir, _make_section
from .output import _generate_from_cache


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


def _find_all_test_jobs(
    client: GitLabClient,
    project_enc: str,
    pipeline_id: int,
    exclude_patterns: list[str],
    include_patterns: list[str] | None = None,
) -> list[dict]:
    """Return all finished test jobs whose names pass the include/exclude filters.

    Used in ``sections`` fetch mode to build one dashboard section per test job.

    Args:
        exclude_patterns: Substrings; a job is excluded if any pattern appears in
                          its name (case-sensitive).
        include_patterns: Substrings; when non-empty, a job is only kept if at
                          least one pattern appears in its name. When empty or
                          None, all non-excluded jobs are kept.
    """
    try:
        jobs = list(client.get_paginated(
            f"/projects/{project_enc}/pipelines/{pipeline_id}/jobs"
        ))
    except Exception as exc:
        print(f"    could not list jobs for pipeline {pipeline_id}: {exc}", file=sys.stderr)
        return []

    return [
        j for j in jobs
        if j.get("status") in ("success", "failed")
        and not any(pat in j.get("name", "") for pat in exclude_patterns)
        and (not include_patterns or any(pat in j.get("name", "") for pat in include_patterns))
    ]


def _download_junit_xml(client: GitLabClient, project_enc: str, job_id: int) -> bytes | None:
    """Download the JUnit XML artifact bytes from a job, or return None."""
    try:
        artifact_url = f"/projects/{project_enc}/jobs/{job_id}/artifacts/{ARTIFACT_PATH}"
        resp = client.get(artifact_url)
        return resp.content
    except Exception as exc:
        print(f"    artifact download failed for job {job_id}: {exc}", file=sys.stderr)
        return None


def run_fetch_mode(args: argparse.Namespace, config: dict | None = None) -> None:
    """Fetch historical pipeline data from GitLab and build the dashboard.

    When *config* contains ``ingestion.fetch_mode: sections``, all non-excluded
    test jobs in each pipeline are fetched and stored as separate sections.
    Otherwise (the default ``single_job`` mode) only the first matching
    IsaacLab job is fetched, preserving the existing behavior.
    """
    cfg = config or {}
    ingestion_cfg = cfg.get("ingestion", {})
    fetch_mode = ingestion_cfg.get("fetch_mode", "single_job")
    exclude_patterns: list[str] = ingestion_cfg.get("exclude_job_patterns", [])
    include_patterns: list[str] = ingestion_cfg.get("include_job_patterns", [])
    namespace_prefix = cfg.get("namespace_prefix", "isaaclab")

    client = GitLabClient(args.gitlab_url, token=args.token, verbose=args.verbose)
    project_enc = urllib.parse.quote(args.project, safe="")

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    branch_dir = _branch_subdir(args.data_dir, args.isaac_sim_branch, prefix=namespace_prefix)
    branch_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = branch_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    runs_index = load_runs_index(branch_dir)
    already_cached = cached_pipeline_ids(runs_index)

    print(
        f"Fetching pipelines for {args.project} ref={args.isaac_sim_branch} "
        f"mode={fetch_mode} ({len(already_cached)} already cached)…"
    )

    found = 0
    checked = 0
    new_records = []

    # If --extra-pipeline-id is set, fetch that pipeline unconditionally first
    # (it may still be running, so it would be excluded by scope=finished).
    extra_pipelines: list[dict] = []
    extra_pid_raw = getattr(args, "extra_pipeline_id", None)
    if extra_pid_raw:
        try:
            extra_pid = int(extra_pid_raw)
            if extra_pid not in already_cached or args.force_refetch:
                p = client.get_json(f"/projects/{project_enc}/pipelines/{extra_pid}")
                extra_pipelines.append(p)
                print(f"  Including forced pipeline {extra_pid}", file=sys.stderr)
        except Exception as exc:
            print(f"  Warning: could not fetch forced pipeline {extra_pid_raw}: {exc}", file=sys.stderr)

    pipeline_params = {"ref": args.isaac_sim_branch, "scope": "finished", "order_by": "id", "sort": "desc"}

    def _pipeline_iter():
        yield from extra_pipelines
        yield from client.get_paginated(
            f"/projects/{project_enc}/pipelines",
            params=pipeline_params,
            max_pages=50,
        )

    consecutive_misses = 0
    for pipeline in _pipeline_iter():
        if found >= args.max_runs:
            break

        pipeline_id = pipeline["id"]
        checked += 1

        # Skip already-cached runs unless --force-refetch
        if pipeline_id in already_cached and not args.force_refetch:
            if args.verbose:
                print(f"  [{checked}] Pipeline {pipeline_id}: already cached, skipping", file=sys.stderr)
            found += 1  # count it toward max_runs so we stop at the right depth
            consecutive_misses = 0
            continue

        label = f"[{checked}] Pipeline {pipeline_id}"
        duration = _get_pipeline_duration(client, project_enc, pipeline_id)
        conclusion = _CONCLUSION_MAP.get(pipeline.get("status", ""), "unknown")
        per_run_path = tests_dir / f"{pipeline_id}.json"

        if fetch_mode == "sections":
            # ── Sections mode: one section per test job ───────────────────────
            jobs = _find_all_test_jobs(client, project_enc, pipeline_id, exclude_patterns, include_patterns)
            if not jobs:
                consecutive_misses += 1
                if args.verbose:
                    print(f"  {label}: no test jobs found, skipping", file=sys.stderr)
                if consecutive_misses >= MAX_CONSECUTIVE_MISSES:
                    print(f"  Stopping: {MAX_CONSECUTIVE_MISSES} consecutive pipelines with no matching jobs",
                          file=sys.stderr)
                    break
                continue

            print(f"  {label}: found {len(jobs)} test job(s)", file=sys.stderr)
            sections: dict[str, dict] = {}
            any_data = False

            # Fetch the pipeline-level test report (aggregates all jobs' results)
            # and split by suite name (which matches the job name in GitLab).
            pipeline_report = None
            try:
                pipeline_report = client.get_json(
                    f"/projects/{project_enc}/pipelines/{pipeline_id}/test_report"
                )
            except Exception as exc:
                print(f"    ⚠  pipeline test-report API failed: {exc}", file=sys.stderr)

            # Build a lookup from job name → job metadata
            job_lookup = {j["name"]: j for j in jobs}

            if pipeline_report and pipeline_report.get("test_suites"):
                # Group suites: exact job name match first, then try prefix match
                unmatched_suites = []
                for suite in pipeline_report["test_suites"]:
                    suite_name = suite.get("name", "")
                    if suite_name in job_lookup:
                        job = job_lookup[suite_name]
                        job_summary, job_suites = parse_test_report_api({"test_suites": [suite]})
                        if job_summary.get("total", 0) > 0:
                            any_data = True
                            print(f"    ✓ [{suite_name}] "
                                  f"{job_summary['passed']}/{job_summary['total']} passed", file=sys.stderr)
                        sections[suite_name] = _make_section(
                            job.get("id"), job.get("web_url", ""), job_summary, job_suites
                        )
                    else:
                        unmatched_suites.append(suite)

                # For suites that don't exactly match a job name, try to find the
                # job whose name is a prefix of the suite name (e.g. job "test-foo"
                # producing suite "test-foo::bar").  Fall back to keeping the suite
                # under its own name if no job matches.
                for suite in unmatched_suites:
                    suite_name = suite.get("name", "")
                    matched_job = None
                    for jname, jmeta in job_lookup.items():
                        if suite_name.startswith(jname):
                            matched_job = jmeta
                            break
                    if matched_job is None:
                        if args.verbose:
                            print(f"    ⚠  [{suite_name}] no matching job, skipping", file=sys.stderr)
                        continue
                    job_summary, job_suites = parse_test_report_api({"test_suites": [suite]})
                    section_key = matched_job["name"]
                    if section_key in sections:
                        # Merge into existing section, prefixing suite keys to avoid
                        # collisions when multiple suites share classnames.
                        existing = sections[section_key]
                        for sk, sv in job_suites.items():
                            unique_key = f"{suite_name}/{sk}" if sk in existing["suites"] else sk
                            existing["suites"][unique_key] = sv
                        if job_summary.get("total", 0) > 0:
                            existing["summary"] = merge_summaries([existing["summary"], job_summary])
                    else:
                        if job_summary.get("total", 0) > 0:
                            any_data = True
                        sections[section_key] = _make_section(
                            matched_job.get("id"), matched_job.get("web_url", ""),
                            job_summary, job_suites
                        )
            else:
                # Fallback: no pipeline-level report available
                if args.verbose:
                    print(f"    ⚠  no pipeline test report available", file=sys.stderr)

            data_fetched = any_data
            if data_fetched:
                all_summaries = [s["summary"] for s in sections.values() if s["summary"]]
                if all_summaries:
                    merged = merge_summaries(all_summaries)
                    failed_count = merged["failed"] + merged["errored"] + merged.get("timed_out", 0)
                    conclusion = "success" if failed_count == 0 else "failure"

            per_run_path.write_text(json.dumps({"sections": sections}, separators=(",", ":")))

            new_records.append({
                "pipeline_id": pipeline_id,
                "commit_sha": pipeline.get("sha", ""),
                "isaac_sim_branch": pipeline.get("ref", args.isaac_sim_branch),
                "isaac_lab_branch": getattr(args, "isaac_lab_branch", ""),
                "conclusion": conclusion,
                "created_at": pipeline.get("created_at", ""),
                "pipeline_url": pipeline.get("web_url", ""),
                "job_url": "",  # multiple jobs — no single job URL
                "job_id": None,
                "duration_seconds": duration,
                "data_file": f"tests/{pipeline_id}.json",
                "data_fetched": data_fetched,
            })

        else:
            # ── Single-job mode (default, backward-compatible) ─────────────────
            job = _find_isaaclab_job(client, project_enc, pipeline_id)
            if job is None:
                consecutive_misses += 1
                if args.verbose:
                    print(f"  {label}: no isaaclab job, skipping", file=sys.stderr)
                if consecutive_misses >= MAX_CONSECUTIVE_MISSES:
                    print(f"  Stopping: {MAX_CONSECUTIVE_MISSES} consecutive pipelines with no isaaclab job",
                          file=sys.stderr)
                    break
                continue

            print(f"  {label}: found job '{job['name']}' ({job['status']})", file=sys.stderr)

            # Try 1: download the raw JUnit XML artifact
            xml_bytes = _download_junit_xml(client, project_enc, job["id"])
            data_fetched = False
            summary: dict = {}
            sections: dict = {}

            if xml_bytes:
                try:
                    summary, sections = parse_junit_xml(xml_bytes)
                    data_fetched = True
                    print(f"    ✓ artifact  {summary['passed']}/{summary['total']} passed "
                          f"({summary['pass_rate']*100:.1f}%)", file=sys.stderr)
                except Exception as exc:
                    print(f"    ⚠  XML parse failed: {exc}", file=sys.stderr)

            # Try 2: fall back to GitLab's stored test-report (survives artifact expiry).
            # parse_test_report_api returns flat classname-grouped suites; wrap them in
            # a single section named after the job so the cache shape stays consistent.
            if not data_fetched:
                if xml_bytes is None:
                    print(f"    ⚠  artifact expired — trying test-report API…", file=sys.stderr)
                try:
                    report = client.get_json(
                        f"/projects/{project_enc}/jobs/{job['id']}/test_report"
                    )
                    summary, flat_suites = parse_test_report_api(report)
                    if summary.get("total", 0) > 0:
                        sections = {
                            job.get("name", "tests"): _make_section(
                                job.get("id"), job.get("web_url", ""), summary, flat_suites
                            )
                        }
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

            per_run_path.write_text(json.dumps({"sections": sections},
                                                separators=(",", ":")))

            # Determine isaac_lab_branch: prefer value stored in the pipeline's variables if
            # available; fall back to the CLI arg.  (GitLab doesn't expose trigger variables
            # on the pipeline list endpoint, so we just use the CLI arg here.)
            new_records.append({
                "pipeline_id": pipeline_id,
                "commit_sha": pipeline.get("sha", ""),
                "isaac_sim_branch": pipeline.get("ref", args.isaac_sim_branch),
                "isaac_lab_branch": getattr(args, "isaac_lab_branch", ""),
                "conclusion": conclusion,
                "created_at": pipeline.get("created_at", ""),
                "pipeline_url": pipeline.get("web_url", ""),
                "job_url": job.get("web_url", ""),
                "job_id": job.get("id"),
                "duration_seconds": duration,
                "data_file": f"tests/{pipeline_id}.json",
                "data_fetched": data_fetched,
            })

        found += 1
        consecutive_misses = 0

    if not new_records and not already_cached:
        mode_hint = "sections" if fetch_mode == "sections" else "isaaclab"
        print(f"No {mode_hint} pipelines found for branch '{args.isaac_sim_branch}'. "
              f"This is normal for new branches with no test history yet.",
              file=sys.stderr)
        return

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
