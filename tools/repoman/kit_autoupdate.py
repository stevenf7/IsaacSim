import os
import sys
import argparse
import fnmatch
import glob

import logging

from typing import Dict, Callable
from string import Template
from pathlib import Path

import omni.repo.man

logger = logging.getLogger(os.path.basename(__file__))


def call_git_safe(root, args):
    print("> git {}".format(" ".join(args)))
    git_output = omni.repo.man.execute_git(args, cwd=root)

    if git_output["returncode"] != 0:
        logger.error("Git command '{}' failed with: '{}'".format(args, git_output))
        sys.exit(-1)
    print(git_output["stdout"])
    return git_output["stdout"]


def bump_version_file(version_file_path):
    version = open(version_file_path).readline()
    start, end = version.rsplit(".", maxsplit=1)
    new_version = "{}.{}".format(start, int(end) + 1)
    with open(version_file_path, "w") as f:
        f.write(new_version)
    print(f"Version in '{version_file_path}' bumped to: {new_version}")


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to automatically update kit dependency to latest version and push changes."
    parser.add_argument(
        "-s",
        "--skip-commit",
        dest="skip_commit",
        required=False,
        action="store_true",
        help="Only update, don't commit changes.",
    )

    def run_repo_tool(options: Dict, config: Dict):
        repo_folders = config["repo"]["folders"]
        root = repo_folders["root"]

        # First merge latest master
        call_git_safe(root, ["merge", "-X", "theirs", "master"])

        # Update kit sdk version to latest
        omni.repo.man.update.update_packages(root, "omniverse-kit", dry_run=False)

        # no changes?
        if omni.repo.man.is_git_status_clean():
            print("Everything is up to date, exiting.")
            sys.exit(0)

        # increment version
        bump_version_file(f"{root}/VERSION.md")

        if not options.skip_commit:
            call_git_safe(root, ["add", "-A"])
            call_git_safe(root, ["config", "user.email", '"teamcity@nvidia.com"'])
            call_git_safe(root, ["config", "user.name", '"Team City"'])
            call_git_safe(root, ["commit", "-m", '"updating kit sdk to latest"'])

            # Git push is done in TC build step.
            # call_git_safe(root, ["push"])

    return run_repo_tool
