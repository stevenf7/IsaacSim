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
    parser.description = "Tool to publish launcher to packman and deploy it on launcher pipeline repo."
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

        tool_config = config["publish_assets_launcher"]
        git_url = tool_config["git_url"]
        template_path = tool_config["template_path"]
        branch_prefix = tool_config["branch_prefix"]

        if not os.path.exists(template_path):
            logger.error(f"template_path: '{template_path}' doesn't exist.")
            sys.exit(-1)

        package_url_windows = "test.url.win"
        package_url_linux = "test.url.linux"

        # publish first
        if not options.test_run:
            packages, labels = omni.repo.man.publish.get_packages_and_labels(
                "isaac-sim-assets*", repo_folders["packages"], None
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

                package_url_windows = package_url
                package_url_linux = package_url

        # Now deploy
        print(f"package_url_windows: {package_url_windows}")
        print(f"package_url_linux: {package_url_linux}")
        with omni.repo.man.TemporaryDirectory() as temp_dir:
            logger.info(f"Working in temp folder: {temp_dir}")

            version = open(f"{root}/VERSION").readline().strip()
            parsed_version = parse_version(version)
            if len(parsed_version.pretag) == 0:
                branch_name = f"{branch_prefix}-{parsed_version.core}"
            else:
                branch_name = f"{branch_prefix}-{parsed_version.core}-{parsed_version.pretag}"

            pipeline_repo = "pipeline_repo"

            # clone repo
            call_git_safe(temp_dir, ["clone", git_url, pipeline_repo])
            cloned_repo_dir = os.path.join(temp_dir, pipeline_repo)

            # setup user
            call_git_safe(cloned_repo_dir, ["config", "user.email", '"teamcity@nvidia.com"'])
            call_git_safe(cloned_repo_dir, ["config", "user.name", '"Team City"'])

            # create branch
            call_git_safe(cloned_repo_dir, ["checkout", "-b", branch_name])
            try:
                call_git_safe(cloned_repo_dir, ["pull", git_url, branch_name])
            except:
                print(f"This is fine. The branch is new and have not been pushed yet.")

            # clean all files and copy ours from template folder
            for p in glob.glob(cloned_repo_dir + "/*"):
                os.remove(p)
            distutils.dir_util.copy_tree(template_path, cloned_repo_dir)

            # fill in all files with data
            tokens = {
                "package_url_windows": package_url_windows,
                "package_url_linux": package_url_linux,
                "version": version,
            }
            for file in ["description.toml", "package.toml"]:
                substitute_tokens_in_file(os.path.join(cloned_repo_dir, file), tokens)

            if not options.skip_commit:
                # push/commit everything
                call_git_safe(cloned_repo_dir, ["add", "-A"])
                call_git_safe(cloned_repo_dir, ["commit", "-m", f"deploy version: {version}"])
                call_git_safe(cloned_repo_dir, ["push", git_url, branch_name])

    return run_repo_tool
