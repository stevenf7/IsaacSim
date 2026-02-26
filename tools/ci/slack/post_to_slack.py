# Copyright (c) 2021-2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import os
import time
from datetime import datetime
from enum import Enum
from typing import Optional

import gitlab
from analyze_test_suites import run as run_analyze_test_suites
from determine_develop_baseline import find_develop_baseline_pipeline
from pipeline_test_stats import run as run_pipeline_test_stats

try:
    import slack_sdk
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("No slack_sdk found")
    exit(1)

# GitLab configuration
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")
KIT_PROJECT_ID = 6510

CHANNEL_NAME_TO_ID_MAP = {
    "#isaac-sim-ci": "C0A87GR0BR8",
    "#isaac-sim-ci-dev-null": "C0A8WKMPTEV",
    "#isaac-sim-ci-mr": "C0A9C7N8L9E",
    "#isaac-sim-kit-integration-ci": "C0AEFVCTLSE",
}


class PipelineType(Enum):
    """Enum for different pipeline types."""

    KIT_MR = "kit_mr"
    KIT_POST_MERGE = "kit_post_merge"
    KIT_NIGHTLY = "kit_nightly"
    ISAAC_NIGHTLY = "isaac_nightly"
    ISAAC_POST_MERGE = "isaac_post_merge"
    ISAAC_MR = "isaac_mr"
    UNKNOWN = "unknown"


def get_gitlab_client() -> Optional[gitlab.Gitlab]:
    """Create and authenticate a GitLab client.

    Returns:
        Authenticated GitLab client or None if authentication fails
    """
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if not private_token:
        print("ERROR: CI_GITLAB_API_TOKEN not set")
        return None

    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=private_token)

    try:
        gl.auth()
        if gl.user is None:
            print("ERROR: GitLab authentication failed!")
            return None
        return gl
    except Exception as e:
        print(f"ERROR: GitLab authentication failed: {e}")
        return None


def emoji_for_job_status(status: str, allow_fail: bool = False) -> str:
    if status == "success":
        return ":gitlab_ci_status_success: "
    elif status == "failed":
        if allow_fail:
            return ":gitlab_ci_status_warning:"
        return ":gitlab_ci_status_failed: "
    elif status == "canceled":
        return ":gitlab_ci_status_canceled: "
    elif status == "created":
        return ":gitlab_ci_status_created: "
    else:
        return ":gitlab_ci_status_not_found: "


def detect_pipeline_type(source_str: str) -> PipelineType:
    """Detect the pipeline type based on GitLab source and environment variables.

    Args:
        source_str: Pipeline source string from GitLab

    Returns:
        PipelineType enum value
    """
    upstream_pipeline_source = os.getenv("UPSTREAM_PIPELINE_SOURCE")

    if source_str == "pipeline":
        # This is a downstream pipeline from Kit
        if not os.getenv("UPSTREAM_PIPELINE_ID"):
            # Downstream pipeline without upstream ID - unknown
            return PipelineType.UNKNOWN

        # Use UPSTREAM_PIPELINE_SOURCE as the discriminator
        if upstream_pipeline_source == "nightly":
            return PipelineType.KIT_NIGHTLY
        elif upstream_pipeline_source == "merge_request":
            return PipelineType.KIT_MR
        elif upstream_pipeline_source == "post_merge":
            return PipelineType.KIT_POST_MERGE
        else:
            # UPSTREAM_PIPELINE_SOURCE not set or not recognized
            return PipelineType.UNKNOWN

    elif source_str == "merge_request_event":
        # Isaac MR pipeline
        return PipelineType.ISAAC_MR
    elif source_str == "schedule":
        # Isaac nightly scheduled pipeline
        return PipelineType.ISAAC_NIGHTLY
    elif source_str == "push":
        # Isaac post-merge pipeline
        return PipelineType.ISAAC_POST_MERGE
    else:
        # Unknown source type
        return PipelineType.UNKNOWN


def header_for_pipeline_post(pipeline_type: PipelineType, gl: gitlab.Gitlab) -> str:
    """Generate Slack header string for a pipeline based on its type.

    Args:
        pipeline_type: PipelineType enum value
        gl: Authenticated GitLab client

    Returns:
        Formatted header string for Slack post
    """
    # Kit downstream types need upstream pipeline information
    if pipeline_type in (PipelineType.KIT_NIGHTLY, PipelineType.KIT_MR, PipelineType.KIT_POST_MERGE):
        upstream_pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID")
        if not upstream_pipeline_id:
            # No upstream pipeline ID available
            return "Downstream pipeline"

        upstream_pipeline_url = f"https://gitlab-master.nvidia.com/omniverse/kit/pipelines/{upstream_pipeline_id}"

        try:
            kit_project = gl.projects.get(KIT_PROJECT_ID)
            upstream_pipeline = kit_project.pipelines.get(upstream_pipeline_id)

            if pipeline_type == PipelineType.KIT_NIGHTLY:
                # Downstream from Kit nightly - fetch branch name for context
                branch_name = upstream_pipeline.ref
                return f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}>, which was a nightly pipeline on branch `{branch_name}`"

            elif pipeline_type == PipelineType.KIT_MR:
                # Downstream from Kit MR - fetch MR details
                branch_name = upstream_pipeline.ref

                if "refs/merge-requests" in branch_name:
                    mr_number = branch_name.split("/")[2]
                    try:
                        mr = kit_project.mergerequests.get(mr_number)
                        mr_web_url = mr.web_url
                        return f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}>, which was for merge request <{mr_web_url}|{mr_number}>\n`{mr.title}`\n"
                    except Exception:
                        pass

                # Fallback if MR fetch fails
                return f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}> (merge request)"

            elif pipeline_type == PipelineType.KIT_POST_MERGE:
                # Downstream from Kit post-merge
                return f"Downstream pipeline started from Kit post-merge <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}>"

        except Exception:
            # Fallback if any API call fails
            return (
                f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}>"
            )

    elif pipeline_type == PipelineType.ISAAC_NIGHTLY:
        # Isaac's own scheduled/nightly pipeline - no upstream info
        return "Schedule"

    elif pipeline_type == PipelineType.ISAAC_MR:
        ref_name = os.getenv("CI_COMMIT_REF_NAME")
        if ref_name is None:
            return "Isaac MR pipeline"
        if "refs/merge-requests" in ref_name:
            mr_number = ref_name.split("/")[2]
            try:
                project_id = os.getenv("CI_PROJECT_ID")
                project = gl.projects.get(project_id)
                mr = project.mergerequests.get(mr_number)
                return f"Isaac MR pipeline started from <{mr.web_url}|MR {mr_number}>\n`{mr.title}`"
            except Exception:
                return f"Isaac MR pipeline - `{ref_name}`"
        else:
            return f"Isaac MR pipeline - `{ref_name}`"

    elif pipeline_type == PipelineType.ISAAC_POST_MERGE:
        return "Post Merge pipeline"

    elif pipeline_type == PipelineType.UNKNOWN:
        # Unknown pipeline type - provide generic message
        upstream_pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID")
        if upstream_pipeline_id:
            upstream_pipeline_url = f"https://gitlab-master.nvidia.com/omniverse/kit/pipelines/{upstream_pipeline_id}"
            return f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}> (type unknown)"
        else:
            return "Pipeline type unknown"

    else:
        # Shouldn't reach here, but handle gracefully
        return ""


def post_heatmap_to_slack(
    display_pipeline_url: str,
    channel: str,
    thread_ts: str,
    branch: str | None = None,
    variable_filters: dict[str, str | list[str]] | None = None,
    pipeline_sources: list[str] | None = None,
    exclude_isaaclab: bool = True,
    exclude_container_tests: bool = False,
    heatmap_subtitle: str | None = None,
    include_pipeline_id: int | str | None = None,
) -> None:
    """Generate and upload test heatmap to Slack.

    Args:
        display_pipeline_url: Formatted pipeline URL for display in messages
        channel: Slack channel to post to
        thread_ts: Thread timestamp to post as reply
        branch: Branch name to filter pipelines (optional)
        variable_filters: Dict of variable filters for pipeline_test_stats (optional; values may be str or list of str to match any)
        pipeline_sources: List of pipeline sources to filter (optional)
        exclude_isaaclab: Whether to exclude Isaac Lab integration tests (default: True)
        heatmap_subtitle: Second line title for the heatmap chart (optional)
        include_pipeline_id: Pipeline ID to show as latest in the heatmap (optional)
    """
    # Build kwargs for run_pipeline_test_stats
    stats_kwargs = {
        "heatmap": True,
        "stacked_chart": False,
        "quiet": True,
        "exclude_patterns": [],
    }

    if branch is not None:
        stats_kwargs["branch"] = branch
    if variable_filters is not None:
        stats_kwargs["variable_filters"] = variable_filters
    if pipeline_sources is not None:
        stats_kwargs["pipeline_sources"] = pipeline_sources
    if heatmap_subtitle is not None:
        stats_kwargs["heatmap_subtitle"] = heatmap_subtitle
    if include_pipeline_id is not None:
        stats_kwargs["include_pipeline_id"] = int(include_pipeline_id)
    if exclude_isaaclab:
        stats_kwargs["exclude_patterns"].append("isaaclab")

    if exclude_container_tests:
        stats_kwargs["exclude_patterns"].append("test-container")

    # Generate heatmap
    run_pipeline_test_stats(**stats_kwargs)

    heatmap_file = "pipeline_test_chart_heatmap.html"
    heatmap_image = "pipeline_test_chart_heatmap.png"

    # Upload files if they exist
    if os.path.isfile(heatmap_image) and os.path.isfile(heatmap_file):
        post_to_slack(f"Test heatmap for {display_pipeline_url}", channel=channel, thread=thread_ts, file=heatmap_file)
        post_to_slack(f"Test heatmap for {display_pipeline_url}", channel=channel, thread=thread_ts, file=heatmap_image)


def post_test_analysis_to_slack(
    pipeline_id: str, project_id: str, channel: str, thread_ts: str, baseline_branch: str = "develop"
) -> None:
    """Generate and post test suite analysis report to Slack.

    Args:
        pipeline_id: Pipeline ID to analyze
        project_id: Project ID for finding baseline
        channel: Slack channel to post to
        thread_ts: Thread timestamp to post as reply
        baseline_branch: Branch to use as baseline (default: "develop")
                        If "develop", uses find_develop_baseline_pipeline
                        Otherwise, uses the branch name directly
    """
    # Determine baseline type and value based on baseline_branch
    if baseline_branch == "develop":
        baseline_pipeline_id = find_develop_baseline_pipeline(project_id)
        if baseline_pipeline_id is None:
            return
        baseline_type = "pipeline"
        baseline_value = str(baseline_pipeline_id["id"])
    else:
        baseline_type = "branch"
        baseline_value = baseline_branch

    # Run analysis
    test_suites_text = run_analyze_test_suites(
        source_type="pipeline",
        source_value=pipeline_id,
        baseline_type=baseline_type,
        baseline_value=baseline_value,
        quiet=True,
        output_file="regressions.txt",
    )

    # Post sections (skip last section which is regressions detail)
    if test_suites_text is None:
        return

    # Post sections (skip last section which is regressions detail)
    for section in test_suites_text[:-1]:
        if not section:  # Skip empty sections
            continue

        # Split large sections into multiple messages on line breaks
        if len(section) > 3000:
            lines = section.split("\n")
            current_chunk = []
            current_length = 0

            for line in lines:
                line_length = len(line) + 1  # +1 for the newline

                # If adding this line would exceed the limit, send current chunk
                if current_length + line_length > 3000 and current_chunk:
                    post_to_slack(f"```\n{chr(10).join(current_chunk)}\n```", channel=channel, thread=thread_ts)
                    current_chunk = []
                    current_length = 0

                current_chunk.append(line)
                current_length += line_length

            # Send remaining chunk if any
            if current_chunk:
                post_to_slack(f"```\n{chr(10).join(current_chunk)}\n```", channel=channel, thread=thread_ts)
        else:
            post_to_slack(f"```\n{section}\n```", channel=channel, thread=thread_ts)

    # Post the full regression report as an attachment
    if os.path.isfile("regressions.txt"):
        post_to_slack("Regression Report", channel=channel, thread=thread_ts, file="regressions.txt")


def create_job_report_message(channel: str = "#isaac-sim-ci") -> None:
    """Create a Slack message for a job status report."""

    job_status = os.getenv("CI_JOB_STATUS", "Unknown Job Status")
    job_name = os.getenv("CI_JOB_NAME", "Unknown Job Name")
    commit_ref_name = os.getenv("CI_COMMIT_REF_NAME", "Unknown Commit Ref Name")
    job_id = os.getenv("CI_JOB_ID", "Unknown Job ID")
    pipeline_id = os.getenv("CI_PIPELINE_ID", "Unknown Pipeline ID")

    message_text = emoji_for_job_status(job_status)
    message_text += f"*{job_name}* {job_status} for branch `{commit_ref_name}`\n"
    job_url = os.getenv("CI_JOB_URL")
    if job_url is not None:
        message_text += f"<{job_url}|Job {job_id}>\n"
    else:
        message_text += f"Job {job_id}\n"
    pipeline_url = os.getenv("CI_PIPELINE_URL")
    if pipeline_url is not None:
        message_text += f"<{pipeline_url}|Pipeline {pipeline_id}>"
    else:
        message_text += f"Pipeline {pipeline_id}\n"

    post_to_slack(message_text, channel=channel)


def create_pipeline_report_message(channel: str = "#isaac-sim-ci") -> None:
    """Create a Slack message for a pipeline status report.

    Raises:
        ValueError: If GitLab authentication fails.
    """
    # Get GitLab client
    gl = get_gitlab_client()
    if not gl:
        raise ValueError("Failed to authenticate with GitLab")

    # Infer data from just CI_PIPELINE_ID and CI_PROJECT_ID
    project_id = os.getenv("CI_PROJECT_ID")
    pipeline_id = os.getenv("CI_PIPELINE_ID")

    try:
        project = gl.projects.get(project_id)
        pipeline = project.pipelines.get(pipeline_id)
    except Exception as e:
        print(f"ERROR: Failed to fetch pipeline: {e}")
        return

    display_pipeline_url = pipeline.web_url
    display_pipeline_url = f"<{display_pipeline_url}|{pipeline_id}>"
    ref = pipeline.ref
    if "refs/merge-requests/" in ref:
        mr_number = ref.split("/")[2]
        try:
            mr = project.mergerequests.get(mr_number)
            ref = f" <{mr.web_url}|MR {mr_number} - {mr.title}>"
        except Exception:
            ref = f"`{ref}`"
    else:
        ref = f"`{ref}`"

    # Detect pipeline type and generate header
    pipeline_type = detect_pipeline_type(pipeline.source)
    source_header = header_for_pipeline_post(pipeline_type, gl)

    header_text = f":gitlab: *Pipeline Status for {display_pipeline_url}* :: {ref} :thread:\n"
    if source_header != "":
        header_text += f"{source_header}\n"
    response = post_to_slack(header_text, channel=channel)
    thread_ts = response["ts"]

    # Get jobs for this pipeline
    try:
        jobs = pipeline.jobs.list(per_page=100, get_all=True)
    except Exception as e:
        print(f"ERROR: Failed to fetch jobs: {e}")
        jobs = []

    job_text = "Jobs:\n"
    for job in sorted(jobs, key=lambda x: (x.started_at is None, x.started_at or "")):
        job_text += (
            f"* {emoji_for_job_status(job.status, job.allow_failure)} `{job.name}` :: <{job.web_url}|{job.status}>\n"
        )
    post_to_slack(job_text, channel=channel, thread=thread_ts)

    # Check for downstream nightly pipelines to get extra reporting
    if pipeline_type == PipelineType.KIT_NIGHTLY:

        heatmap_subtitle = f"Nightly Kit Pipeline for branch {os.getenv('CI_COMMIT_REF_NAME', 'develop-kit-tot')}"
        # Append datetime to the subtitle
        heatmap_subtitle += f" on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Generate and upload a heatmap of the test report
        post_heatmap_to_slack(
            display_pipeline_url,
            channel,
            thread_ts,
            branch=os.getenv("CI_COMMIT_REF_NAME", "develop-kit-tot"),
            variable_filters={"UPSTREAM_PIPELINE_SOURCE": ["nightly", "post_merge"]},
            heatmap_subtitle=heatmap_subtitle,
            include_pipeline_id=pipeline_id,
        )
        time.sleep(10)

        # Get a test report analysis against a recent completed develop pipeline
        post_test_analysis_to_slack(pipeline_id, project_id, channel, thread_ts)

    # For Kit post-merge we want to generate a heatmap
    if pipeline_type == PipelineType.KIT_POST_MERGE:

        heatmap_subtitle = f"Post-Merge Kit Pipeline for branch {os.getenv('CI_COMMIT_REF_NAME', 'develop-kit-tot')}"
        # Append datetime to the subtitle
        heatmap_subtitle += f" on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Generate and upload a heatmap of the test report
        post_heatmap_to_slack(
            display_pipeline_url,
            channel,
            thread_ts,
            branch=os.getenv("CI_COMMIT_REF_NAME", "develop-kit-tot"),
            variable_filters={"UPSTREAM_PIPELINE_SOURCE": ["nightly", "post_merge"]},
            exclude_container_tests=True,
            heatmap_subtitle=heatmap_subtitle,
            include_pipeline_id=pipeline_id,
        )

    if pipeline_type == PipelineType.KIT_MR:
        try:
            # Step 1 - get pipeline details from UPSTREAM_PIPELINE_ID
            upstream_pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID")
            kit_project = gl.projects.get(KIT_PROJECT_ID)
            upstream_pipeline = kit_project.pipelines.get(upstream_pipeline_id)

            # Step 2 - get the MR details from the ref name
            ref_parts = upstream_pipeline.ref.split("/")
            if len(ref_parts) < 3 or ref_parts[0] != "refs":
                raise ValueError(f"Unexpected upstream pipeline ref format: {upstream_pipeline.ref!r}")
            mr_number = ref_parts[2]
            mr = kit_project.mergerequests.get(mr_number)
            mr_branch = mr.target_branch

            # Step 3 - check to see if we have an accommodating kit-integration/* branch
            isaac_branch_name = f"kit-integration/{mr_branch}"

            isaac_project = gl.projects.get(project_id)
            try:
                # Try to get the specific branch
                isaac_project.branches.get(isaac_branch_name)
                # Branch exists, use it
            except Exception:
                # Branch doesn't exist, fall back to develop-kit-tot
                isaac_branch_name = "develop-kit-tot"

            post_test_analysis_to_slack(pipeline_id, project_id, channel, thread_ts, baseline_branch=isaac_branch_name)
        except Exception as e:
            print(f"ERROR: Failed to process KIT_MR pipeline: {e}")

    if pipeline_type == PipelineType.ISAAC_NIGHTLY:
        # Currently no special logic, placeholder left for future use
        pass

    # Check for post-merge develop pipelines to get just heatmaps
    if pipeline_type == PipelineType.ISAAC_POST_MERGE:
        heatmap_subtitle = f"Post-Merge Isaac Pipeline for branch {os.getenv('CI_COMMIT_REF_NAME', 'develop')}"
        # Append datetime to the subtitle
        heatmap_subtitle += f" on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        # Generate and upload a heatmap of the test report
        post_heatmap_to_slack(
            display_pipeline_url,
            channel,
            thread_ts,
            branch="develop",
            pipeline_sources=["push"],
            heatmap_subtitle=heatmap_subtitle,
            include_pipeline_id=pipeline_id,
        )

    # For non-downstream MRs make sure we post the analyze_test_suites report
    if pipeline_type == PipelineType.ISAAC_MR:
        target_branch = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
        if target_branch is None:
            target_branch = "develop"  # Default to develop if not set
        # Get a test report analysis against a recent completed pipeilne matching
        # the MR target branch
        post_test_analysis_to_slack(pipeline_id, project_id, channel, thread_ts, baseline_branch=target_branch)

    # Testing code, should not encounter normally
    if os.getenv("SEND_HEATMAP") == "true":
        heatmap_subtitle = f"Isaac Pipeline for branch {os.getenv('CI_COMMIT_REF_NAME', 'develop')}"
        # Append datetime to the subtitle
        heatmap_subtitle += f" on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        post_heatmap_to_slack(
            display_pipeline_url,
            channel,
            thread_ts,
            branch="develop",
            pipeline_sources=["push"],
            exclude_isaaclab=True,
            exclude_container_tests=True,
            heatmap_subtitle=heatmap_subtitle,
            include_pipeline_id=pipeline_id,
        )


def post_to_slack(
    message_text: str, channel: str = "#isaac-sim-ci", thread: str | None = None, file: str | None = None
) -> dict:
    """Post a message to a Slack channel.

    Args:
        message_text: The message text to post.
        channel: The Slack channel to post to.
        thread: Thread timestamp to post as reply.
        file: File path to upload.

    Returns:
        The response from the Slack API.

    Raises:
        ValueError: If DS_CI_SLACK_TOKEN environment variable is not set.
        SlackApiError: If the Slack API returns an error.
    """
    token = os.getenv("DS_CI_SLACK_TOKEN")

    if token is None:
        raise ValueError("DS_CI_SLACK_TOKEN environment variable is not set")

    client = WebClient(token=token)

    if file is not None:

        if channel not in CHANNEL_NAME_TO_ID_MAP:
            raise ValueError(f"Channel {channel} not found in CHANNEL_NAME_TO_ID_MAP")

        # Build the upload parameters
        upload_params = {
            "channel": CHANNEL_NAME_TO_ID_MAP[channel],
            "file": file,
            "title": file,
            "initial_comment": message_text,
        }

        # Add thread_ts if posting to a thread
        if thread is not None:
            upload_params["thread_ts"] = thread

        response = client.files_upload_v2(**upload_params)

        # files_upload_v2 returns a different structure - no need to get permalink
        # The file is uploaded and we can return the response directly
        return response
    else:

        response = client.chat_postMessage(
            channel=channel,
            text=message_text,
            thread_ts=thread,
        )

        permalink_response = client.chat_getPermalink(channel=response["channel"], message_ts=response["ts"])
        # Only print links to the head message of threads, not replies
        if "permalink" in permalink_response and thread is None:
            print("Posted to slack {}".format(permalink_response["permalink"]))

        return response


def main() -> None:
    """Main entry point for the Slack posting script."""
    parser = argparse.ArgumentParser(description="Post CI/CD status reports to Slack")

    report_group = parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--job-report", action="store_true", help="Post a job status report")
    report_group.add_argument("--pipeline-report", action="store_true", help="Post a pipeline status report")

    parser.add_argument("--channel", default="#isaac-sim-ci", help="Slack channel to post to (default: #isaac-sim-ci)")

    args = parser.parse_args()

    if args.job_report:
        create_job_report_message(args.channel)
    elif args.pipeline_report:
        create_pipeline_report_message(args.channel)


if __name__ == "__main__":
    main()
