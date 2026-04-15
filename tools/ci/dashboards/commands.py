# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Subcommand handlers for the CI dashboard CLI (ci, generate, fetch-github)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config
from .parsing import parse_junit_xml, SCHEMA_VERSION
from .cache import load_runs_index, save_runs_index, _branch_subdir, _make_section, _collect_all_branch_runs
from .output import _generate_from_cache
from .clients import GitHubClient, _resolve_token, _GITHUB_TOKEN_VARS
from .github_fetch import fetch_github_data


def run_github_fetch_only(args: argparse.Namespace, config: dict | None = None) -> None:
    """Fetch GitHub workflow data into the local cache.

    The *config* dict drives which repository and workflows are fetched.
    When config specifies ``ingestion.github.repo``, data is stored in
    ``github_isaacsim/`` if the repo differs from the IsaacLab default, or
    ``github/`` for the canonical IsaacLab repository.
    """
    cfg = config or {}
    gh_cfg = cfg.get("ingestion", {}).get("github", {})
    repo = gh_cfg.get("repo") or "isaac-sim/IsaacLab"
    # Use a dedicated subdirectory when fetching a non-IsaacLab repo so that
    # IsaacLab and IsaacSim GitHub caches never collide in the same data_dir.
    if repo == "isaac-sim/IsaacLab":
        subdir = "github"
    else:
        subdir = "github_isaacsim"
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    workflows = gh_cfg.get("workflows", [])
    if not workflows:
        print(f"Note: no GitHub workflows configured for repo '{repo}' — skipping GitHub fetch.",
              file=sys.stderr)
        return
    fetch_github_data(args, data_dir / subdir, config=cfg)


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


def run_ci_mode(args: argparse.Namespace, config: dict | None = None) -> None:
    """Process the current pipeline's JUnit XML and update the cache."""
    namespace_prefix = (config or {}).get("namespace_prefix", "isaaclab")
    pipeline_id = int(args.pipeline_id)
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    branch_dir = _branch_subdir(args.data_dir, args.isaac_sim_branch, prefix=namespace_prefix)
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

    # Capture CI job identity for the sections format and drilldown links.
    job_name = os.environ.get("CI_JOB_NAME", "test")
    job_id_str = os.environ.get("CI_JOB_ID", "")
    job_id: int | None = int(job_id_str) if job_id_str.isdigit() else None
    job_url = os.environ.get("CI_JOB_URL", args.pipeline_url)

    # Write per-run JSON in the sections format.  The JavaScript getSections()
    # helper also handles the old flat {"summary": ..., "suites": ...} format
    # for backward compatibility with pre-existing cache entries.
    per_run_path = branch_dir / "tests" / f"{pipeline_id}.json"
    per_run_path.write_text(json.dumps(
        {"sections": {job_name: _make_section(job_id, job_url, summary, suites)}},
        separators=(",", ":")))

    # Report regressions: tests that were passing in the previous run but are failing now.
    if data_fetched and suites:
        prev_runs = [r for r in runs_index["runs"] if r.get("data_fetched")]
        if prev_runs:
            prev_run_file = branch_dir / prev_runs[0]["data_file"]
            try:
                prev_data = json.loads(prev_run_file.read_text())
                # Support both old flat format and new sections format in the cache.
                prev_suites = prev_data.get("suites") or {}
                if not prev_suites:
                    for sec in prev_data.get("sections", {}).values():
                        prev_suites.update(sec.get("suites", {}))
                _report_newly_failing_tests(suites, prev_suites)
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
        "job_url": job_url,
        "job_id": job_id,
        "data_file": f"tests/{pipeline_id}.json",
        "data_fetched": data_fetched,
        "is_ci_run": True,
    })
    runs_index["last_updated"] = now
    save_runs_index(branch_dir, runs_index)
    print(f"Cache updated: {len(runs_index['runs'])} total run(s) in branch '{args.isaac_sim_branch}'")

    cfg = load_config(args.config)
    prefix = (cfg or {}).get("namespace_prefix", "isaaclab")
    _generate_from_cache(data_dir, args.output_dir, prefix=prefix, config=cfg)


def run_generate_only_mode(args: argparse.Namespace, config: dict | None = None) -> None:
    """Rebuild data.js + HTML from the local cache without any network calls."""
    cfg = config or {}
    prefix = cfg.get("namespace_prefix", "isaaclab")
    branch_runs = _collect_all_branch_runs(args.data_dir, prefix=prefix)
    if not branch_runs:
        print("Warning: no branch subdirectories with runs.json found in cache. "
              "Dashboard will be empty.", file=sys.stderr)
    else:
        for wk, (_, ri) in branch_runs.items():
            print(f"Loaded {len(ri['runs'])} run(s) from cache for '{wk}'.")
    _generate_from_cache(args.data_dir, args.output_dir, prefix=prefix, config=cfg)
