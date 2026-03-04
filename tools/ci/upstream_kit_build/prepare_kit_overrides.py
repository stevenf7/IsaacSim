"""Prepare packman overrides from upstream Kit artifacts (no build).

This script downloads Kit build artifacts from an upstream GitLab pipeline,
extracts them, and writes packman .user files so that a subsequent Isaac Sim
build uses those Kit packages instead of CDN versions.

It overrides ALL pinned Kit packages to use those from the upstream pipeline:
  1. Kit SDK — extracted from omniverse-kit 7z (from kit-build-* job artifacts),
     overridden via kit-sdk.packman.xml.user
  2. Kit deps (generic-model-output, sensor-checker) — extracted from
     rendering/_builtpackages in the RTX build job artifacts (rtx-build-*),
     overridden via isaac-sim.packman.xml.user with <source path> elements

Can be run as a repo tool (repo prepare_kit_overrides) with:
  --pipeline-id ID   Use this GitLab pipeline (or set UPSTREAM_PIPELINE_ID in env).
  --branch NAME      Find latest nightly pipeline on this branch and use it.
  --kit-path PATH    Use existing kit artifacts at PATH (kit/kit/_builtpackages layout).
  --platform         linux-x86_64 | linux-aarch64 | windows-x86_64 (default: linux-x86_64).
  --config           release | debug (default: release).

Environment (when not passed as args): CI_JOB_NAME, UPSTREAM_PIPELINE_ID, CI_GITLAB_API_TOKEN.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
from typing import Callable, Dict

from omni.repo.ci import resolve_tokens
from omni.repo.man import extract_archive_to_folder

from tools.ci.upstream_kit_build.pull_kit import (
    download_kit_artifacts,
    fetch_rtx_kit_dep_packages,
    find_latest_nightly_pipeline_id,
)

# Kit-related packages in isaac-sim.packman.xml that are versioned with the
# Kit commit and must be overridden when building against an upstream Kit.
KIT_DEP_PACKAGES: dict[str, str] = {
    "generic-model-output": "generic_model_output",
    "sensor-checker": "sensor_checker",
}


def _platform_from_name(platform: str) -> tuple[str, str]:
    """Return (platform_target, platform) for packman and job names."""
    if platform == "windows-x86_64":
        return "windows-x86_64", "windows-x86_64"
    if platform == "linux-aarch64":
        return "manylinux_2_35_aarch64", "linux-aarch64"
    return "manylinux_2_35_x86_64", "linux-x86_64"


def extract_kit_dep_packages(
    builtpackages_dir: str,
    output_base_dir: str,
    platform_target: str,
    build_config: str,
) -> dict[str, str]:
    """Extract Kit dependency packages from the Kit build artifacts."""
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
) -> None:
    """Generate isaac-sim.packman.xml.user with source-path overrides."""
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
    print(f"[prepare_kit_overrides] Generated {output_path} with source-path overrides for: {overridden}")


def _run(
    pipeline_id: str | None,
    kit_path: str | None,
    platform: str,
    build_config: str,
    project_id: int,
    gitlab_url: str,
) -> None:
    platform_target, _ = _platform_from_name(platform)
    root = resolve_tokens("${root}")
    if not root or root == "None":
        root = os.getcwd()
    root = os.path.abspath(root)
    kit_deps_dir = os.path.join(root, "_kit_deps")

    if kit_path is not None:
        # Use existing kit artifacts at path (no download, no RTX deps)
        builtpackages_dir = os.path.join(os.path.abspath(kit_path), "kit", "kit", "_builtpackages")
        if not os.path.isdir(builtpackages_dir):
            raise ValueError(f"Kit path must contain kit/kit/_builtpackages; not found at {builtpackages_dir}")
        work_dir = root
        cleanup_kit = False
    else:
        if not pipeline_id:
            raise ValueError("Provide one of: --pipeline-id, --branch, or set UPSTREAM_PIPELINE_ID")
        work_dir = root
        kit_dir = os.path.join(work_dir, "kit")
        os.makedirs(kit_dir, exist_ok=True)
        artifacts_path = os.path.join(kit_dir, "artifacts.zip")
        success = download_kit_artifacts(
            project_id=project_id,
            pipeline_id=pipeline_id,
            platform=platform,
            config=build_config,
            output_path=artifacts_path,
            gitlab_url=gitlab_url,
        )
        if not success:
            raise RuntimeError(f"Failed to download kit artifacts for platform={platform}, config={build_config}")
        extract_archive_to_folder(artifacts_path, os.path.join(work_dir, "kit"))
        builtpackages_dir = os.path.join(work_dir, "kit", "kit", "_builtpackages")
        cleanup_kit = True

    print(
        f"[prepare_kit_overrides] build_config={build_config}, platform={platform}, platform_target={platform_target}"
    )

    # --- 1. Kit SDK override ---
    if os.path.exists("_kit"):
        shutil.rmtree("_kit")
    os.makedirs("_kit")
    all_builtpackages = glob.glob(f"{builtpackages_dir}/*")
    print(f"[prepare_kit_overrides] Built packages in artifacts ({len(all_builtpackages)}):")
    for p in sorted(all_builtpackages):
        print(f"  {os.path.basename(p)}")
    kit_7z = glob.glob(f"{builtpackages_dir}/omniverse-kit*{platform_target}*{build_config}*.7z")
    if len(kit_7z) != 1:
        raise ValueError(f"Expected 1 kit 7z file, got {len(kit_7z)}")
    print(f"[prepare_kit_overrides] Extracting Kit SDK: {os.path.basename(kit_7z[0])}")
    extract_archive_to_folder(kit_7z[0], "_kit")
    kit_sdk_user_path = os.path.join(root, "deps", "kit-sdk.packman.xml.user")
    with open(os.path.join(root, "tools", "ci", "upstream_kit_build", "kit-sdk.packman.xml.user"), "r") as f:
        content = f.read()
    content = content.replace("${config}", build_config).replace("${platform}", platform)
    with open(kit_sdk_user_path, "w") as f:
        f.write(content)
    print(f"[prepare_kit_overrides] Generated {kit_sdk_user_path}")

    # --- 2. Kit dep packages (RTX) override ---
    if os.path.exists(kit_deps_dir):
        shutil.rmtree(kit_deps_dir)
    os.makedirs(kit_deps_dir, exist_ok=True)
    extracted = {}
    if pipeline_id:
        extracted = fetch_rtx_kit_dep_packages(
            project_id=project_id,
            pipeline_id=pipeline_id,
            platform=platform,
            build_config=build_config,
            output_base_dir=kit_deps_dir,
            gitlab_url=gitlab_url,
        )
    else:
        print("[prepare_kit_overrides] No pipeline ID; skipping RTX Kit dep overrides")
    if extracted:
        generate_isaac_sim_packman_user(
            isaac_sim_xml_path=os.path.join(root, "deps", "isaac-sim.packman.xml"),
            output_path=os.path.join(root, "deps", "isaac-sim.packman.xml.user"),
            extracted_packages=extracted,
            kit_deps_rel_prefix="../_kit_deps",
        )
    else:
        print("[prepare_kit_overrides] No Kit dep packages found; skipping isaac-sim overrides")

    if cleanup_kit and os.path.exists("kit"):
        print("[prepare_kit_overrides] Cleaning up kit/ directory")
        shutil.rmtree("kit")
    print("[prepare_kit_overrides] Done — Kit SDK at _kit/, Kit deps at _kit_deps/")


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Prepare packman overrides from upstream Kit artifacts (download or use existing)."
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--pipeline-id",
        dest="pipeline_id",
        type=str,
        default=None,
        help="GitLab pipeline ID to download Kit artifacts from (or set UPSTREAM_PIPELINE_ID).",
    )
    group.add_argument(
        "--branch",
        dest="branch",
        type=str,
        default=None,
        help="Branch name: find latest nightly pipeline on this branch and use it.",
    )
    group.add_argument(
        "--kit-path",
        dest="kit_path",
        type=str,
        default=None,
        help="Path to existing kit artifacts (directory containing kit/kit/_builtpackages). Skips download and RTX deps.",
    )
    parser.add_argument(
        "--platform",
        dest="platform",
        type=str,
        default="linux-x86_64",
        choices=("linux-x86_64", "linux-aarch64", "windows-x86_64"),
        help="Target platform (default: linux-x86_64).",
    )
    parser.add_argument(
        "--config",
        dest="config",
        type=str,
        default="release",
        choices=("release", "debug"),
        help="Build config (default: release).",
    )

    def run_repo_tool(options: argparse.Namespace, config: Dict) -> None:
        tool_config = config.get("prepare_kit_overrides", {})
        project_id = int(tool_config.get("project_id", 6510))
        gitlab_url = str(tool_config.get("gitlab_url", "https://gitlab-master.nvidia.com"))

        pipeline_id = getattr(options, "pipeline_id", None)
        branch = getattr(options, "branch", None)
        kit_path = getattr(options, "kit_path", None)
        platform = getattr(options, "platform", "linux-x86_64")
        build_config = getattr(options, "config", "release")

        if pipeline_id is None and branch is None and kit_path is None:
            pipeline_id = os.getenv("UPSTREAM_PIPELINE_ID")
        if pipeline_id is None and branch is not None:
            nightly_id = find_latest_nightly_pipeline_id(branch=branch)
            if nightly_id is None:
                raise ValueError(f"Unable to find latest nightly pipeline on branch {branch!r}")
            pipeline_id = str(nightly_id)
            print(f"[prepare_kit_overrides] Using nightly pipeline {pipeline_id} for branch {branch!r}")

        _run(
            pipeline_id=pipeline_id,
            kit_path=kit_path,
            platform=platform,
            build_config=build_config,
            project_id=project_id,
            gitlab_url=gitlab_url,
        )

    return run_repo_tool


if __name__ == "__main__":
    # Allow direct run (e.g. from CI or for testing) using env and minimal args
    parser = argparse.ArgumentParser()
    run = setup_repo_tool(parser, {})
    args = parser.parse_args()
    run(args, {})
