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
import tempfile
from urllib.parse import quote

import requests

# Path in the Kit repo for major.minor.patch (fetched at pipeline sha).
KIT_VERSION_PATH = "kit/VERSION"

BUILD_JOB_NAMES = [
    "kit-build-release-linux-x86_64",
    "kit-build-debug-linux-x86_64",
    "kit-build-release-windows-x86_64",
    "kit-build-debug-windows-x86_64",
    "kit-build-release-linux-aarch64",
    "kit-build-debug-linux-aarch64",
]

# RTX build jobs (no debug/release in job name; artifacts are in rendering/_builtpackages).
# Used to fetch generic-model-output and sensor-checker via +latest.txt and single-file API.
RTX_BUILD_JOB_NAMES = [
    "rtx-build-linux-x86_64",
    "rtx-build-linux-aarch64",
    "rtx-build-windows-x86_64",
]

# Kit dep packages fetched from RTX job (package name -> local dir name).
RTX_KIT_DEP_PACKAGES = {
    "generic-model-output": "generic_model_output",
    "sensor-checker": "sensor_checker",
}

# The Kit branch that Isaac Sim depends on.  Used by the nightly fallback
# to find the latest scheduled pipeline with all build jobs passing.
KIT_BRANCH = "feature/110.0"


def setup_kit_upstream() -> None:
    """Detect whether this build should use upstream Kit and set up accordingly.

    Decision matrix:
      1. Downstream trigger from Kit (CI_PIPELINE_SOURCE == "pipeline") with
         UPSTREAM_PIPELINE_ID already set → honor it directly.
      2. Running on the develop-kit-tot or kit-integration/* branch (post-merge push, scheduled, or
         MR targeting it) → fall back to the latest Kit nightly on KIT_BRANCH.
      3. Otherwise → skip Kit override entirely.

    When an upstream Kit pipeline is identified (case 1 or 2), this function
    launches ``build_isaac_from_kit`` which downloads Kit artifacts and
    generates packman ``.user`` overrides so all Kit packages come from the
    same commit.
    """
    import omni.repo.ci  # deferred so module can be imported outside CI

    ci_pipeline_source = os.getenv("CI_PIPELINE_SOURCE", "")
    ci_commit_ref = os.getenv("CI_COMMIT_REF_NAME", "")
    ci_mr_target = os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "")
    upstream_pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID", "")

    print(f"[setup_kit_upstream] CI_PIPELINE_SOURCE={ci_pipeline_source}")
    print(f"[setup_kit_upstream] CI_COMMIT_REF_NAME={ci_commit_ref}")
    print(f"[setup_kit_upstream] CI_MERGE_REQUEST_TARGET_BRANCH_NAME={ci_mr_target}")
    print(f"[setup_kit_upstream] UPSTREAM_PIPELINE_ID={upstream_pipeline_id}")

    downstream_pipeline = ci_pipeline_source == "pipeline"
    develop_kit_tot_pipeline = (
        ci_mr_target == "develop-kit-tot"
        or ci_commit_ref == "develop-kit-tot"
        or ci_commit_ref.startswith("kit-integration/")
        or ci_mr_target.startswith("kit-integration/")
    )

    # for kit-integration/* pipelines we override the KIT_BRANCH, just in case its a non-downstream kit-integration pipeline
    if ci_commit_ref.startswith("kit-integration/"):
        KIT_BRANCH = ci_commit_ref.split("/")[1]
    if ci_mr_target.startswith("kit-integration/"):
        KIT_BRANCH = ci_mr_target.split("/")[1]

    print(
        f"[setup_kit_upstream] downstream_pipeline={downstream_pipeline}, "
        f"develop_kit_tot_pipeline={develop_kit_tot_pipeline}"
    )

    if downstream_pipeline and upstream_pipeline_id:
        # Upstream pipeline already provided the pipeline ID — honour it.
        print(f"[setup_kit_upstream] Using upstream-provided UPSTREAM_PIPELINE_ID={upstream_pipeline_id}")
    elif develop_kit_tot_pipeline:
        # Fallback: find the latest Kit nightly on KIT_BRANCH.
        print(f"[setup_kit_upstream] No upstream pipeline ID, falling back to latest Kit nightly on {KIT_BRANCH}")
        nightly_pipeline_id = find_latest_nightly_pipeline_id()
        if nightly_pipeline_id is None:
            raise ValueError("Unable to find latest nightly pipeline")
        os.environ["UPSTREAM_PIPELINE_ID"] = str(nightly_pipeline_id)
        print(f"[setup_kit_upstream] Set UPSTREAM_PIPELINE_ID={nightly_pipeline_id} from nightly lookup")
    else:
        print(
            "[setup_kit_upstream] Not a downstream or develop-kit-tot/kit-integration pipeline, skipping Kit override"
        )
        return

    print("[setup_kit_upstream] Launching build_isaac_from_kit to override Kit packages...")
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "ci", "build_isaac_from_kit"])


def find_latest_nightly_pipeline_id(project_id=6510, gitlab_url="https://gitlab-master.nvidia.com"):
    """Find the latest successful nightly pipeline ID from GitLab.

    Queries GitLab API for scheduled pipelines on KIT_BRANCH and finds the
    most recent one where all required kit build jobs and RTX build jobs have
    completed successfully (so Kit dep packages from RTX artifacts are available).

    Args:
        project_id: The GitLab project ID to query. Defaults to 6510.
        gitlab_url: The base URL of the GitLab instance. Defaults to 'https://gitlab-master.nvidia.com'.

    Returns:
        The pipeline ID of the latest successful nightly build, or None if no suitable pipeline found.

    Raises:
        ValueError: If CI_GITLAB_API_TOKEN environment variable is not set.
        requests.HTTPError: If any API request fails.
    """
    print(f"Querying for latest nightly pipeline on {KIT_BRANCH}...")
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("Unable to find PRIVATE_TOKEN, please set CI_GITLAB_API_TOKEN environment variable")

    headers = {"PRIVATE-TOKEN": private_token}

    pipelines_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines?source=schedule&ref={KIT_BRANCH}"
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
            rtx_job_count = 0
            page = 1
            while True:
                child_pipeline_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{child_pipeline['id']}/jobs?per_page=100&page={page}"
                response = requests.get(child_pipeline_url, headers=headers, timeout=30)
                response.raise_for_status()
                child_pipeline_details = response.json()
                if not child_pipeline_details:
                    break
                for job in child_pipeline_details:
                    if job["status"] != "success":
                        continue
                    if job["name"] in BUILD_JOB_NAMES:
                        build_job_count += 1
                    elif job["name"] in RTX_BUILD_JOB_NAMES:
                        rtx_job_count += 1
                page += 1
            if build_job_count == len(BUILD_JOB_NAMES) and rtx_job_count == len(RTX_BUILD_JOB_NAMES):
                print(f"Found latest nightly pipeline {child_pipeline['id']}")
                return child_pipeline["id"]
    return None


def find_job_in_pipeline(
    gitlab_url,
    project_id,
    pipeline_id,
    expected_job_name,
    headers,
    status="success",
):
    """Search a GitLab pipeline for a job with the given name and status.

    Args:
        gitlab_url: The base URL of the GitLab instance.
        project_id: The GitLab project ID.
        pipeline_id: The pipeline ID to search.
        expected_job_name: The exact job name to find (e.g. 'kit-build-release-linux-x86_64', 'rtx-build-linux-x86_64').
        headers: Dictionary containing authentication headers with PRIVATE-TOKEN.
        status: Required job status. Defaults to 'success' to match current behavior.

    Returns:
        Tuple of (bool, dict or None): True if exactly one matching job was found,
        and the job dictionary if found, None otherwise.
    """
    for page in range(1, 4):
        jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs?per_page=100&page={page}"
        response = requests.get(jobs_url, headers=headers, timeout=30)
        response.raise_for_status()
        jobs = response.json()

        target_jobs = [job for job in jobs if job["name"] == expected_job_name and job["status"] == status]
        if len(target_jobs) == 1:
            return True, target_jobs[0]

    return False, None


def get_kit_version_file_content(project_id, pipeline_id, gitlab_url="https://gitlab-master.nvidia.com"):
    """Return the contents of kit/VERSION at the pipeline's commit (e.g. 110.1.0).

    Used to construct the path to +latest.txt files in the RTX job artifacts:
    rendering/_builtpackages/{package}@{version}+latest.txt

    Returns:
        First line of the VERSION file, stripped, or None if pipeline or fetch fails.
    """
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("CI_GITLAB_API_TOKEN is not set")
    headers = {"PRIVATE-TOKEN": private_token}

    pipeline_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
    resp = requests.get(pipeline_url, headers=headers, timeout=30)
    resp.raise_for_status()
    pipeline = resp.json()

    sha = pipeline.get("sha")
    if not sha:
        return None

    version_url = f"{gitlab_url}/omniverse/kit/-/raw/{sha}/{KIT_VERSION_PATH}"
    v_resp = requests.get(version_url, headers=headers, timeout=30)
    v_resp.raise_for_status()
    return v_resp.text.strip().split("\n")[0].strip() or None


def download_job_artifact_file(
    project_id,
    job_id,
    artifact_path,
    output_path,
    gitlab_url="https://gitlab-master.nvidia.com",
):
    """Download a single file from a job's artifacts (GitLab API by job ID).

    artifact_path is the path inside the archive (e.g. rendering/_builtpackages/foo+latest.txt).
    Special characters (e.g. +) are quoted for the URL.
    """
    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("CI_GITLAB_API_TOKEN is not set")
    headers = {"PRIVATE-TOKEN": private_token}

    encoded_path = quote(artifact_path, safe="/")
    url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts/{encoded_path}"
    resp = requests.get(url, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True


def fetch_rtx_kit_dep_packages(
    project_id,
    pipeline_id,
    platform,
    build_config,
    output_base_dir,
    gitlab_url="https://gitlab-master.nvidia.com",
):
    """Fetch generic-model-output and sensor-checker from RTX job via +latest.txt and single-file download.

    1. Get kit/VERSION file content at pipeline sha (e.g. 110.1.0).
    2. Find the RTX job for the platform.
    3. For each package: download rendering/_builtpackages/{package}@{version}+latest.txt,
       read the release filename, fix to release/debug per build_config, download that zip,
       extract to output_base_dir/{dir_name}.

    Returns:
        Dict mapping package name -> extracted directory path.
    """
    import shutil

    from omni.repo.man import extract_archive_to_folder

    private_token = os.getenv("CI_GITLAB_API_TOKEN")
    if private_token is None:
        raise ValueError("CI_GITLAB_API_TOKEN is not set")
    headers = {"PRIVATE-TOKEN": private_token}

    version_content = get_kit_version_file_content(project_id, pipeline_id, gitlab_url)
    if not version_content:
        print("[pull_kit] Failed to get kit VERSION file content for RTX artifacts")
        return {}

    found, target_job = find_job_in_pipeline(gitlab_url, project_id, pipeline_id, f"rtx-build-{platform}", headers)
    if not found or target_job is None:
        print(f"[pull_kit] No RTX job for platform '{platform}' in pipeline {pipeline_id}")
        return {}

    job_id = target_job["id"]
    print(f"[pull_kit] Using RTX job {target_job['name']} (id={job_id}), VERSION={version_content}")

    extracted = {}
    builtpackages_prefix = "rendering/_builtpackages"

    for package_name, dir_name in RTX_KIT_DEP_PACKAGES.items():
        latest_txt_path = f"{builtpackages_prefix}/{package_name}@{version_content}+latest.txt"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            download_job_artifact_file(project_id, job_id, latest_txt_path, tmp_path, gitlab_url)
        except requests.HTTPError as e:
            print(f"[pull_kit] Could not download {latest_txt_path}: {e}")
            continue
        try:
            with open(tmp_path, "r") as f:
                filename = f.read().strip().split("\n")[0].strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        if not filename:
            print(f"[pull_kit] Empty filename in {latest_txt_path}")
            continue

        if build_config == "release" and filename.endswith(".debug.zip"):
            filename = filename.replace(".debug.zip", ".release.zip")
        elif build_config == "debug" and filename.endswith(".release.zip"):
            filename = filename.replace(".release.zip", ".debug.zip")

        zip_artifact_path = f"{builtpackages_prefix}/{filename}"
        output_dir = os.path.join(output_base_dir, dir_name)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        zip_path = os.path.join(output_base_dir, f"_tmp_{dir_name}.zip")
        try:
            download_job_artifact_file(project_id, job_id, zip_artifact_path, zip_path, gitlab_url)
            extract_archive_to_folder(zip_path, output_dir)
            extracted[package_name] = output_dir
            print(f"[pull_kit] Extracted {filename} -> {output_dir}")
        except requests.HTTPError as e:
            print(f"[pull_kit] Could not download {zip_artifact_path}: {e}")
        finally:
            if os.path.exists(zip_path):
                try:
                    os.unlink(zip_path)
                except OSError:
                    pass

    return extracted


def download_kit_artifacts(
    project_id,
    pipeline_id,
    platform,
    config,
    output_path="artifacts.zip",
    gitlab_url="https://gitlab-master.nvidia.com",
):
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

    headers = {"PRIVATE-TOKEN": private_token}

    print(f"Searching pipeline {pipeline_id} for kit build job...")

    found, target_job = find_job_in_pipeline(
        gitlab_url, project_id, pipeline_id, f"kit-build-{config}-{platform}", headers
    )

    if not found or target_job is None:
        print(f"Found no matching job for config '{config}' and platform '{platform}' in pipeline {pipeline_id}")
        return False

    job_name = target_job["name"]
    job_web_url = target_job["web_url"]
    job_id = target_job["id"]
    artifacts_url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts"

    print(f"Found kit {job_name} {job_web_url} proceeding to download...")

    # Download the artifacts
    response = requests.get(artifacts_url, headers=headers, stream=True, timeout=300)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print("Download complete")
    return True
