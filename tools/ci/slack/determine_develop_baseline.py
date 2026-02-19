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
from typing import Optional

import gitlab


def find_develop_baseline_pipeline(project_id: str, branch: str = "develop", max_pipelines: int = 100) -> dict | None:
    """Find a suitable develop pipeline for baseline comparison.

    Search for a finished develop pipeline that was not from a schedule and
    not from a version bump commit.

    Args:
        project_id: GitLab project ID.
        branch: Branch name to search pipelines for.
        max_pipelines: Maximum number of pipelines to check.

    Returns:
        Pipeline dictionary if found, None otherwise.

    Raises:
        ValueError: If CI_GITLAB_API_TOKEN environment variable is not set.
        Exception: If the GitLab API request fails.
    """
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("CI_GITLAB_API_TOKEN environment variable is not set")

    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab-master.nvidia.com")

    # Create GitLab client
    gl = gitlab.Gitlab(url=gitlab_url, private_token=private_token)

    try:
        gl.auth()
        if gl.user is None:
            raise ValueError("GitLab authentication failed")
    except Exception as e:
        raise ValueError(f"GitLab authentication failed: {e}")

    try:
        project = gl.projects.get(project_id)

        # Fetch pipelines for the specified branch
        pipelines = project.pipelines.list(
            ref=branch,
            per_page=max_pipelines,
            order_by="id",
            sort="desc",
            get_all=False,
        )

        for pipeline in pipelines:
            # Check if pipeline is finished
            if pipeline.status not in ["success", "failed"]:
                continue

            # Check if pipeline was from a schedule
            if pipeline.source == "schedule":
                continue

            # Fetch commit details to check for version bump
            try:
                commit = project.commits.get(pipeline.sha)

                # Check if commit message contains "Bumped version"
                if "Bumped version" in commit.message:
                    continue

                # Found a suitable pipeline - return as dict for compatibility
                return {
                    "id": pipeline.id,
                    "status": pipeline.status,
                    "web_url": pipeline.web_url,
                    "created_at": pipeline.created_at,
                    "sha": pipeline.sha,
                    "ref": pipeline.ref,
                    "source": pipeline.source,
                }

            except Exception as e:
                # If we can't fetch commit details, skip this pipeline
                print(f"Warning: Could not fetch commit details for pipeline {pipeline.id}: {e}")
                continue

        return None

    except Exception as e:
        raise Exception(f"Failed to fetch pipelines: {e}")


def main() -> int | None:
    """Main entry point for the develop baseline determination script."""
    parser = argparse.ArgumentParser(description="Find a suitable develop pipeline for baseline comparison")

    parser.add_argument(
        "--project-id",
        help="GitLab project ID (default: from CI_PROJECT_ID env var)",
    )

    parser.add_argument(
        "--branch",
        default="develop",
        help="Branch name to search (default: develop)",
    )

    parser.add_argument(
        "--max-pipelines",
        type=int,
        default=100,
        help="Maximum number of pipelines to check (default: 100)",
    )

    args = parser.parse_args()

    project_id = args.project_id or os.getenv("CI_PROJECT_ID")
    if project_id is None:
        raise ValueError("Project ID must be provided via --project-id or CI_PROJECT_ID environment variable")

    try:
        pipeline = find_develop_baseline_pipeline(project_id, args.branch, args.max_pipelines)

        if pipeline:
            print(f"Found suitable baseline pipeline: {pipeline['id']}")
            print(f"Status: {pipeline['status']}")
            print(f"Web URL: {pipeline['web_url']}")
            print(f"Created at: {pipeline['created_at']}")
            return pipeline["id"]
        else:
            print("No suitable baseline pipeline found")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    main()
