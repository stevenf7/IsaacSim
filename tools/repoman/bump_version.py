import os
import sys
import argparse
import distutils.dir_util
import glob

import logging

from typing import Dict, Callable
from string import Template
from pathlib import Path

import omni.repo.man

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


def call_git_safe(root, args):
    print("> git {}".format(" ".join(args)))
    with omni.repo.man.change_cwd(root):
        omni.repo.man.run_process(["git"] + args, exit_on_error=True)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to bump VERSION.md and update repo."
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
        root = repo_folders["root"]

        tool_config = config["bump_version"]
        #git_url = tool_config["git_url"]
        #template_path = tool_config["template_path"]

        # if not os.path.exists(template_path):
        #     logger.error(f"template_path: '{template_path}' doesn't exist.")
        #     sys.exit(-1)

        # Bump version in file
        with omni.repo.man.TemporaryDirectory() as temp_dir:
            logger.info(f"Working in temp folder: {temp_dir}")

            # Read version file
            version = open(f"{root}/VERSION.md").readline().strip()
            parsed_version = parse_version(version)
            logger.info(f"parsed_version: {parsed_version}")

        if not options.skip_commit:
            # push/commit everything
            call_git_safe(root, ["add", "-A"])
            call_git_safe(root, ["commit", "-m", f"deploy version: {version}"])
            #call_git_safe(root, ["push", git_url, branch_name])

    return run_repo_tool
