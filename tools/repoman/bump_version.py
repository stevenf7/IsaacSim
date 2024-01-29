# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# import sys
import argparse
import logging
import os
from typing import Callable, Dict

import omni.repo.man

# import distutils.dir_util
# import glob


# from string import Template
# from pathlib import Path


logger = logging.getLogger(os.path.basename(__file__))


class Version:
    def __init__(self):
        self.core = ""
        self.prerelease = ""
        self.major = ""
        self.minor = ""
        self.patch = ""
        self.pretag = ""
        self.prebuild = ""


def parse_version(full_version: Version):
    parsed_version = Version()
    if "-" in full_version:
        parsed_version.core, parsed_version.prerelease = full_version.split("-", maxsplit=1)
        parsed_version.major, parsed_version.minor, parsed_version.patch = parsed_version.core.split(".", maxsplit=2)
        parsed_version.pretag, parsed_version.prebuild = parsed_version.prerelease.split(".", maxsplit=1)
    else:
        parsed_version.major, parsed_version.minor, parsed_version.patch = full_version.split(".", maxsplit=2)
    return parsed_version


def bump_version_file(version_file_path):
    version = open(version_file_path).readline()
    start, end = version.rsplit(".", maxsplit=1)
    new_version = "{}.{}".format(start, int(end) + 1)
    with open(version_file_path, "w") as f:
        f.write(new_version)
    print(f"Version in '{version_file_path}' bumped to: {new_version}")
    return new_version


def call_git_safe(root, args):
    print("> git {}".format(" ".join(args)))
    with omni.repo.man.change_cwd(root):
        omni.repo.man.run_process(["git"] + args, exit_on_error=True)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to bump VERSION and update repo."
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
        # repo_folders = config["repo"]["folders"]
        # root = repo_folders["root"]

        tool_config = config["bump_version"]
        git_url = tool_config["git_url"]
        branch_name = tool_config["branch_name"]

        # Bump version in file
        with omni.repo.man.TemporaryDirectory() as temp_dir:
            logger.info(f"Working in temp folder: {temp_dir}")

            # version = open(f"{root}/VERSION").readline().strip()
            # parsed_version = parse_version(version)

            repo_name = "isaac-sim_bump_repo"

            # clone repo
            call_git_safe(temp_dir, ["clone", git_url, repo_name])
            cloned_repo_dir = os.path.join(temp_dir, repo_name)

            # setup user
            call_git_safe(cloned_repo_dir, ["config", "user.email", '"teamcity@nvidia.com"'])
            call_git_safe(cloned_repo_dir, ["config", "user.name", '"Team City"'])

            # create branch
            # branch_name = "develop-bump-test"
            call_git_safe(cloned_repo_dir, ["checkout", branch_name])
            try:
                call_git_safe(cloned_repo_dir, ["pull", git_url, branch_name])
            except:
                print(f"ERROR: Branch does not exists.")

            # increment version
            new_version = bump_version_file(f"{cloned_repo_dir}/VERSION")

            if not options.skip_commit:
                # push/commit everything
                logger.info("push/commit everything")
                call_git_safe(cloned_repo_dir, ["add", "VERSION"])
                call_git_safe(cloned_repo_dir, ["config", "user.email", '"teamcity@nvidia.com"'])
                call_git_safe(cloned_repo_dir, ["config", "user.name", '"Team City"'])
                call_git_safe(cloned_repo_dir, ["commit", "-m", f"Bumped version: {new_version}"])
                call_git_safe(cloned_repo_dir, ["lfs", "fetch", "--all"])
                call_git_safe(cloned_repo_dir, ["push", git_url, branch_name])

    return run_repo_tool
