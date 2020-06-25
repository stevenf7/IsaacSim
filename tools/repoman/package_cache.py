import os
import sys
import platform
import argparse
import logging
import shutil
import subprocess
import packmanapi
import repoman
from test_runner import prepare_package
import omni.repo.man


logger = logging.getLogger(os.path.basename(__file__))


def find_7za():
    if platform.system() == "Windows":
        return os.path.join(os.getenv("PM_7za_PATH"), "win-x86/64/7za.exe")
    elif platform.system() == "Linux" and platform.uname().machine == "aarch64":
        return os.path.join(os.getenv("PM_7za_PATH"), "linux-arm/64/7za")
    elif platform.system() == "Linux":
        return os.path.join(os.getenv("PM_7za_PATH"), "linux-x86/64/7za")
    return "7za"


def remove_folder(archive_path, folder_path):
    args = [find_7za(), "d", archive_path, folder_path, "-r"]
    p = subprocess.Popen(args)
    returncode = p.wait()
    if returncode != 0:
        print("Error removing {folder_path}")
        sys.exit(1)


def remove_file(archive_path, file_path):
    args = [find_7za(), "d", archive_path, file_path]
    p = subprocess.Popen(args)
    returncode = p.wait()
    if returncode != 0:
        print("Error removing the {file_path}")
        sys.exit(1)


def copy_data_folder(archive_path, root_folder, data_folder):
    data_path = os.path.join(root_folder, data_folder)

    if not os.path.exists(data_path):
        logger.error("Data folder not found: {data_folder}")
        sys.exit(1)

    if os.path.exists(data_folder):
        shutil.rmtree(data_folder)

    print(f"Copying {data_path} => {data_folder}")
    shutil.copytree(data_path, data_folder)

    args = [find_7za(), "u", archive_path, data_folder, "-spf"]
    p = subprocess.Popen(args)
    returncode = p.wait()

    if returncode != 0:
        print("Error copying data folder")
        sys.exit(1)


def update_package(root: str, platform: str, config: str, experience: str):
    root_folder, archive_path = prepare_package(root, platform, config, False, False)

    # update cache folder
    cache_folder = f"_build/target-deps/kit_sdk_{config}/_build/{platform}/{config}/cache"
    cache_path = os.path.join(root_folder, cache_folder)

    if not os.path.exists(cache_path):
        logger.error("Cache folder not found")
        sys.exit(-1)

    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)

    print(f"Copying {cache_path} => {cache_folder}")
    shutil.copytree(cache_path, cache_folder)

    args = [find_7za(), "u", archive_path, cache_folder, "-spf"]
    p = subprocess.Popen(args)
    returncode = p.wait()

    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)

    if returncode != 0:
        logger.error(f"Error updating {archive_path}")
        sys.exit(1)

    # remove shaders folder
    print(f"Removing shaders folder")
    shaders_folder = f"_build/target-deps/kit_sdk_{config}/_build/shaders"
    remove_folder(archive_path, shaders_folder)

    # remove info file
    print(f"Removing package info file")
    info_file = f"PACKAGE-INFO.yaml"
    remove_file(archive_path, info_file)

    # remove samples_internal extensions
    print(f"Removing samples_internal extensions")
    extension_folder = f"_build/{platform}/{config}/exts/omni.isaac.samples_internal"
    remove_folder(archive_path, extension_folder)

    # update data folder
    print(f"Updating data folder")
    data_folder = f"_build/target-deps/kit_sdk_{config}/_build/{platform}/{config}/data"
    copy_data_folder(archive_path, root_folder, f"{data_folder}/Kit/{experience}/2020.2.3598/pip3-envs")
    copy_data_folder(archive_path, root_folder, f"{data_folder}/Kit/{experience}-headless/2020.2.3598/pip3-envs")


def main():
    repo_folders = omni.repo.man.get_repo_paths()

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.name = "Cache Packager"
    parser.add_argument(
        "-p",
        "--platform",
        dest="platform",
        required=False,
        default="windows-x86_64",
        help="Platform target. (default: %(default)s)",
    )
    parser.add_argument(
        "-c", "--config", dest="config", required=False, default="debug", help="Config target. (default: %(default)s)"
    )
    parser.add_argument("--experience", dest="experience", default="isaac-sim", help="Experience to run.")

    options = parser.parse_args()
    update_package(repo_folders["root"], options.platform, options.config, options.experience)


if __name__ == "__main__":
    main()
