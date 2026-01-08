# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import argparse
import os
import sys
from typing import Callable, Dict


import omni.repo.ci
from tools.ci.upstream_kit_build.pull_kit import find_latest_nightly_pipeline_id


def pull_library_from_linbuild_usr_lib64(d: str, name: str):
    # Hack to be able to link to libasan.
    # Our toolchain is using an older version of GCC that can't statically link ASAN, so we need
    # to pull the library out of docker
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "build", "--fetch", "-rd"])
    omni.repo.ci.launch(["_build/host-deps/linbuild/linbuild.sh", "--", "cp", f"/usr/lib64/{name}", d])


def main(args: argparse.Namespace):


    downstream_pipeline = os.getenv("CI_PIPELINE_SOURCE","") == "pipeline"

    develop_kit_tot_pipeline = (
        os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "") == "develop-kit-tot" or 
        os.getenv("CI_COMMIT_REF_NAME", "") == "develop-kit-tot"
    )

    if develop_kit_tot_pipeline:
        nightly_pipeline_id = find_latest_nightly_pipeline_id()
        if nightly_pipeline_id is None:
            raise ValueError("Unable to find latest nightly pipeline")
        os.environ["UPSTREAM_PIPELINE_ID"] = str(nightly_pipeline_id)


    if downstream_pipeline or develop_kit_tot_pipeline:
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "ci", "build_isaac_from_kit"])



    build_config = args.build_config

    extra_flags = []
    if build_config == "release":
        extra_flags.append("-r")
    elif build_config == "debug":
        extra_flags.append("-d")
    if not omni.repo.ci.is_windows():
        extra_flags.append("--no-docker")

    build_cmd = ["${root}/repo${shell_ext}", "build", "-x"] + extra_flags

    # Full rebuild config
    omni.repo.ci.launch(build_cmd)

    # Generate symlinks, currently it breaks python
    # if sys.platform == "linux":
    #     omni.repo.ci.launch(
    #         ["rdfind", "-followsymlinks", "true", "-makesymlinks", "true", f"_build/linux-x86_64/{build_config}/"],
    #         warning_only=True,
    #     )

    # Use repo_docs.enabled as indicator for whether to build docs
    repo_docs_enabled = omni.repo.ci.get_repo_config().get("repo_docs", {}).get("enabled", True)
    # repo_docs_enabled = repo_docs_enabled and omni.repo.ci.is_windows()

    # We don't need to build docs for windows release builds
    if omni.repo.ci.is_windows() and build_config == "release":
        repo_docs_enabled = False

    # We don't need to build docs for debug builds
    if build_config == "debug":
        repo_docs_enabled = False


    if downstream_pipeline:
        repo_docs_enabled = False
        print("Docs are disabled for downstream pipeline")

    # Docs
    if repo_docs_enabled:
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "extension_toc"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "extension_docs"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "examples_list"])
        # Temporarily ignore warnings in docs build
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--config", build_config, "--warn-as-error=0"])
        # omni.repo.ci.launch(["${root}/repo${shell_ext}", "docs", "--config", build_config])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "package", "-m", "docs", "-c", build_config])

    # store the debugging symbols for release builds only.
    if build_config == "release":
        # For CICD builds against protected branches only set the TTL to 30 days
        if os.getenv("CI_COMMIT_REF_PROTECTED") == "true":
            omni.repo.ci.launch(["${root}/repo${shell_ext}", "symstore", "--ttl-seconds", "259200"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "symstore", "--process-mrs"], warning_only=True)



    # Package release
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "package", "-m", "isaac-sim-standalone", "-c", build_config])
