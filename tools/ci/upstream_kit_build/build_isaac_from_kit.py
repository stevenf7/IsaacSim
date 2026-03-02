"""Build Isaac Sim from upstream Kit artifacts.

This script downloads Kit build artifacts from an upstream GitLab pipeline,
extracts them, and prepares the environment for building Isaac Sim.

It overrides ALL pinned Kit packages to use those from the upstream pipeline:
  1. Kit SDK — extracted from omniverse-kit 7z (from kit-build-* job artifacts),
     overridden via kit-sdk.packman.xml.user
  2. Kit deps (generic-model-output, sensor-checker) — extracted from
     rendering/_buildpackages in the RTX build job artifacts (rtx-build-*),
     overridden via isaac-sim.packman.xml.user with <source path> elements

This ensures every Kit-related package comes from the same upstream commit, so
the build faithfully tests whether a new Kit commit breaks Isaac Sim.

Environment Variables:
    CI_JOB_NAME: The CI job name used to determine platform and build configuration.
    UPSTREAM_PIPELINE_ID: The GitLab pipeline ID to download Kit artifacts from (required).
    CI_GITLAB_API_TOKEN: GitLab API token for authentication (required).
"""

import glob
import os
import re
import shutil

from omni.repo.ci import resolve_tokens
from omni.repo.man import extract_archive_to_folder

from tools.ci.upstream_kit_build.pull_kit import download_kit_artifacts, fetch_rtx_kit_dep_packages

# Kit-related packages in isaac-sim.packman.xml that are versioned with the
# Kit commit and must be overridden when building against an upstream Kit.
# Maps packman package name -> local extraction directory name.
KIT_DEP_PACKAGES: dict[str, str] = {
    "generic-model-output": "generic_model_output",
    "sensor-checker": "sensor_checker",
}


def extract_kit_dep_packages(
    builtpackages_dir: str,
    output_base_dir: str,
    platform_target: str,
    build_config: str,
) -> dict[str, str]:
    """Extract Kit dependency packages from the Kit build artifacts.

    Searches for zip archives matching each package in KIT_DEP_PACKAGES and
    extracts them to local directories under output_base_dir.

    Returns:
        Dict mapping package name to the extracted directory path.
    """
    extracted = {}

    for package_name, dir_name in KIT_DEP_PACKAGES.items():
        pattern = f"{builtpackages_dir}/{package_name}*{platform_target}*{build_config}*.zip"
        matches = glob.glob(pattern)

        if len(matches) != 1:
            print(f"Warning: expected 1 archive for '{package_name}', found {len(matches)}: {matches}")
            continue

        output_dir = os.path.join(output_base_dir, dir_name)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        extract_archive_to_folder(matches[0], output_dir)
        extracted[package_name] = output_dir
        print(f"Extracted {os.path.basename(matches[0])} -> {output_dir}")

    return extracted


def generate_isaac_sim_packman_user(
    isaac_sim_xml_path: str,
    output_path: str,
    extracted_packages: dict[str, str],
    kit_deps_rel_prefix: str,
):
    """Generate isaac-sim.packman.xml.user with source-path overrides.

    Reads the original isaac-sim.packman.xml and replaces <package> elements
    for each extracted Kit dep with <source path> elements pointing to the
    locally extracted directories. All other dependencies are preserved as-is.

    Args:
        isaac_sim_xml_path: Path to the original isaac-sim.packman.xml.
        output_path: Where to write the .user file.
        extracted_packages: Dict mapping package name -> extracted dir path.
        kit_deps_rel_prefix: Relative path prefix from deps/ to the extraction
            base dir (e.g. "../_kit_deps").
    """
    with open(isaac_sim_xml_path, "r") as f:
        content = f.read()

    for package_name, dir_name in KIT_DEP_PACKAGES.items():
        if package_name not in extracted_packages:
            continue
        source_path = f"{kit_deps_rel_prefix}/{KIT_DEP_PACKAGES[package_name]}/"
        content = re.sub(
            rf'<package\s+name="{re.escape(package_name)}"\s+version="[^"]+"\s*/>',
            f'<source path="{source_path}" />',
            content,
        )

    with open(output_path, "w") as f:
        f.write(content)

    overridden = [name for name in KIT_DEP_PACKAGES if name in extracted_packages]
    print(f"[build_isaac_from_kit] Generated {output_path} with source-path overrides for: {overridden}")
    print(f"[build_isaac_from_kit] isaac-sim.packman.xml.user content:\n{content}")


# Determine build configuration and platform from CI job name
job_name = os.getenv("CI_JOB_NAME", "")

# Parse build configuration: release or debug
build_config = "debug" if "-debug" in job_name else "release"

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

print(f"[build_isaac_from_kit] CI_JOB_NAME={job_name}")
print(f"[build_isaac_from_kit] build_config={build_config}, platform={platform}, platform_target={platform_target}")
print(f"[build_isaac_from_kit] UPSTREAM_PIPELINE_ID={pipeline_id}")

if pipeline_id is None:
    raise ValueError("UPSTREAM_PIPELINE_ID environment variable is not set")

# Create kit folder if it doesn't exist
if not os.path.exists("kit"):
    os.makedirs("kit")

# Download Kit artifacts from the upstream pipeline
artifacts_path = "kit/artifacts.zip"
success = download_kit_artifacts(
    project_id=project_id, pipeline_id=pipeline_id, platform=platform, config=build_config, output_path=artifacts_path
)

if not success:
    raise RuntimeError(f"Failed to download kit artifacts for platform={platform}, config={build_config}")

print(f"Successfully downloaded kit artifacts to {artifacts_path}")

# Extract the downloaded artifacts
extract_archive_to_folder(artifacts_path, "kit")

builtpackages_dir = "kit/kit/_builtpackages"

# --- 1. Kit SDK override (kit-sdk.packman.xml.user) ---

# Prepare the _kit directory for Kit SDK extraction
if os.path.exists("_kit"):
    shutil.rmtree("_kit")

os.mkdir("_kit")

# List all built packages for debugging
all_builtpackages = glob.glob(f"{builtpackages_dir}/*")
print(f"[build_isaac_from_kit] Built packages in artifacts ({len(all_builtpackages)}):")
for p in sorted(all_builtpackages):
    print(f"  {os.path.basename(p)}")

# Find the Kit SDK 7z archive matching the platform and configuration
kit_7z = glob.glob(f"{builtpackages_dir}/omniverse-kit*{platform_target}*{build_config}*.7z")
if len(kit_7z) != 1:
    raise ValueError(f"Expected 1 kit 7z file, got {len(kit_7z)}")

# Extract the Kit SDK archive
print(f"[build_isaac_from_kit] Extracting Kit SDK: {os.path.basename(kit_7z[0])}")
extract_archive_to_folder(kit_7z[0], "_kit")

# Configure the kit-sdk.packman.xml.user file with the correct platform and config
with open(resolve_tokens("${root}/tools/ci/upstream_kit_build/kit-sdk.packman.xml.user"), "r") as f:
    content = f.read()

# Replace template variables with actual values
content = content.replace("${config}", build_config)
content = content.replace("${platform}", platform)

# Write the configured file to the deps directory
kit_sdk_user_path = resolve_tokens("${root}/deps/kit-sdk.packman.xml.user")
with open(kit_sdk_user_path, "w") as f:
    f.write(content)
print(f"[build_isaac_from_kit] Generated {kit_sdk_user_path}")
print(f"[build_isaac_from_kit] kit-sdk.packman.xml.user content:\n{content}")

# --- 2. Kit dep packages override (isaac-sim.packman.xml.user) ---
# Fetch generic-model-output and sensor-checker from RTX job via +latest.txt and
# single-file zip download (no full artifact download).

kit_deps_dir = "_kit_deps"
if os.path.exists(kit_deps_dir):
    shutil.rmtree(kit_deps_dir)
os.makedirs(kit_deps_dir, exist_ok=True)
extracted = fetch_rtx_kit_dep_packages(
    project_id=project_id,
    pipeline_id=pipeline_id,
    platform=platform,
    build_config=build_config,
    output_base_dir=kit_deps_dir,
)

if extracted:
    isaac_sim_xml = resolve_tokens("${root}/deps/isaac-sim.packman.xml")
    isaac_sim_user = resolve_tokens("${root}/deps/isaac-sim.packman.xml.user")
    generate_isaac_sim_packman_user(
        isaac_sim_xml_path=isaac_sim_xml,
        output_path=isaac_sim_user,
        extracted_packages=extracted,
        kit_deps_rel_prefix=f"../{kit_deps_dir}",
    )
else:
    print("[build_isaac_from_kit] Warning: no Kit dep packages found in artifacts, skipping isaac-sim overrides")

# Do a bit of cleanup at the end here
print("[build_isaac_from_kit] Cleaning up kit/ directory")
shutil.rmtree("kit")
print("[build_isaac_from_kit] Done — Kit SDK at _kit/, Kit deps at _kit_deps/")
