"""Build Isaac Sim from upstream Kit artifacts.

This script downloads Kit build artifacts from an upstream GitLab pipeline,
extracts them, and prepares the environment for building Isaac Sim.

Environment Variables:
    CI_JOB_NAME: The CI job name used to determine platform and build configuration.
    UPSTREAM_PIPELINE_ID: The GitLab pipeline ID to download Kit artifacts from (required).
    CI_GITLAB_API_TOKEN: GitLab API token for authentication (required).
"""
import os
import glob
import shutil

from omni.repo.man import extract_archive_to_folder
from omni.repo.ci import resolve_tokens

from tools.ci.upstream_kit_build.pull_kit import download_kit_artifacts

# Determine build configuration and platform from CI job name
job_name = os.getenv("CI_JOB_NAME", "")

# Parse build configuration: release or debug
build_config = "release" if "-release" in job_name else "debug"

# Parse platform and determine the corresponding packman platform target
if "linux-aarch64" in job_name:
    platform_target = "manylinux_2_35_aarch64"
    platform = "linux-aarch64"
elif "windows-x86_64" in job_name:
    platform_target = "windows-x86_64"
    platform = "windows-x86_64"
else:
    # Default to linux-x86_64
    platform_target = "manylinux_2_35_x86_64"
    platform = "linux-x86_64"

# Kit project configuration
project_id = 6510  # GitLab project ID for the Kit repository
pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID")

if pipeline_id is None:
    raise ValueError("UPSTREAM_PIPELINE_ID environment variable is not set")

# Create kit folder if it doesn't exist
if not os.path.exists("kit"):
    os.makedirs("kit")

# Download Kit artifacts from the upstream pipeline
artifacts_path = "kit/artifacts.zip"
success = download_kit_artifacts(
    project_id=project_id,
    pipeline_id=pipeline_id,
    platform=platform,
    config=build_config,
    output_path=artifacts_path
)

if not success:
    raise RuntimeError(f"Failed to download kit artifacts for platform={platform}, config={build_config}")

print(f"Successfully downloaded kit artifacts to {artifacts_path}")

# Extract the downloaded artifacts
extract_archive_to_folder(artifacts_path, "kit")


# Prepare the _kit directory for Kit SDK extraction
if os.path.exists("_kit"):
    shutil.rmtree("_kit")

os.mkdir("_kit")

# Find the Kit SDK 7z archive matching the platform and configuration
kit_7z = glob.glob(f"kit/kit/_builtpackages/omniverse-kit*{platform_target}*{build_config}*.7z")
if len(kit_7z) != 1:
    raise ValueError(f"Expected 1 kit 7z file, got {len(kit_7z)}")

# Extract the Kit SDK archive
extract_archive_to_folder(kit_7z[0], "_kit")

# Configure the kit-sdk.packman.xml.user file with the correct platform and config
with open(resolve_tokens("${root}/tools/ci/upstream_kit_build/kit-sdk.packman.xml.user"), "r") as f:
    content = f.read()

# Replace template variables with actual values
content = content.replace("${config}", build_config)
content = content.replace("${platform}", platform)

# Write the configured file to the deps directory
with open(resolve_tokens("${root}/deps/kit-sdk.packman.xml.user"), "w") as f:
    f.write(content)

