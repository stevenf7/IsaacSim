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
import platform
import sys
from typing import Callable, Dict

import omni.repo.ci

from tools.ci.upstream_kit_build.arbitrate_kit_upstream import arbitrate_kit_upstream


def pull_library_from_linbuild_usr_lib64(d: str, name: str):
    # Hack to be able to link to libasan.
    # Our toolchain is using an older version of GCC that can't statically link ASAN, so we need
    # to pull the library out of docker
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "build", "--fetch", "-rd"])
    omni.repo.ci.launch(["_build/host-deps/linbuild/linbuild.sh", "--", "cp", f"/usr/lib64/{name}", d])


def main(args: argparse.Namespace):

    arbitrate_kit_upstream(build_config=args.build_config)
    omni.repo.ci.launch(["git", "lfs", "pull"])

    downstream_pipeline = os.getenv("CI_PIPELINE_SOURCE", "") == "pipeline"

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

    develop_kit_tot_pipeline = (
        os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "") == "develop-kit-tot"
        or os.getenv("CI_COMMIT_REF_NAME", "") == "develop-kit-tot"
        or os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "").startswith("kit-integration/")
        or os.getenv("CI_COMMIT_REF_NAME", "").startswith("kit-integration/")
    )

    if downstream_pipeline or develop_kit_tot_pipeline:
        repo_docs_enabled = False
        print("Docs are disabled for downstream/develop-kit-tot/kit-integration pipeline")

    # API docs only (user guide is built in a separate CI job)
    if repo_docs_enabled:
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "generate_doxygen_input"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "extension_toc"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "extension_docs"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "examples_list"])
        omni.repo.ci.launch(
            ["${root}/repo${shell_ext}", "docs", "--project", "api", "--config", build_config, "--warn-as-error=0"]
        )
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "package", "-m", "docs", "-c", build_config])

    # If docs were not built on linux-x86_64 release, create the expected docs output dir so packaging doesn't break.
    if (
        not repo_docs_enabled
        and not omni.repo.ci.is_windows()
        and build_config == "release"
        and platform.machine() == "x86_64"
    ):
        os.makedirs("_build/docs/isaac-sim/latest/py", exist_ok=True)

    # store the debugging symbols for release builds only.
    if build_config == "release":
        # For CICD builds against protected branches only set the TTL to 30 days
        if os.getenv("CI_COMMIT_REF_PROTECTED") == "true":
            omni.repo.ci.launch(["${root}/repo${shell_ext}", "symstore", "--ttl-seconds", "259200"])
        omni.repo.ci.launch(["${root}/repo${shell_ext}", "symstore", "--process-mrs"], warning_only=True)

    # Package release
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "package", "-m", "isaac-sim-standalone", "-c", build_config])
