# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Output generation for the CI dashboard — data.js emission and HTML copying."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from .cache import _collect_all_branch_runs, _add_branch_placeholders
from .github_fetch import _gh_load_index, _gh_load_test_data


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


_UNUSED_CASE_FIELDS = {"classname", "system_output", "stack_trace"}


def _strip_case_fields(dashboard_data: dict) -> None:
    """Remove fields from test cases that the dashboard JS never reads.

    Mutates *dashboard_data* in place.  Walks every suite→cases list across
    all workflow keys and drops keys in ``_UNUSED_CASE_FIELDS``.
    """
    def _strip_suites(suites: dict) -> None:
        for suite_data in suites.values():
            for case in suite_data.get("cases", []):
                for field in _UNUSED_CASE_FIELDS:
                    case.pop(field, None)

    for key, val in dashboard_data.items():
        if not isinstance(val, dict) or "test_data" not in val:
            continue
        for entry in val["test_data"].values():
            # Single-job format: {summary, suites}
            if "suites" in entry:
                _strip_suites(entry["suites"])
            # Sections format: {sections: {name: {suites: ...}}}
            if "sections" in entry:
                for sec in entry["sections"].values():
                    _strip_suites(sec.get("suites", {}))
            # Compat format: {aggregate: {suites}, versions: {v: {suites}}}
            if "aggregate" in entry:
                _strip_suites(entry["aggregate"].get("suites", {}))
            if "versions" in entry:
                for ver in entry["versions"].values():
                    _strip_suites(ver.get("suites", {}))


def generate_output(
    branch_runs: dict,
    output_dir: str | Path,
    github_data_dir: str | Path | None = None,
    github_extra_dir: str | Path | None = None,
    dashboard_meta: dict | None = None,
) -> None:
    """Write data/data.js and copy index.html into output_dir.

    Args:
        branch_runs: dict mapping workflow key (e.g. "isaaclab_develop") to
                     (branch_dir: Path, runs_index: dict) tuples.
        output_dir: directory to write dashboard files into.
        github_data_dir: optional path to the primary GitHub cache directory
                         (e.g. ``<cache_dir>/github``).
        github_extra_dir: optional path to a secondary GitHub cache directory
                          (e.g. ``<cache_dir>/github_isaacsim``).
        dashboard_meta: optional metadata dict (``gitlab_url``, ``gitlab_project``)
                        embedded as ``window.DASHBOARD_META`` in data.js and used by
                        the dashboard for the branch-card click URL.
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
        runs_with_data = []
        for run in runs_index["runs"]:
            pid = str(run["pipeline_id"])
            per_run_file = bdir / run["data_file"]
            if per_run_file.exists():
                try:
                    test_data[pid] = json.loads(per_run_file.read_text())
                    runs_with_data.append(run)
                except json.JSONDecodeError as exc:
                    print(f"Warning: skipping corrupt per-run JSON {per_run_file}: {exc}", file=sys.stderr)
            elif run.get("data_fetched"):
                # Run claims data was fetched but file is missing — include the run
                # metadata so timeline shows the pipeline, but without test data.
                runs_with_data.append(run)
        dashboard_data[workflow_key] = {"runs": runs_with_data, "test_data": test_data}
        total_runs += len(runs_index["runs"])

    # Merge GitHub build/compat data from the primary cache directory
    if github_data_dir:
        try:
            github_data = _load_github_from_cache(github_data_dir)
            dashboard_data.update(github_data)
        except Exception as exc:
            print(f"Warning: could not load GitHub cache from {github_data_dir}: {exc}", file=sys.stderr)

    # Merge any additional GitHub data (e.g. from a secondary repo like IsaacSim)
    if github_extra_dir:
        try:
            extra_data = _load_github_from_cache(github_extra_dir)
            dashboard_data.update(extra_data)
        except Exception as exc:
            print(f"Warning: could not load extra GitHub cache from {github_extra_dir}: {exc}", file=sys.stderr)

    # Strip fields from test cases that the dashboard JS never reads.
    # This keeps the on-disk cache complete while shrinking data.js significantly
    # (classname alone accounts for ~45% of all case data).
    _strip_case_fields(dashboard_data)

    # Build the data.js file: DASHBOARD_META then DASHBOARD_DATA
    meta = dashboard_meta or {}
    meta_js = "window.DASHBOARD_META = " + json.dumps(meta, separators=(",", ":")) + ";\n"
    data_js = "window.DASHBOARD_DATA = " + json.dumps(dashboard_data, separators=(",", ":")) + ";\n"
    data_js_path = data_out_dir / "data.js"
    data_js_path.write_text(meta_js + data_js)

    _non_meta_keys = {"generated_at", "build", "compat"}
    branch_summary = ", ".join(
        f"{k}: {len(v['runs'])}" for k, v in dashboard_data.items()
        if k not in _non_meta_keys
    )
    print(f"Generated {data_js_path} ({total_runs} GitLab run(s) — {branch_summary})")

    html_src = Path(__file__).resolve().parent / "index.html"
    html_dst = output_dir / "dashboard.html"
    if html_src.exists():
        shutil.copy2(html_src, html_dst)
        print(f"Copied dashboard HTML to {html_dst}")
    else:
        print(f"Error: dashboard HTML not found at {html_src}", file=sys.stderr)
        sys.exit(1)

    print(f"Dashboard output ready in {output_dir}/")


def _generate_from_cache(data_dir: str | Path, output_dir: str | Path,
                         prefix: str = "isaaclab",
                         config: dict | None = None) -> None:
    """Collect all branch runs from *data_dir* and generate dashboard output.

    Args:
        data_dir: Root cache directory containing branch subdirs and github/.
        output_dir: Destination for data.js and the copied dashboard HTML.
        prefix: Workflow key prefix; controls which subdirs are scanned and
                how they appear in the dashboard dropdown (e.g. ``"isaacsim"``).
        config: Loaded dashboard config dict used to populate DASHBOARD_META.
    """
    cfg = config or {}
    gh_dir = Path(data_dir) / "github"
    gh_extra_dir = Path(data_dir) / "github_isaacsim"
    branch_runs = _collect_all_branch_runs(data_dir, prefix=prefix)
    branch_env_var = (
        "ISAACSIM_CI_REPORT_BRANCHES" if prefix == "isaacsim"
        else "ISAAC_LAB_CI_REPORT_BRANCHES"
    )
    extra_branches = [
        b.strip()
        for b in os.environ.get(branch_env_var, "").splitlines()
        if b.strip()
    ]
    if extra_branches:
        branch_runs = _add_branch_placeholders(branch_runs, extra_branches, prefix=prefix)
    github_cfg = cfg.get("ingestion", {}).get("github", {})
    namespace = cfg.get("namespace_prefix", "")
    meta = {
        "gitlab_url": cfg.get("gitlab_url", "https://gitlab-master.nvidia.com"),
        "gitlab_project": cfg.get("gitlab_project", "omniverse/isaac/omni_isaac_sim"),
        "dashboard_title": cfg.get("dashboard_title", ""),
        "github_repo": github_cfg.get("repo", ""),
        # Canonical heatmap artifact name produced by the `heatmap` subcommand.
        # The dashboard's "Open heatmap" link resolves this relative to the
        # dashboard HTML so both files must live in the same directory.
        "heatmap_filename": (
            f"pipeline_test_chart_{namespace}_heatmap.html" if namespace else ""
        ),
    }
    generate_output(
        branch_runs, output_dir,
        github_data_dir=gh_dir if gh_dir.exists() else None,
        github_extra_dir=gh_extra_dir if gh_extra_dir.exists() else None,
        dashboard_meta=meta,
    )
