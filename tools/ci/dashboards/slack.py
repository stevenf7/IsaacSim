# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Slack integration for CI dashboard — posting pipeline status, heatmaps, and regression analysis."""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.parse
from datetime import datetime
from .config import load_config, _cfg_slack_token, _cfg_channel_id_map, _cfg_resolve_channel, _cfg_gitlab_url, _cfg_kit_project_id
from .clients import GitLabClient, _resolve_token, _GITLAB_TOKEN_VARS
from .heatmap import run_pipeline_test_stats
from .regression import PipelineType, detect_pipeline_type, _run_regression_analysis, _find_baseline_pipeline, _format_failure_report, _fetch_pipeline_test_report_api, _find_regressions


def _emoji_for_job_status(status: str, allow_fail: bool = False) -> str:
    if status == "success":
        return ":gitlab_ci_status_success: "
    if status == "failed":
        return ":gitlab_ci_status_warning:" if allow_fail else ":gitlab_ci_status_failed: "
    if status == "canceled":
        return ":gitlab_ci_status_canceled: "
    if status == "created":
        return ":gitlab_ci_status_created: "
    return ":gitlab_ci_status_not_found: "


def _post_to_slack(
    message_text: str,
    channel: str,
    thread: str | None = None,
    file: str | None = None,
    token: str | None = None,
    channel_id_map: dict[str, str] | None = None,
) -> dict:
    """Post a message or upload a file to a Slack channel.

    *channel* may be a name (e.g. ``'#isaac-sim-ci'``) or a channel ID.
    When uploading a file, *channel_id_map* is used to resolve the name to an ID.
    """
    try:
        from slack_sdk import WebClient
    except ImportError:
        print("ERROR: slack_sdk not installed. Install with: pip install slack-sdk", file=sys.stderr)
        return {}

    if token is None:
        token = os.getenv("DS_CI_SLACK_TOKEN")
    if not token:
        raise ValueError("Slack token not available (DS_CI_SLACK_TOKEN not set)")

    client = WebClient(token=token)

    if file is not None:
        _map = channel_id_map or {}
        channel_id = _map.get(channel, channel)
        params: dict = {"channel": channel_id, "file": file, "title": file,
                        "initial_comment": message_text}
        if thread is not None:
            params["thread_ts"] = thread
        return client.files_upload_v2(**params)

    response = client.chat_postMessage(channel=channel, text=message_text, thread_ts=thread)
    permalink = client.chat_getPermalink(channel=response["channel"], message_ts=response["ts"])
    if "permalink" in permalink and thread is None:
        print(f"Posted to Slack {permalink['permalink']}")
    return response


def _header_for_pipeline_post(
    pipeline_type: PipelineType,
    client: "GitLabClient",
    project_id: str,
    kit_project_id: str,
    gitlab_url: str,
    dashboard_title: str = "",
) -> str:
    """Generate the Slack thread header for a pipeline (uses GitLabClient)."""
    project_enc = urllib.parse.quote(str(project_id), safe="")
    kit_enc = urllib.parse.quote(str(kit_project_id), safe="")
    base = gitlab_url.rstrip("/")

    if pipeline_type in (PipelineType.KIT_NIGHTLY, PipelineType.KIT_MR, PipelineType.KIT_POST_MERGE):
        upstream_id = os.getenv("UPSTREAM_PIPELINE_ID")
        if not upstream_id:
            return "Downstream pipeline"
        upstream_url = f"{base}/omniverse/kit/pipelines/{upstream_id}"
        try:
            pl = client.get_json(f"/projects/{kit_enc}/pipelines/{upstream_id}")
            ref = pl.get("ref", "")
            if pipeline_type == PipelineType.KIT_NIGHTLY:
                return (f"Downstream pipeline started from <{upstream_url}|upstream pipeline {upstream_id}>, "
                        f"which was a nightly pipeline on branch `{ref}`")
            if pipeline_type == PipelineType.KIT_MR:
                if "refs/merge-requests" in ref:
                    mr_num = ref.split("/")[2]
                    try:
                        mr = client.get_json(f"/projects/{kit_enc}/merge_requests/{mr_num}")
                        return (f"Downstream pipeline started from <{upstream_url}|upstream pipeline {upstream_id}>, "
                                f"which was for merge request <{mr['web_url']}|{mr_num}>\n`{mr['title']}`\n")
                    except Exception:
                        pass
                return (f"Downstream pipeline started from <{upstream_url}|upstream pipeline {upstream_id}> "
                        f"(merge request)")
            if pipeline_type == PipelineType.KIT_POST_MERGE:
                return (f"Downstream pipeline started from Kit post-merge "
                        f"<{upstream_url}|upstream pipeline {upstream_id}>")
        except Exception:
            return f"Downstream pipeline started from <{upstream_url}|upstream pipeline {upstream_id}>"

    if pipeline_type == PipelineType.ISAAC_NIGHTLY:
        return "Schedule"

    if pipeline_type == PipelineType.ISAAC_MR:
        label = f"{dashboard_title} MR pipeline" if dashboard_title else "Isaac MR pipeline"
        ref_name = os.getenv("CI_COMMIT_REF_NAME")
        if not ref_name:
            return label
        if "refs/merge-requests" in ref_name:
            mr_num = ref_name.split("/")[2]
            try:
                mr = client.get_json(f"/projects/{project_enc}/merge_requests/{mr_num}")
                return f"{label} started from <{mr['web_url']}|MR {mr_num}>\n`{mr['title']}`"
            except Exception:
                return f"{label} - `{ref_name}`"
        return f"{label} - `{ref_name}`"

    if pipeline_type == PipelineType.ISAAC_POST_MERGE:
        label = f"{dashboard_title} Post Merge pipeline" if dashboard_title else "Post Merge pipeline"
        return label

    if pipeline_type == PipelineType.UNKNOWN:
        upstream_id = os.getenv("UPSTREAM_PIPELINE_ID")
        if upstream_id:
            upstream_url = f"{base}/omniverse/kit/pipelines/{upstream_id}"
            return (f"Downstream pipeline started from "
                    f"<{upstream_url}|upstream pipeline {upstream_id}> (type unknown)")
        return "Pipeline type unknown"

    return ""


def _post_heatmap_to_slack(
    display_pipeline_url: str,
    channel: str,
    thread_ts: str,
    config: dict,
    branch: str | None = None,
    variable_filters: dict | None = None,
    pipeline_sources: list[str] | None = None,
    exclude_isaaclab: bool = True,
    exclude_container_tests: bool = False,
    heatmap_subtitle: str | None = None,
    include_pipeline_id: int | str | None = None,
) -> None:
    """Generate a Plotly heatmap and upload it to Slack."""
    hcfg = config.get("slack", {}).get("heatmap", {})
    excl = list(hcfg.get("exclude_job_patterns", []))
    incl = list(hcfg.get("include_job_patterns", []))
    # When include_job_patterns is set, it already narrows scope — don't also
    # add the default isaac-lab exclusion (which would conflict if isaac-lab
    # jobs are the ones being included).
    if exclude_isaaclab and not incl and "isaac-lab" not in excl:
        excl.append("isaac-lab")
    if exclude_container_tests and "test-container" not in excl:
        excl.append("test-container")

    run_pipeline_test_stats(
        heatmap=True, quiet=True,
        exclude_patterns=excl,
        include_patterns=incl or None,
        limit=hcfg.get("limit", 100),
        branch=branch or os.getenv("CI_COMMIT_REF_NAME", "develop"),
        variable_filters=variable_filters,
        pipeline_sources=pipeline_sources,
        heatmap_subtitle=heatmap_subtitle,
        include_pipeline_id=int(include_pipeline_id) if include_pipeline_id is not None else None,
    )

    token = _cfg_slack_token(config)
    cmap = _cfg_channel_id_map(config)
    for fname in ("pipeline_test_chart_heatmap.html", "pipeline_test_chart_heatmap.png"):
        if os.path.isfile(fname):
            _post_to_slack(
                f"Test heatmap for {display_pipeline_url}",
                channel=channel, thread=thread_ts, file=fname,
                token=token, channel_id_map=cmap,
            )


def _post_test_analysis_to_slack(
    client: "GitLabClient",
    project_enc: str,
    pipeline_id: str,
    channel: str,
    thread_ts: str,
    config: dict,
    baseline_branch: str = "develop",
) -> None:
    """Run failure analysis and post results to a Slack thread.

    Posts: pipeline comparison table, a tagged failure summary (new vs
    pre-existing), and the full failure report as a file attachment.
    Falls back to listing all failures without tagging when no baseline is
    available.
    """
    bcfg = config.get("baseline", {})
    rcfg = config.get("slack", {}).get("reporting", {})
    hcfg = config.get("slack", {}).get("heatmap", {})
    skip_sources = bcfg.get("skip_sources", ["schedule"])
    skip_pattern = bcfg.get("skip_commit_message_pattern", "Bumped version")
    show_all = rcfg.get("show_all_failures", True)
    max_listed = rcfg.get("max_failures_listed", 30)
    # Reuse heatmap job filters for regression analysis so both show the same test scope
    include_job = hcfg.get("include_job_patterns") or None
    exclude_job = hcfg.get("exclude_job_patterns") or None

    if baseline_branch == "develop":
        baseline_pl = _find_baseline_pipeline(
            client, project_enc, branch=baseline_branch,
            skip_sources=skip_sources, skip_commit_pattern=skip_pattern,
        )
        baseline_type = "pipeline" if baseline_pl else None
        baseline_value = str(baseline_pl["id"]) if baseline_pl else None
    else:
        baseline_type, baseline_value = "branch", baseline_branch

    sections: list | None = None
    all_failures: list | None = None
    has_baseline = False

    if baseline_type is not None:
        result = _run_regression_analysis(
            client, project_enc,
            source_type="pipeline", source_value=pipeline_id,
            baseline_type=baseline_type, baseline_value=baseline_value,
            output_file="regressions.txt", quiet=True,
            include_job_patterns=include_job, exclude_job_patterns=exclude_job,
        )
        if result is not None:
            sections, all_failures = result
            has_baseline = True

    # Fallback: fetch test data directly to show failures without baseline context
    if all_failures is None:
        test_data = _fetch_pipeline_test_report_api(
            client, project_enc, pipeline_id,
            include_patterns=include_job, exclude_patterns=exclude_job)
        if test_data:
            all_failures, _, _ = _find_regressions(
                {}, test_data, output_file="regressions.txt", quiet=True)

    token = _cfg_slack_token(config)
    cmap = _cfg_channel_id_map(config)

    def _post_chunked(text: str) -> None:
        if len(text) <= 3000:
            _post_to_slack(f"```\n{text}\n```",
                           channel=channel, thread=thread_ts, token=token, channel_id_map=cmap)
            return
        lines, chunk, length = text.split("\n"), [], 0
        for line in lines:
            ll = len(line) + 1
            if length + ll > 3000 and chunk:
                block = "\n".join(chunk)
                _post_to_slack(f"```\n{block}\n```",
                               channel=channel, thread=thread_ts, token=token, channel_id_map=cmap)
                chunk, length = [], 0
            chunk.append(line)
            length += ll
        if chunk:
            block = "\n".join(chunk)
            _post_to_slack(f"```\n{block}\n```",
                           channel=channel, thread=thread_ts, token=token, channel_id_map=cmap)

    # Post info + comparison table + mapping summary
    if sections:
        for section in sections[:3]:
            if section:
                _post_chunked(section)

    # Post Slack-formatted failure summary
    if show_all and all_failures is not None:
        failure_text = _format_failure_report(all_failures, has_baseline=has_baseline,
                                              max_listed=max_listed)
        _post_to_slack(failure_text, channel=channel, thread=thread_ts,
                       token=token, channel_id_map=cmap)

    # Attach full report file
    if os.path.isfile("regressions.txt"):
        _post_to_slack("Full Test Failure Report", channel=channel, thread=thread_ts,
                       file="regressions.txt", token=token, channel_id_map=cmap)


# ── Slack subcommand ────────────────────────────────────────────────────────────

def run_slack_mode(args: argparse.Namespace, config: dict) -> None:
    """Post pipeline status, heatmap, and regression analysis to Slack."""
    token = _cfg_slack_token(config)
    cmap = _cfg_channel_id_map(config)
    # Channel: explicit --channel flag > $SLACK_CHANNEL env var > config routing rules > '#isaac-sim-ci'
    channel = args.channel or os.getenv("SLACK_CHANNEL") or _cfg_resolve_channel(config)

    # ── Job-level report (used in after_script) ──────────────────────────────
    if getattr(args, "job_report", False):
        job_status = os.getenv("CI_JOB_STATUS", "unknown")
        job_name = os.getenv("CI_JOB_NAME", "unknown job")
        ref = os.getenv("CI_COMMIT_REF_NAME", "unknown branch")
        job_id = os.getenv("CI_JOB_ID", "")
        pipeline_id_env = os.getenv("CI_PIPELINE_ID", "")
        job_url = os.getenv("CI_JOB_URL")
        pipeline_url = os.getenv("CI_PIPELINE_URL")

        text = _emoji_for_job_status(job_status) + f"*{job_name}* {job_status} for branch `{ref}`\n"
        text += (f"<{job_url}|Job {job_id}>\n" if job_url else f"Job {job_id}\n")
        text += (f"<{pipeline_url}|Pipeline {pipeline_id_env}>" if pipeline_url else f"Pipeline {pipeline_id_env}")

        if args.dry_run:
            print(f"[DRY RUN] Would post job report to {channel}:\n{text}")
            return
        _post_to_slack(text, channel=channel, token=token, channel_id_map=cmap)
        return

    # ── Pipeline-level report ────────────────────────────────────────────────
    gitlab_url = _cfg_gitlab_url(config)
    gl_token, _ = _resolve_token(_GITLAB_TOKEN_VARS)
    if not gl_token:
        gl_token = os.getenv("CI_GITLAB_API_TOKEN", "")

    client = GitLabClient(gitlab_url, token=gl_token or None)
    project_id = os.getenv("CI_PROJECT_ID", "")
    project_enc = urllib.parse.quote(project_id, safe="")
    pipeline_id = os.getenv("CI_PIPELINE_ID", "")
    kit_project_id = _cfg_kit_project_id(config)

    if not pipeline_id or not project_id:
        print("ERROR: CI_PIPELINE_ID and CI_PROJECT_ID must be set.", file=sys.stderr)
        return

    try:
        pipeline = client.get_json(f"/projects/{project_enc}/pipelines/{pipeline_id}")
    except Exception as exc:
        print(f"ERROR: Failed to fetch pipeline {pipeline_id}: {exc}", file=sys.stderr)
        return

    ref = pipeline.get("ref", "")
    if "refs/merge-requests/" in ref:
        mr_num = ref.split("/")[2]
        try:
            mr = client.get_json(f"/projects/{project_enc}/merge_requests/{mr_num}")
            ref_display = f" <{mr['web_url']}|MR {mr_num} - {mr['title']}>"
        except Exception:
            ref_display = f"`{ref}`"
    else:
        ref_display = f"`{ref}`"

    pipeline_type = detect_pipeline_type(pipeline.get("source", ""))
    source_header = _header_for_pipeline_post(
        pipeline_type, client, project_id, kit_project_id, gitlab_url,
        dashboard_title=config.get("dashboard_title", ""))
    display_url = f"<{pipeline['web_url']}|{pipeline_id}>"

    header = f":gitlab: *Pipeline Status for {display_url}* :: {ref_display} :thread:\n"
    if source_header:
        header += f"{source_header}\n"

    if args.dry_run:
        print(f"[DRY RUN] Would post to {channel}:\n{header}")
        print(f"[DRY RUN] Pipeline type: {pipeline_type.value}")
        return

    response = _post_to_slack(header, channel=channel, token=token, channel_id_map=cmap)
    thread_ts = response.get("ts", "")

    hcfg = config.get("slack", {}).get("heatmap", {})
    try:
        jobs = list(client.get_paginated(f"/projects/{project_enc}/pipelines/{pipeline_id}/jobs"))
        incl = hcfg.get("include_job_patterns", [])
        excl = hcfg.get("exclude_job_patterns", [])
        job_text = "Jobs:\n"
        for job in sorted(jobs, key=lambda j: (j.get("started_at") is None, j.get("started_at") or "")):
            name = job.get("name", "")
            if incl and not any(p in name for p in incl):
                continue
            if excl and any(p in name for p in excl):
                continue
            job_text += (
                f"* {_emoji_for_job_status(job['status'], job.get('allow_failure', False))}"
                f" `{name}` :: <{job['web_url']}|{job['status']}>\n"
            )
        _post_to_slack(job_text, channel=channel, thread=thread_ts, token=token, channel_id_map=cmap)
    except Exception as exc:
        print(f"Warning: could not fetch jobs: {exc}")

    post_for = set(hcfg.get("post_for", ["KIT_NIGHTLY", "KIT_POST_MERGE", "ISAAC_POST_MERGE"]))
    always_heatmap = hcfg.get("always_generate", False)
    heatmap_generated = False

    if pipeline_type == PipelineType.KIT_NIGHTLY and "KIT_NIGHTLY" in post_for:
        branch = os.getenv("CI_COMMIT_REF_NAME", "develop-kit-tot")
        subtitle = f"Nightly Kit Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        _post_heatmap_to_slack(
            display_url, channel, thread_ts, config, branch=branch,
            variable_filters={"UPSTREAM_PIPELINE_SOURCE": ["nightly", "post_merge"]},
            heatmap_subtitle=subtitle, include_pipeline_id=pipeline_id,
        )
        heatmap_generated = True
        time.sleep(10)
        _post_test_analysis_to_slack(client, project_enc, pipeline_id, channel, thread_ts, config)

    if pipeline_type == PipelineType.KIT_POST_MERGE and "KIT_POST_MERGE" in post_for:
        branch = os.getenv("CI_COMMIT_REF_NAME", "develop-kit-tot")
        subtitle = f"Post-Merge Kit Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        _post_heatmap_to_slack(
            display_url, channel, thread_ts, config, branch=branch,
            variable_filters={"UPSTREAM_PIPELINE_SOURCE": ["nightly", "post_merge"]},
            exclude_container_tests=True,
            heatmap_subtitle=subtitle, include_pipeline_id=pipeline_id,
        )
        heatmap_generated = True

    if pipeline_type == PipelineType.KIT_MR:
        try:
            upstream_id = os.getenv("UPSTREAM_PIPELINE_ID")
            kit_enc = urllib.parse.quote(str(kit_project_id), safe="")
            upstream_pl = client.get_json(f"/projects/{kit_enc}/pipelines/{upstream_id}")
            ref_parts = upstream_pl.get("ref", "").split("/")
            if len(ref_parts) >= 3 and ref_parts[0] == "refs":
                mr_num = ref_parts[2]
                mr = client.get_json(f"/projects/{kit_enc}/merge_requests/{mr_num}")
                isaac_branch = f"kit-integration/{mr.get('target_branch', 'master')}"
                try:
                    client.get(f"/projects/{project_enc}/repository/branches/"
                               f"{urllib.parse.quote(isaac_branch, safe='')}")
                except Exception:
                    isaac_branch = "develop-kit-tot"
                _post_test_analysis_to_slack(
                    client, project_enc, pipeline_id, channel, thread_ts, config,
                    baseline_branch=isaac_branch,
                )
                if "KIT_MR" in post_for:
                    subtitle = (f"Target branch {isaac_branch} history on "
                                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    _post_heatmap_to_slack(
                        display_url, channel, thread_ts, config,
                        branch=isaac_branch, pipeline_sources=["push"],
                        heatmap_subtitle=subtitle,
                    )
                    heatmap_generated = True
        except Exception as exc:
            print(f"ERROR: Failed to process KIT_MR pipeline: {exc}", file=sys.stderr)

    if pipeline_type == PipelineType.ISAAC_POST_MERGE and "ISAAC_POST_MERGE" in post_for:
        branch = os.getenv("CI_COMMIT_REF_NAME", "develop")
        subtitle = f"Post-Merge Isaac Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        _post_heatmap_to_slack(
            display_url, channel, thread_ts, config,
            branch="develop", pipeline_sources=["push"],
            heatmap_subtitle=subtitle, include_pipeline_id=pipeline_id,
        )
        heatmap_generated = True

    if pipeline_type == PipelineType.ISAAC_MR:
        target_branch = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "develop")
        _post_test_analysis_to_slack(
            client, project_enc, pipeline_id, channel, thread_ts, config,
            baseline_branch=target_branch,
        )
        if "ISAAC_MR" in post_for:
            subtitle = (f"Target branch {target_branch} history on "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            _post_heatmap_to_slack(
                display_url, channel, thread_ts, config,
                branch=target_branch, pipeline_sources=["push"],
                heatmap_subtitle=subtitle,
            )
            heatmap_generated = True

    if os.getenv("SEND_HEATMAP") == "true":
        branch = os.getenv("CI_COMMIT_REF_NAME", "develop")
        subtitle = f"Isaac Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        _post_heatmap_to_slack(
            display_url, channel, thread_ts, config,
            branch="develop", pipeline_sources=["push"],
            exclude_isaaclab=True, exclude_container_tests=True,
            heatmap_subtitle=subtitle, include_pipeline_id=pipeline_id,
        )
        heatmap_generated = True

    # Fallback: always generate a heatmap if configured and none was generated above
    if always_heatmap and not heatmap_generated:
        branch = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME",
                           os.getenv("CI_COMMIT_REF_NAME", "develop"))
        subtitle = f"Pipeline for branch {branch} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        _post_heatmap_to_slack(
            display_url, channel, thread_ts, config,
            branch=branch, pipeline_sources=["push"],
            heatmap_subtitle=subtitle, include_pipeline_id=pipeline_id,
        )
