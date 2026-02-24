# Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import glob
import logging
import os
import shutil
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
    parser.add_argument("-t", "--test", dest="test_run", required=False, action="store_true", help="Test run.")

    def run_repo_tool(options: Dict, config: Dict):
        repo_folders = config["repo"]["folders"]

        # Check if this is a nightly build that should use alternate naming
        upstream_pipeline_source = os.environ.get("UPSTREAM_PIPELINE_SOURCE", "")
        use_alternate_naming = upstream_pipeline_source == "nightly"
        
        if use_alternate_naming:
            logger.info("Detected UPSTREAM_PIPELINE_SOURCE=nightly - will publish with alternate naming")
        
        if options.test_run:
            logger.info("TEST RUN MODE - Will skip actual packman push operations")

        # Get packages to publish
        packages, labels = omni.repo.man.publish.get_packages_and_labels(
            "isaac-sim-standalone*", repo_folders["packages"], None
        )
        if len(packages) == 0:
            logger.error("No packages found.")
            sys.exit(-1)
        
        for package in packages:
            if package.lower().endswith((".7z")):
                logger.info(f"Converting package {package} to a zip file.")
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
                        logger.error(f"Error converting {package}.")
                        sys.exit(-1)

            if not package.lower().endswith((".zip")):
                logger.error(f"Invalid package {package}. Need to be a zip file.")
                sys.exit(-1)

            # Handle alternate naming for nightly builds
            package_to_publish = package
            if use_alternate_naming:
                # Rename the package (move it to new name)
                original_name = Path(package).name

                commit_ref = os.environ.get("CI_COMMIT_REF_NAME", "")
                if commit_ref.startswith("kit-integration/"):
                    kit_branch = commit_ref.removeprefix("kit-integration/")
                    kit_branch = kit_branch.replace("/", "-")
                    new_name = original_name.replace("isaac-sim-standalone", f"isaac-sim-standalone-kit-tot-{kit_branch}")
                else:
                    new_name = original_name.replace("isaac-sim-standalone", "isaac-sim-standalone-kit-tot")
                new_package_path = Path(package).parent / new_name
                
                logger.info(f"Renaming package: {original_name} -> {new_name}")
                shutil.move(package, new_package_path)
                package_to_publish = str(new_package_path)

            logger.info(f"Publishing Package {package_to_publish}")
            remote = "cloudfront"
            
            package_name, package_version = Path(package_to_publish).stem.split("@")
            
            if not options.test_run:
                try:
                    packmanapi.push(package_to_publish, remotes=[remote], force=False)
                except packmanapi.PackmanErrorFileExists:
                    logger.info(f"package: {package_to_publish} already exist on remote.")

                package_info = packmanapi.resolve(name=package_name, package_version=package_version, remotes=[remote])
                package_url = package_info["remote_url"]
                logger.info(f"package: {package_name}, url: {package_url}")
            else:
                logger.info(f"TEST RUN: Would push package: {package_name}@{package_version} to remote: {remote}")
                package_url = f"<test-mode-url-for-{package_name}>"

            if "windows" in package_to_publish:
                package_url_windows = package_url
                logger.info(f"package_url_windows: {package_url_windows}")
            else:
                package_url_linux = package_url
                logger.info(f"package_url_linux: {package_url_linux}")


    return run_repo_tool
