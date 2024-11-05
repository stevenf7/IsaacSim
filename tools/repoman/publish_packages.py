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
import omni.repo.package
import packmanapi

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
        parsed_version.core = full_version
    return parsed_version


def call_git_safe(root, args):
    print("> git {}".format(" ".join(args)))
    with omni.repo.man.change_cwd(root):
        omni.repo.man.run_process(["git"] + args, exit_on_error=True)


def substitute_tokens_in_file(path, tokens):
    logger.info(f"substitute_tokens_in_file: '{path}'. Tokens: {tokens}")
    content = Template(open(path, "r").read()).substitute(tokens)
    with open(path, "w") as f:
        f.write(content)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to publish packages to packman."
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
                "isaac-sim-standalone*", repo_folders["packages"], None
            )
            if len(packages) == 0:
                logger.error("No packages found.")
                sys.exit(-1)
            for package in packages:

                if package.lower().endswith((".7z")):
                    print(f"Converting package {package} to a zip file.")
                    with omni.repo.man.TemporaryDirectory() as temp_dir:
                        target_dir = temp_dir
                        logger.info("TempDir: %s" % target_dir)
                        logger.info("NOTE: File attributes are not preserved when converting package on Windows.")
                        try:
                            packmanapi.extract_archive7z_to_folder(package, target_dir)
                            new_package = f"{os.path.splitext(package)[0]}.zip"
                            packmanapi.create_archivezip_from_folder(target_dir, new_package)
                            omni.repo.package.try_remove(package)
                            package = new_package
                        except:
                            print(f"Error converting {package}.")
                            sys.exit(-1)

                if not package.lower().endswith((".zip")):
                    print(f"Invalid package {package}. Need to be a zip file.")
                    sys.exit(-1)

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

                if "windows" in package:
                    package_url_windows = package_url
                else:
                    package_url_linux = package_url

        print(f"package_url_windows: {package_url_windows}")
        print(f"package_url_linux: {package_url_linux}")

    return run_repo_tool
