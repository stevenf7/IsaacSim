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


BUILD_JOB_NAMES = [
    "kit-build-release-linux-x86_64", 
    "kit-build-debug-linux-x86_64", 
    "kit-build-release-windows-x86_64", 
    "kit-build-debug-windows-x86_64", 
    "kit-build-release-linux-aarch64", 
    "kit-build-debug-linux-aarch64"
]

def find_latest_nightly_pipeline_id(project_id=6510, gitlab_url="https://gitlab-master.nvidia.com"):
    """Find the latest successful nightly pipeline ID from GitLab.

    Queries GitLab API for scheduled pipelines on master branch and finds the most
    recent one where all required kit build jobs have completed successfully.

    Args:
        project_id: The GitLab project ID to query. Defaults to 6510.
        gitlab_url: The base URL of the GitLab instance. Defaults to 'https://gitlab-master.nvidia.com'.

    Returns:
        The pipeline ID of the latest successful nightly build, or None if no suitable pipeline found.

    Raises:
        ValueError: If CI_GITLAB_API_TOKEN environment variable is not set.
        requests.HTTPError: If any API request fails.
    """
    print("Querying for latest nightly pipeline...")
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("Unable to find PRIVATE_TOKEN, please set CI_GITLAB_API_TOKEN environment variable")
    
    headers = {
        "PRIVATE-TOKEN": private_token
    }
    
    pipelines_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines?source=schedule&ref=master"
    response = requests.get(pipelines_url, headers=headers, timeout=30)
    response.raise_for_status()
    pipelines = response.json()
    if len(pipelines) == 0:
        return None
    print(f"Found {len(pipelines)} top level nightly pipelines")
    # We now have a list of the top level nightly pipelines, next we need to make sure the kit sub pipeline is done
    for pipeline in pipelines:
        # Next we need to get the details for this pipeline
        pipeline_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline['id']}"
        response = requests.get(pipeline_url, headers=headers, timeout=30)
        response.raise_for_status()
        pipeline_details = response.json()
        for child_pipeline in pipeline_details.get("triggered_pipelines", []):
            build_job_count = 0
            page = 1
            while True:
                child_pipeline_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{child_pipeline['id']}/jobs?per_page=100&page={page}"
                response = requests.get(child_pipeline_url, headers=headers, timeout=30)
                response.raise_for_status()
                child_pipeline_details = response.json()
                if not child_pipeline_details:
                    break
                for job in child_pipeline_details:
                    if job['name'] in BUILD_JOB_NAMES and job['status'] == 'success':
                        build_job_count += 1
                page += 1
            if build_job_count == len(BUILD_JOB_NAMES):
                print(f"Found latest nightly pipeline {child_pipeline['id']}")
                return child_pipeline['id']
    return None

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
