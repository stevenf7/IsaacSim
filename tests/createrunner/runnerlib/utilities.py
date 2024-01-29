# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import fnmatch
import os
import platform
import stat
import sys
import xml.etree.ElementTree as ET
from itertools import chain
from pathlib import Path
from typing import Generator, Union


class PlatformHelper(object):
    def __init__(self):
        self.os = platform.system()
        if self.os != "Windows" and self.os != "Linux":
            raise EnvironmentError(f"Unsupported OS: {self.os}")

    def script_extension(self):
        if self.os == "Windows":
            return ".bat"
        else:
            return ".sh"

    def invalid_script_extensions(self):
        if self.os == "Windows":
            return [".sh"]
        else:
            return [".bat", ".cmd"]

    def executable_extension(self):
        if self.os == "Windows":
            return ".exe"
        else:
            return ""

    def architecture(self):
        if self.os == "Windows":
            return "windows-x86_64"
        else:
            return "linux-x86_64"


def remove_directory_item(path: Union[str, Path]):
    """
    Stolen from packman: https://gitlab-master.nvidia.com/hfannar/packman/-/blob/main/common/utils.py#L69

    We use this in preference to shutil.rmtree as it won't follow symlinks and delete
    packman packages symlinked into the package.

    Args:
        path: A string or Path-like object to a file or directory
    """

    if os.path.islink(path) or os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            # make sure we have write access and try again:
            os.chmod(path, stat.S_IWUSR)
            os.remove(path)
    else:
        # try first to delete the dir because this will work for folder junctions,
        # otherwise we would follow the junctions and cause destruction!
        try:
            os.rmdir(path)
        except OSError:
            # we should make sure the directory is empty
            names = os.listdir(path)
            for name in names:
                fullname = os.path.join(path, name)
                remove_directory_item(fullname)
            # now try to again get rid of the folder - and not catch if it raises:
            os.rmdir(path)


def find_rglob(root: Path, pattern: str) -> Generator[Path, None, None]:
    """
    Find files or directories matching a pattern

    Args:
        root: the root directory to start the recursive search.
        pattern: fnmatch pattern for the file/directory.

    Yields:
        Path objects with the matches.
    """
    for dirname, directories, files in os.walk(root):
        for entry in chain(directories, files):
            if fnmatch.fnmatch(entry, pattern):
                yield root / dirname / entry


depFileXml = '<project toolsVersion="5.6"></project>'


def updateXmlDep(root, name, buildId):
    deps = root.findall("dependency")
    for dep in deps:
        package = dep.find("package")
        package.set("version", buildId + "-${platform}-release")


def writeUpdatedPackmanDeps(create_root_path, kit_tc_build_id):
    """
    app_exe_path - the root of the project, normally where the build files etc are
    kit_tc_build_id - format like "100.1.39496-84fdbba2-release"
    """
    createDepsDir = os.path.join(create_root_path, "deps")
    createKitSDKFile = os.path.join(createDepsDir, "kit-sdk.packman.xml")
    if not os.path.exists(createKitSDKFile):
        print("couldnt find kitsdk deps file in %s" % createKitSDKFile)
        return
    xmlTree = ET.parse(createKitSDKFile)
    root = xmlTree.getroot()
    updateXmlDep(root, "kit_sdk_release", kit_tc_build_id)
    xmlTree.write(createKitSDKFile)
