import argparse
import os
import shutil
import glob
import base64
import logging
import hashlib
import subprocess
import sys

import packmanapi
import repoman

repoman.bootstrap()

import omni.repo.man

REPO_FOLDERS = omni.repo.man.get_repo_paths()
SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT = REPO_FOLDERS["root"]

logger = logging.getLogger(os.path.basename(__file__))

KIT_ARCHIVE_PATTERN = "_builtpackages/omniverse-kit*-{config}.7z"


def simple_yaml_load(file):
    d = {}
    with open(file, "r") as f:
        for line in f.readlines():
            if line != "\n":
                key, value = line.split(":", maxsplit=1)
                value = value.strip()
                if value.startswith("b'"):
                    value = value[2:-1]
                d[key.strip()] = value
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", dest="config", required=False, default="release", help="Config target. (default: %(default)s)"
    )
    parser.add_argument(
        "-p",
        "--platform-target",
        dest="platform_target",
        default=omni.repo.man.get_host_platform(),
        required=False,
        help="Platform. (default: %(default)s)",
    )

    options = parser.parse_args()
    platform_target = options.platform_target
    config = options.config

    kit_path = f"{REPO_ROOT}/_build/kit_release"

    package_info_file = os.path.join(kit_path, "PACKAGE-INFO.yaml")
    if not os.path.exists(package_info_file):
        logger.error(f"Packman package '{kit_path}' doesn't have PACKAGE-INFO.yaml file.")
        sys.exit(-1)

    # read current kit sdk package version
    info = simple_yaml_load(package_info_file)
    kit_sdk_version = info.get("Version", None)
    print(f"omniverse-kit version: {kit_sdk_version}")

    # WAR for different version schemes
    # kit_launcher_version = kit_sdk_version.replace(f"-{platform_target}-{config}", f".{platform_target}.{config}")
    # print(f"kit-launcher version: {kit_launcher_version}")

    # # Here we switch from omniverse-kit package to smaller kit-launcher package on the same folder link.
    # # Then we package it in and in the end switch back. That is almost as if kit sdkwas coming from launcher itself.
    # packmanapi.install("kit-launcher", kit_launcher_version, link_path=f"{REPO_ROOT}/_build/kit_release")

    # Package launcher using this package as a root:
    print("Packaging launcher...")
    repo_exec = f"{REPO_ROOT}/repo.bat" if platform_target == "windows-x86_64" else f"{REPO_ROOT}/repo.sh"
    omni.repo.man.run_process([repo_exec, "package", "-m", "isaac_sim-launcher", "-c", config], exit_on_error=True)

    # Make package TC artifact:
    print(f"##teamcity[publishArtifacts '_build/packages/*']")

    # revert back
    # packmanapi.install("omniverse-kit", kit_sdk_version, link_path=f"{REPO_ROOT}/_build/kit_release")
