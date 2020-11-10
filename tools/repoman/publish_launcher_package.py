import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import packmanapi
import repoman

repoman.bootstrap()

import omni.repo.man

platform_host = omni.repo.man.get_and_validate_host_platform(["windows-x86_64"])
repo_folders = omni.repo.man.get_repo_paths()
script_dir = os.path.dirname(os.path.realpath(__file__))
repo_root = repo_folders["root"]


def publish_package(platform):
    package_dir = os.path.join(repo_folders["build"], "packages", platform)
    try:
        package_file = os.listdir(package_dir)[0]
    except Exception:
        print(f"Can't find a launcher package for platform: {platform}. Skipping.")
        return False
    package_path = os.path.join(package_dir, package_file)
    package_split = package_file.split("@")
    package_name = package_split[0]
    package_version = Path(package_split[1]).resolve().stem

    packmanapi.push(path=package_path, remotes=["cloudfront"], force=False)

    package_info = packmanapi.resolve(name=package_name, package_version=package_version, remotes=["cloudfront"])

    print(f"{platform} package: {package_info['remote_url']}")
    return True


def main():
    res = False
    res |= publish_package("windows")
    res |= publish_package("linux")
    if not res:
        print("Failed to publish any launcher package")
        sys.exit(-1)


if __name__ == "__main__" or __name__ == "__mp_main__":
    main()
