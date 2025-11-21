"""
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
"""
import os

import requests


def find_kit_build_job_in_pipeline(platform, config, gitlab_url, project_id, pipeline_id, headers):
    """Search a GitLab pipeline for a specific kit build job.

    Args:
        platform: The platform identifier (e.g., 'linux-x86_64', 'windows-x86_64', 'linux-aarch64').
        config: The build configuration ('release' or 'debug').
        gitlab_url: The base URL of the GitLab instance.
        project_id: The GitLab project ID.
        pipeline_id: The pipeline ID to search.
        headers: Dictionary containing authentication headers with PRIVATE-TOKEN.

    Returns:
        Tuple of (bool, dict or None): First element is True if a matching successful job was found,
        False otherwise. Second element is the job dictionary if found, None otherwise.
    """
    # Find the target job in the pipeline
    target_job_name = f"kit-build-{config}-{platform}"
    jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    response = requests.get(jobs_url, headers=headers, params={"per_page": 100}, timeout=30)
    response.raise_for_status()
    jobs = response.json()

    target_jobs = [job for job in jobs if job["name"] == target_job_name and job["status"] == "success"]
    if len(target_jobs) == 1:
        return True, target_jobs[0]

    return False, None


def download_kit_artifacts(project_id, pipeline_id, platform, config, output_path="artifacts.zip", gitlab_url="https://gitlab-master.nvidia.com"):
    """Download kit build artifacts from a GitLab pipeline.

    Args:
        project_id: The GitLab project ID for the kit repository.
        pipeline_id: The specific pipeline ID to download artifacts from.
        platform: The platform identifier (e.g., 'linux-x86_64', 'windows-x86_64', 'linux-aarch64').
        config: The build configuration ('release' or 'debug').
        output_path: The path where the artifacts zip file will be saved. Defaults to 'artifacts.zip'.
        gitlab_url: The base URL of the GitLab instance. Defaults to 'https://gitlab-master.nvidia.com'.

    Returns:
        True if the download was successful, False if no matching job was found.

    Raises:
        ValueError: If CI_GITLAB_API_TOKEN environment variable is not set.
        requests.HTTPError: If any API request fails.
    """
    private_token = os.getenv("CI_GITLAB_API_TOKEN")

    if private_token is None:
        raise ValueError("Unable to find PRIVATE_TOKEN, please set CI_GITLAB_API_TOKEN environment variable")

    headers = {
        "PRIVATE-TOKEN": private_token
    }

    print(f"Searching pipeline {pipeline_id} for kit build job...")

    found, target_job = find_kit_build_job_in_pipeline(platform, config, gitlab_url, project_id, pipeline_id, headers)

    if not found or target_job is None:
        print(f"Found no matching job for config '{config}' and platform '{platform}' in pipeline {pipeline_id}")
        return False

    job_name = target_job["name"]
    job_web_url = target_job["web_url"]
    job_id = target_job["id"]

    print(f"Found kit {job_name} {job_web_url} proceeding to download...")

    # Download the artifacts
    artifacts_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts"
    response = requests.get(artifacts_url, headers=headers, stream=True, timeout=300)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("Download complete")
    return True
