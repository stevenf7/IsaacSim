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
from omni.repo.man import find_and_extract_package

def main(args: argparse.Namespace):

    git_clone_command = ["git", "clone", f"https://oauth2:{os.environ.get('GITHUB_ISAACLAB_CLONER_TOKEN')}@github.com/isaac-sim/IsaacLab-Internal.git", "_isaaclab"]
    omni.repo.ci.launch(git_clone_command)

    os.chdir("_isaaclab")

    git_checkout_command = ["git", "checkout", "devel"]
    omni.repo.ci.launch(git_checkout_command)

    os.chdir("..")

    folder, _ = find_and_extract_package("_build/packages/isaac-sim-standalone*.7z")

    link_cmd = ["ln", "-s", f"../{folder}", "_isaaclab/_isaac_sim"]
    omni.repo.ci.launch(link_cmd)


    os.chdir("_isaaclab")

    os.environ["TERM"] = "linux"

    setup_command = ["./isaaclab.sh", "-i"]
    omni.repo.ci.launch(setup_command)

    test_command = ["./_isaac_sim/python.sh", "-m", "pytest", "tools", "-v",]

    if os.getenv("RUN_NIGHTLY_TESTS","") != "true":
        test_command += ["-m", "isaacsim_ci"]

    omni.repo.ci.launch(test_command)