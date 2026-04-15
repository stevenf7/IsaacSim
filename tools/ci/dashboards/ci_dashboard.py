# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Manage CI test dashboards for IsaacLab and IsaacSim.

Subcommands:

ci — process a local JUnit XML file and update the cache.
Useful for manual testing or custom pipelines that produce JUnit XML directly::

    python tools/ci/dashboards/ci_dashboard.py ci \\
        --junit-xml        _isaaclab/tests/full_report.xml \\
        --isaac-lab-branch "${ISAAC_LAB_BRANCH:-develop}" \\
        --data-dir         _isaaclab_cache
    # --pipeline-id, --pipeline-url, --commit-sha, --isaac-sim-branch default
    # from $CI_PIPELINE_ID, $CI_PIPELINE_URL, $CI_COMMIT_SHA, and
    # $CI_MERGE_REQUEST_TARGET_BRANCH_NAME / $CI_COMMIT_REF_NAME respectively.
    #
    # Note: CI dashboard jobs now use fetch-gitlab + generate instead of ci.

fetch-gitlab — pull historical data from GitLab into the local cache.
Tokens are resolved automatically from environment variables
(``GITLAB_AUTH_TOKEN`` → ``GITLAB_TOKEN`` → ``GITLAB_API_TOKEN``).
Run via the manual ``get-isaac-lab-historical-data`` CI job or locally::

    export GITLAB_AUTH_TOKEN=glpat-...
    python tools/ci/dashboards/ci_dashboard.py fetch-gitlab \\
        --isaac-sim-branch develop \\
        --isaac-lab-branch develop \\
        --data-dir    _isaaclab_cache

    # Add --force-refetch to re-download runs already in the cache.
    # Add --verbose for per-pipeline progress.

fetch-github — pull IsaacLab GitHub Actions build/compat data into the local cache.
Token resolved from ``GITHUB_NVIDIA_DEV_TOKEN`` → ``GITHUB_TOKEN`` → ``GITHUB_API_TOKEN``::

    export GITHUB_NVIDIA_DEV_TOKEN=ghp-...   # optional but recommended
    python tools/ci/dashboards/ci_dashboard.py fetch-github \\
        --data-dir _isaaclab_cache

generate — rebuild dashboard HTML from the local cache, no network calls::

    python tools/ci/dashboards/ci_dashboard.py generate \\
        --data-dir   _isaaclab_cache
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure the package is importable when invoked directly as a script.
_pkg_dir = str(Path(__file__).resolve().parent.parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from dashboards.clients import _resolve_token, _GITLAB_TOKEN_VARS, _GITHUB_TOKEN_VARS
from dashboards.commands import run_ci_mode, run_generate_only_mode, run_github_fetch_only
from dashboards.config import load_config
from dashboards.gitlab_fetch import run_fetch_mode
from dashboards.slack import run_slack_mode


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    _config_help = "Path to dashboard config YAML (optional; built-in defaults used if omitted)"

    # ── ci ─────────────────────────────────────────────────────────────────────
    ci_p = subparsers.add_parser(
        "ci",
        help="Record current pipeline JUnit XML into cache and regenerate dashboard",
        description="Process the current pipeline's JUnit XML, update the cache, and generate dashboard output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ci_p.add_argument("--config", default=None, help=_config_help)
    ci_p.add_argument("--data-dir", default="_isaaclab_cache",
                      help="Cache directory (default: _isaaclab_cache)")
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
    gl_p.add_argument("--config", default=None, help=_config_help)
    gl_p.add_argument(
        "--project", default="omniverse/isaac/omni_isaac_sim",
        help="GitLab project path (default: omniverse/isaac/omni_isaac_sim)")
    gl_p.add_argument("--data-dir", default="_isaaclab_cache",
                      help="Cache directory (default: _isaaclab_cache)")
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
        "--extra-pipeline-id", default=None, metavar="PIPELINE_ID",
        help="Additional pipeline ID to fetch unconditionally (e.g. the current CI pipeline). "
             "Useful when the pipeline is still running and would be excluded by scope=finished.")
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
    gh_p.add_argument("--config", default=None, help=_config_help)
    gh_p.add_argument("--data-dir", default="_isaaclab_cache",
                      help="Cache directory (default: _isaaclab_cache)")
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
    gen_p.add_argument("--config", default=None, help=_config_help)
    gen_p.add_argument("--data-dir", default="_isaaclab_cache",
                       help="Cache directory (default: _isaaclab_cache)")
    gen_p.add_argument("--output-dir", default=None,
                       help="Output directory (default: <data-dir>/output)")

    # ── slack ───────────────────────────────────────────────────────────────────
    slack_p = subparsers.add_parser(
        "slack",
        help="Post pipeline status, heatmap, and regression analysis to Slack",
        description=(
            "Detect the current pipeline type, post a status summary and job list to Slack, "
            "and (depending on pipeline type) also post a heatmap and regression analysis."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    slack_p.add_argument("--config", default=None, help=_config_help)
    slack_p.add_argument(
        "--channel", default=None,
        help="Override Slack channel (e.g. '#isaac-sim-ci'). "
             "Falls back to $SLACK_CHANNEL, then config routing rules, then '#isaac-sim-ci'.")
    slack_p.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be posted without actually calling the Slack API")
    slack_p.add_argument(
        "--job-report", action="store_true",
        help="Post a single job status notification (CI_JOB_STATUS/NAME/URL) "
             "instead of a full pipeline report. Used in job after_script.")

    args = parser.parse_args()
    config = load_config(args.config)

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
        run_ci_mode(args, config)
    elif args.command == "fetch-gitlab":
        run_fetch_mode(args, config)
    elif args.command == "fetch-github":
        run_github_fetch_only(args, config)
    elif args.command == "generate":
        if not args.output_dir:
            args.output_dir = str(Path(args.data_dir) / "output")
        run_generate_only_mode(args, config)
    elif args.command == "slack":
        run_slack_mode(args, config)


if __name__ == "__main__":
    main()
