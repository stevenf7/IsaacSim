# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Cache management utilities for the CI dashboard.

Helpers for loading, saving, and querying the per-branch ``runs.json``
index files that track which pipeline results have been fetched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _make_section(job_id: int | None, job_url: str, summary: dict, suites: dict) -> dict:
    """Build a single section entry for per-run JSON (sections format).

    The sections format groups test results by CI job name, enabling the
    dashboard to render collapsible per-job sections.  The old flat format
    ``{"summary": ..., "suites": ...}`` is still accepted for backward
    compatibility — the JavaScript ``getSections()`` helper normalises it.
    """
    return {"job_id": job_id, "job_url": job_url, "summary": summary, "suites": suites}


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


def _branch_subdir(data_dir: str | Path, branch: str, prefix: str = "isaaclab") -> Path:
    """Return the branch-specific subdirectory, sanitizing the branch name."""
    safe = branch.replace("/", "-").replace("\\", "-")
    return Path(data_dir) / f"{prefix}_{safe}"


def _collect_all_branch_runs(data_dir: str | Path, prefix: str = "isaaclab") -> dict:
    """Scan data_dir subdirectories for runs.json files.

    Returns a dict mapping workflow key (e.g. ``"isaaclab_develop"``) to
    ``(branch_dir: Path, runs_index: dict)`` for each branch subdir found.
    Skips known non-branch directories.

    Args:
        data_dir: Root cache directory to scan.
        prefix: Workflow key prefix (e.g. ``"isaaclab"`` or ``"isaacsim"``).
                Controls how the dashboard dropdown groups these runs.
    """
    branch_runs = {}
    data_dir = Path(data_dir)
    _SKIP = {"github", "github_isaacsim", "output", "tests"}
    prefix_tag = f"{prefix}_"
    for subdir in sorted(data_dir.iterdir()):
        if not subdir.is_dir() or subdir.name in _SKIP:
            continue
        # Only collect subdirs that match the expected prefix (created by _branch_subdir)
        if not subdir.name.startswith(prefix_tag):
            continue
        runs_file = subdir / "runs.json"
        if runs_file.exists():
            try:
                runs_index = json.loads(runs_file.read_text())
            except json.JSONDecodeError as exc:
                print(f"Warning: skipping corrupt runs.json in {subdir}: {exc}", file=sys.stderr)
                continue
            # Subdir name already includes the prefix (e.g. "isaacsim_develop")
            branch_runs[subdir.name] = (subdir, runs_index)
    return branch_runs


def _add_branch_placeholders(branch_runs: dict, extra_branches: list[str],
                             prefix: str = "isaaclab") -> dict:
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
        key = f"{prefix}_{safe}"
        if key not in result:
            result[key] = (None, {"runs": []})
    return result
