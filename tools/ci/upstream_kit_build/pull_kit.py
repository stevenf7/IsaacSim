# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import tempfile
from urllib.parse import quote
from xml.etree import ElementTree

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

# Fallback when rtx-build-{platform} is not present: job that produces rendering_deps.xml.
RTX_PLUGINS_LOOKUP_JOB_PREFIX = "kit-rtx-plugins-lookup-"
RENDERING_DEPS_ARTIFACT_PATH = "kit/_build/rendering_deps.xml"

# The Kit branch that Isaac Sim depends on.  Used by the nightly fallback
# to find the latest scheduled pipeline with all build jobs passing.
KIT_BRANCH = "feature/110.1"


def _gitlab_headers() -> dict:
    """Return GitLab API auth headers. CI_GITLAB_API_TOKEN preferred, then GITLAB_API_TOKEN."""
    token = os.getenv("CI_GITLAB_API_TOKEN") or os.getenv("GITLAB_API_TOKEN")
    if not token:
        raise ValueError("GitLab API token required. Set CI_GITLAB_API_TOKEN or GITLAB_API_TOKEN.")
    return {"PRIVATE-TOKEN": token}


def find_latest_nightly_pipeline_id(
    project_id=6510,
    gitlab_url="https://gitlab-master.nvidia.com",
    branch=None,
):
    """Find the latest successful nightly pipeline ID from GitLab.

    Queries GitLab API for scheduled pipelines on the given branch and finds the
    most recent one where all required kit build jobs and RTX build jobs have
    completed successfully (so Kit dep packages from RTX artifacts are available).

    Args:
        project_id: The GitLab project ID to query. Defaults to 6510.
        gitlab_url: The base URL of the GitLab instance. Defaults to 'https://gitlab-master.nvidia.com'.
        branch: Branch name to query (e.g. feature/110.0). Defaults to KIT_BRANCH.

    Returns:
        The pipeline ID of the latest successful nightly build, or None if no suitable pipeline found.

    Raises:
        ValueError: If CI_GITLAB_API_TOKEN and GITLAB_API_TOKEN environment variables are not set.
        requests.HTTPError: If any API request fails.
    """
    ref = branch if branch is not None else KIT_BRANCH
    print(f"Querying for latest nightly pipeline on {ref}...")
    headers = _gitlab_headers()

    pipelines_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines?source=schedule&ref={ref}"
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
    headers = _gitlab_headers()

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
    headers = _gitlab_headers()

    encoded_path = quote(artifact_path, safe="/")
    url = f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts/{encoded_path}"
    resp = requests.get(url, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True


def _platform_to_packman_target(platform: str) -> str:
    """Map platform (linux-x86_64, linux-aarch64, windows-x86_64) to packman platform string."""
    if platform == "windows-x86_64":
        return "windows-x86_64"
    if platform == "linux-aarch64":
        return "manylinux_2_35_aarch64"
    return "manylinux_2_35_x86_64"


def _tweak_rendering_deps_xml(xml_content: str, build_config: str) -> str:
    """Tweak the artifact XML: drop the dependency we do not need, add linkPath to the rest.

    Removes the release dependency when doing a debug build and vice versa.
    Sets linkPath="rtx_plugins" on the remaining dependency so packman extracts there.
    """
    root = ElementTree.fromstring(xml_content)
    # Match ".release." (old format) or ".release_" (new format with underscore separator).
    config_marker = f".{build_config}"
    for dep in list(root.findall("dependency")):
        dep_name = dep.get("name") or ""
        if config_marker not in dep_name:
            root.remove(dep)
        else:
            dep.set("linkPath", "rtx_plugins")
    return ElementTree.tostring(root, encoding="unicode", default_namespace="")


def fetch_rendering_deps_from_lookup_job(
    project_id,
    pipeline_id,
    platform,
    gitlab_url="https://gitlab-master.nvidia.com",
) -> tuple[bool, str | None]:
    """Fallback when rtx-build-{platform} is missing: use kit-rtx-plugins-lookup-{platform}.

    Finds the lookup job, downloads kit/_build/rendering_deps.xml from its artifacts.

    Returns:
        (True, XML content string) on success, (False, None) if job or file missing.
    """
    lookup_job_name = f"{RTX_PLUGINS_LOOKUP_JOB_PREFIX}{platform}"
    headers = _gitlab_headers()

    found, target_job = find_job_in_pipeline(gitlab_url, project_id, pipeline_id, lookup_job_name, headers)
    if not found or target_job is None:
        return False, None

    job_id = target_job["id"]
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        download_job_artifact_file(project_id, job_id, RENDERING_DEPS_ARTIFACT_PATH, tmp_path, gitlab_url)
        with open(tmp_path, "r") as f:
            xml_content = f.read()
        print(f"[pull_kit] Fallback: got rendering_deps.xml from {lookup_job_name}")
        return True, xml_content
    except (requests.HTTPError, OSError) as e:
        print(f"[pull_kit] Fallback: failed to get rendering_deps.xml: {e}")
        return False, None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# Folder names under rtx_plugins/_build/{platform}/{config}/libs/ we map to our packages.
RTX_LIBS_SUBDIR_TO_PACKAGE = {
    "sensors-checker": "sensor-checker",
    "sensors-gmo": "generic-model-output",
}

# Extra files that the published generic-model-output packman package bundles from
# rendering/source/include/ (see rendering/package.toml) but that the sensors-gmo
# build output does not contain.  Must be patched in when using the fallback path.
_GMO_EXTRA_INCLUDE_FILES = [
    "omni/sensors/cuda/CudaHelperDecl.h",
    "omni/sensors/cuda/CudaHelperMath.h",
    "omni/sensors/cuda/CudaHelperMem.h",
]


def _patch_gmo_extra_includes(
    gmo_dir: str,
    project_id,
    pipeline_id,
    gitlab_url: str,
) -> None:
    """Download CudaHelper headers missing from the sensors-gmo build output.

    The published generic-model-output packman package bundles extra headers from
    rendering/source/include/ (see rendering/package.toml ``CudaHelper**`` glob).
    The sensors-gmo directory under rtx_plugins.release does not include them,
    so builds that depend on GMOAuxiliaryData.h fail with a missing CudaHelperMem.h.
    """
    headers = _gitlab_headers()
    # Resolve the pipeline SHA for deterministic file downloads.
    try:
        resp = requests.get(
            f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        sha = resp.json()["sha"]
    except (requests.HTTPError, KeyError) as e:
        print(f"[pull_kit] Fallback: WARNING: could not resolve pipeline SHA: {e}")
        return

    include_dir = os.path.join(gmo_dir, "include")
    for rel_path in _GMO_EXTRA_INCLUDE_FILES:
        dst = os.path.join(include_dir, rel_path)
        if os.path.exists(dst):
            continue
        src_path = f"rendering/source/include/{rel_path}"
        encoded = quote(src_path, safe="")
        url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/files/{encoded}/raw?ref={sha}"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(resp.content)
            print(f"[pull_kit] Fallback: patched {rel_path} into GMO include dir")
        except requests.HTTPError as e:
            print(f"[pull_kit] Fallback: WARNING: failed to download {rel_path}: {e}")


def _fetch_rtx_deps_via_packman_lookup(
    rendering_deps_xml: str,
    build_config: str,
    platform: str,
    output_base_dir: str,
) -> dict[str, str]:
    """Use rendering_deps XML to run packman pull, then copy libs subdirs to match expected layout.

    Tweaks the artifact XML (drop other config, add linkPath), runs packmanapi.pull, then copies
    rtx_plugins/_build/library/{platform_target}/{config}/libs/... to output_base_dir.
    """
    import shutil

    import packmanapi

    packman_platform = _platform_to_packman_target(platform)
    try:
        xml_content = _tweak_rendering_deps_xml(rendering_deps_xml, build_config)
    except ElementTree.ParseError as e:
        print(f"[pull_kit] Fallback: failed to parse/tweak rendering_deps.xml: {e}")
        return {}
    if "<dependency " not in xml_content:
        print("[pull_kit] Fallback: no dependencies left after filtering for config")
        return {}

    xml_path = os.path.join(output_base_dir, "rendering_deps.packman.xml")
    with open(xml_path, "w") as f:
        f.write(xml_content)

    try:
        packmanapi.pull(
            project_path=xml_path,
            platform=packman_platform,
        )
    except Exception as e:
        print(f"[pull_kit] Fallback: packman pull failed: {e}")
        return {}

    rtx_plugins_dir = os.path.join(output_base_dir, "rtx_plugins")
    # Package internal layout may use either the short platform name (linux-x86_64, new) or
    # the packman/manylinux name (manylinux_2_35_x86_64, old).  Try both.
    libs_dir = os.path.join(rtx_plugins_dir, "_build", platform, build_config, "libs")
    if not os.path.isdir(libs_dir):
        libs_dir = os.path.join(rtx_plugins_dir, "_build", packman_platform, build_config, "libs")
    if not os.path.isdir(libs_dir):
        print(f"[pull_kit] Fallback: libs dir not found under _build/{platform} or _build/{packman_platform}")
        return {}

    extracted = {}
    for subdir in os.listdir(libs_dir):
        pkg_name = RTX_LIBS_SUBDIR_TO_PACKAGE.get(subdir)
        if pkg_name is None:
            continue
        dir_name = RTX_KIT_DEP_PACKAGES[pkg_name]
        src = os.path.join(libs_dir, subdir)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(output_base_dir, dir_name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        extracted[pkg_name] = dst
        print(f"[pull_kit] Fallback: copied {subdir} -> {dst}")

    return extracted


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

    headers = _gitlab_headers()

    version_content = get_kit_version_file_content(project_id, pipeline_id, gitlab_url)
    if not version_content:
        print("[pull_kit] Failed to get kit VERSION file content for RTX artifacts")
        return {}

    found, target_job = find_job_in_pipeline(gitlab_url, project_id, pipeline_id, f"rtx-build-{platform}", headers)
    if not found or target_job is None:
        print(f"[pull_kit] No rtx-build job for platform '{platform}', trying kit-rtx-plugins-lookup fallback...")
        ok, rendering_deps_xml = fetch_rendering_deps_from_lookup_job(project_id, pipeline_id, platform, gitlab_url)
        if ok and rendering_deps_xml is not None:
            extracted = _fetch_rtx_deps_via_packman_lookup(rendering_deps_xml, build_config, platform, output_base_dir)
            # The sensors-gmo build output is missing headers that the published
            # generic-model-output packman package bundles from rendering/source/include/.
            # Patch them in so downstream builds can find CudaHelperMem.h et al.
            if "generic-model-output" in extracted:
                _patch_gmo_extra_includes(extracted["generic-model-output"], project_id, pipeline_id, gitlab_url)
            return extracted
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
        ValueError: If CI_GITLAB_API_TOKEN or GITLAB_API_TOKEN environment variable is not set.
        requests.HTTPError: If any API request fails.
    """
    headers = _gitlab_headers()

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
