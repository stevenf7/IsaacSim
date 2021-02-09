import os
import sys
import argparse
import logging
from typing import Dict, Callable, List

import omni.repo.man
import git_utils
import slack_notifier
import changelog

logger = logging.getLogger(os.path.basename(__file__))


def bump_version_file(version_file_path):
    version = open(version_file_path).readline()
    start, end = version.rsplit(".", maxsplit=1)
    new_version = "{}.{}".format(start, int(end) + 1)
    with open(version_file_path, "w") as f:
        f.write(new_version)
    print(f"Version in '{version_file_path}' bumped to: {new_version}")
    return new_version


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Tool to automatically update kit dependency to latest version and push changes."
    parser.add_argument(
        "-sc",
        "--skip-commit",
        dest="skip_commit",
        required=False,
        action="store_true",
        help="Only update, don't commit changes.",
    )
    parser.add_argument(
        "-sm",
        "--skip-merge",
        dest="skip_merge",
        required=False,
        action="store_true",
        help="Skip merge from master...for testing.",
    )
    parser.add_argument("-b", "--branch", dest="kit_branch", default="master", required=False, help="Kit branch to use")

    parser.add_argument(
        "-krr",
        "--kit-repo-root-folder",
        dest="kit_repo_root",
        required=False,
        help="Kit root folder if you have a local kit install, avoids clone ",
    )

    def run_repo_tool(options: Dict, config: Dict):
        repo_folders = config["repo"]["folders"]
        root = repo_folders["root"]

        if not options.skip_merge:
            # First merge latest master
            git_utils.call_git_safe(root, ["fetch", "--all"])
            git_utils.call_git_safe(root, ["merge", "-X", "theirs", "origin/master"])

        # Update kit sdk version to latest
        ret = omni.repo.man.update.update_packages(
            root, "omniverse-kit", dry_run=False, version_match_fn=omni.repo.man.update.version_match_minor
        )

        # no changes?
        if omni.repo.man.is_git_status_clean():
            print("Everything is up to date, exiting.")
            sys.exit(0)

        # increment version
        new_version = bump_version_file(f"{root}/VERSION.md")

        # Generate changelog
        if "omniverse-kit" not in ret:
            print("skipping changelog generation")
        else:
            start_version = ret["omniverse-kit"][0]
            end_version = ret["omniverse-kit"][1]
            start_commit = changelog.extract_commit_from_version_string(start_version)
            end_commit = changelog.extract_commit_from_version_string(end_version)

            print("start_commit", start_commit, "end_commit", end_commit)

            changelog_path = f"{root}/CHANGELOG.md"

            if options.kit_branch != "master" and options.kit_repo_root:
                print("specify either a kit branch or a root folder, not both")
            else:
                commit_log = []
                if options.kit_repo_root:
                    commit_log = git_utils.generate_log(options.kit_repo_root, ["%s..%s" % (start_commit, end_commit)])
                else:
                    commit_log = git_utils.generate_kit_commit_log(start_commit, end_commit, options.kit_branch)

                if not commit_log:
                    print("commit log is empty!")

                changelog.write_log(new_version, start_commit, end_commit, commit_log, changelog_path)
                print("commit log", commit_log)

                slack_notifier.post_extension_published("Isaac Sim", new_version, commit_log)

        if not options.skip_commit:
            git_utils.call_git_safe(root, ["add", "-A"])
            git_utils.call_git_safe(root, ["config", "user.email", '"teamcity@nvidia.com"'])
            git_utils.call_git_safe(root, ["config", "user.name", '"Team City"'])
            git_utils.call_git_safe(root, ["commit", "-m", '"updating kit sdk to latest"'])

            # Git push is done in TC build step.
            # call_git_safe(root, ["push"])

    return run_repo_tool
