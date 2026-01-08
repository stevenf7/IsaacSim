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
from tools.ci.upstream_kit_build.pull_kit import find_latest_nightly_pipeline_id
import omni.repo.ci


def main(args: argparse.Namespace):


    downstream_pipeline =  os.getenv("CI_PIPELINE_SOURCE", "") == "pipeline"
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

    extra_flags.append("--enable-gcov")

    build_cmd = ["${root}/repo${shell_ext}", "build", "-x"] + extra_flags

    # Full rebuild config
    omni.repo.ci.launch(build_cmd)


    # This build exists specifically for coverage so we can skip docs

    # Package release
    omni.repo.ci.launch(["${root}/repo${shell_ext}", "package", "-m", "isaac-sim-standalone-coverage", "-c", build_config])
