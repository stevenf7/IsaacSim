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

try:
    import slack_sdk
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("No slack_sdk found")
    exit(1)

import requests


def emoji_for_job_status(status, allow_fail=False):
    if status == 'success':
        return ":gitlab_ci_status_success: "
    elif status == 'failed':
        if allow_fail:
            return ":gitlab_ci_status_warning:"
        return ":gitlab_ci_status_failed: "
    elif status == 'canceled':
        return ":gitlab_ci_status_canceled: "
    elif status == 'created':
        return ":gitlab_ci_status_created: "
    else:
        return ":gitlab_ci_status_not_found: "

def source_for_pipeline(source_str):
    if source_str == "pipeline":
        if upstream_pipeline_id := os.getenv("UPSTREAM_PIPELINE_ID"):
            upstream_pipeline_url = f"https://gitlab-master.nvidia.com/omniverse/kit/pipelines/{upstream_pipeline_id}"
            upstream_pipeline_source = os.getenv('UPSTREAM_PIPELINE_SOURCE', 'Unknown')
            return f"Downstream pipeline started from <{upstream_pipeline_url}|upstream pipeline {upstream_pipeline_id}>, which was a {upstream_pipeline_source} pipeline"
        else:
            return "Downstream pipeline"
    elif source_str == "merge_request_event":
        # Inferrable from the MR number in the ref
        return ""
    elif source_str == "schedule":
        return "Schedule"
    else:
        return source_str

def create_job_report_message(channel="#isaac-sim-ci"):
    """Create a Slack message for a job status report."""
    
    job_status = os.getenv('CI_JOB_STATUS', "Unknown Job Status")
    job_name = os.getenv('CI_JOB_NAME', "Unknown Job Name")
    commit_ref_name = os.getenv('CI_COMMIT_REF_NAME', "Unknown Commit Ref Name")
    job_id = os.getenv('CI_JOB_ID', "Unknown Job ID")
    pipeline_id = os.getenv('CI_PIPELINE_ID', "Unknown Pipeline ID")

    message_text = emoji_for_job_status(job_status)
    message_text += f"*{job_name}* {job_status} for branch `{commit_ref_name}`\n"
    job_url = os.getenv('CI_JOB_URL')
    if job_url is not None:
        message_text += f"<{job_url}|Job {job_id}>\n"
    else:
        message_text += f"Job {job_id}\n"
    pipeline_url = os.getenv('CI_PIPELINE_URL')
    if pipeline_url is not None:
        message_text += f"<{pipeline_url}|Pipeline {pipeline_id}>"
    else:
        message_text += f"Pipeline {pipeline_id}\n"

    post_to_slack(message_text, channel=channel)



def create_pipeline_report_message(channel="#isaac-sim-ci"):
    """Create a Slack message for a pipeline status report.

    Returns:
        Formatted message text for pipeline status.

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    # Infer data from just CI_PIPELINE_ID and CI_PROJECT_ID
    project_id = os.getenv('CI_PROJECT_ID')
    pipeline_id = os.getenv('CI_PIPELINE_ID')
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("CI_GITLAB_API_TOKEN environment variable is not set")

    headers = {
        "PRIVATE-TOKEN": private_token
    }
    
    pipeline_url = f"https://gitlab-master.nvidia.com/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
    response = requests.get(pipeline_url, headers=headers)
    response.raise_for_status()
    pipeline = response.json()
    

    

    display_pipeline_url = pipeline['web_url']
    display_pipeline_url = f"<{display_pipeline_url}|{pipeline_id}>"
    ref = pipeline['ref']
    if "refs/merge-requests/" in ref:
        mr_number = ref.split('/')[2]
        
        mr_url = f"https://gitlab-master.nvidia.com/api/v4/projects/{project_id}/merge_requests/{mr_number}"
        response = requests.get(mr_url, headers=headers)
        response.raise_for_status()
        mr = response.json()
        ref = f" <{mr['web_url']}|MR {mr_number} - {mr['title']}>"
    else:
        ref = f"`{ref}`"
    header_text = f":gitlab: *Pipeline Status for {display_pipeline_url}* :: {ref} :thread:\n"
    source_str = source_for_pipeline(pipeline['source'])
    if source_str != "":
        header_text += f"{source_str}\n"
    response = post_to_slack(header_text, channel=channel)
    thread_ts = response["ts"]

    # Next we need to get the jobs for this pipeline
    jobs_url = f"https://gitlab-master.nvidia.com/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs?per_page=100"
    response = requests.get(jobs_url, headers=headers)
    response.raise_for_status()
    jobs = response.json()


    job_text = "Jobs:\n"
    for job in sorted(jobs, key=lambda x: (x.get('started_at') is None, x.get('started_at') or '')):
        job_text += f"* {emoji_for_job_status(job['status'], job['allow_failure'])} `{job['name']}` :: <{job['web_url']}|{job['status']}>\n"
    post_to_slack(job_text, channel=channel, thread=thread_ts)

def post_to_slack(message_text, channel="#isaac-sim-ci", thread=None):
    """Post a message to a Slack channel.

    Args:
        param message_text: The message text to post.
        param channel: The Slack channel to post to.

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


def main():
    """Main entry point for the Slack posting script."""
    parser = argparse.ArgumentParser(
        description="Post CI/CD status reports to Slack"
    )

    report_group = parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument(
        "--job-report",
        action="store_true",
        help="Post a job status report"
    )
    report_group.add_argument(
        "--pipeline-report",
        action="store_true",
        help="Post a pipeline status report"
    )

    parser.add_argument(
        "--channel",
        default="#isaac-sim-ci",
        help="Slack channel to post to (default: #isaac-sim-ci)"
    )

    args = parser.parse_args()

    if args.job_report:
        create_job_report_message(args.channel)
    elif args.pipeline_report:
        create_pipeline_report_message(args.channel)



if __name__ == "__main__":
    main()
