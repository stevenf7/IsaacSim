# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import distutils.dir_util
import glob
import logging
import os
import sys
from pathlib import Path
from string import Template
from typing import Callable, Dict

import omni.repo.man
import packmanapi

REPO_FOLDERS = omni.repo.man.get_repo_paths()
SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT = REPO_FOLDERS["root"]

logger = logging.getLogger(os.path.basename(__file__))


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to publish launcher images."
    parser.add_argument(
        "-s",
        "--skip-commit",
        dest="skip_commit",
        required=False,
        action="store_true",
        help="Only update, don't commit changes.",
    )
    parser.add_argument("-t", "--test", dest="test_run", required=False, action="store_true", help="Test run.")

    def run_repo_tool(options: Dict, config: Dict):
        repo_folders = config["repo"]["folders"]

        # publish first
        if not options.test_run:
            packages, labels = omni.repo.man.publish.get_packages_and_labels(
                "isaac-sim-pipeline-images-*", repo_folders["packages"], None
            )
            if len(packages) == 0:
                logger.error("No packages found.")
                sys.exit(-1)
            for package in packages:
                print(f"Publishing Package {package}")

                remote = "cloudfront"
                try:
                    packmanapi.push(package, remotes=[remote], force=False)
                except packmanapi.PackmanErrorFileExists:
                    print(f"package: {package} already exist on remote.")

                package_name, package_version = Path(package).stem.split("@")
                package_info = packmanapi.resolve(name=package_name, package_version=package_version, remotes=[remote])
                package_url = package_info["remote_url"]
                print(f"package: {package_name}, url: {package_url}")

    return run_repo_tool
