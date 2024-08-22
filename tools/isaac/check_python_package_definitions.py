# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import logging
import os
import string
import sys
from typing import Callable, Dict
from xml.etree import ElementTree

import omni.repo.man
import omni.repo.python_package
from omni.repo.man.version import OVFlowBuildIdentifier, PackmanVersion

logger = logging.getLogger(__name__)


def _check_omniverse_kit_version(package_definitions, kit_sdk_packman, omniverse_kit_version):
    def get_by_index_or_default(elems, index, default):
        return elems[index] if len(elems) > index else default

    # get kit sdk/kernel build number
    build_number = ""
    tree = ElementTree.parse(kit_sdk_packman)
    for dependency in tree.getroot().iter("dependency"):
        for package in dependency.iter("package"):
            if package.get("name").lower() in ["kit-sdk", "kit-kernel"]:
                build_number = package.get("version").replace(r".${platform}", "").replace(r".${config}", "")
    if not build_number:
        omni.repo.man.print_log(f"Unable to identify kit sdk/kernel version in {kit_sdk_packman}", logging.ERROR)
        sys.exit(1)

    # parse kit sdk/kernel build number to get the omniverse-kit target version
    ov_flow_version = OVFlowBuildIdentifier.from_build_string(build_number)
    packman_version = PackmanVersion(ov_flow_version.version)
    tokens = {
        "major": get_by_index_or_default(packman_version.components, 0, 0),
        "minor": get_by_index_or_default(packman_version.components, 1, 0),
        "patch": get_by_index_or_default(packman_version.components, 2, 0),
        "build_number": ov_flow_version.build_number,
        "build_string": build_number,
    }
    target_version = string.Template(omniverse_kit_version).substitute(tokens)

    # get packages that depend on omniverse-kit
    packages = []
    for i, (name, spec) in enumerate(package_definitions.items()):
        dependencies = spec.get("pyproject", {}).get("dependencies", [])
        for dependency in dependencies:
            if dependency.startswith("omniverse-kit"):
                packages.append({"name": name, "dependency": dependency})
    if not packages:
        omni.repo.man.print_log("Skipping checking: No packages found that depend on omniverse-kit", logging.WARN)

    # compare versions
    incompatible_version = False
    for package in packages:
        version = package["dependency"].split("==")[-1]
        if target_version != version:
            incompatible_version = True
            omni.repo.man.print_log(
                f"Package {package['name']} has an omniverse-kit version ({version}) incompatible with {target_version}",
                logging.ERROR,
            )
    if incompatible_version:
        sys.exit(1)


def _check_extensions(package_definitions, extension_folder, excluded_extensions):
    # get extension names
    extensions = [d for d in os.listdir(extension_folder) if os.path.isdir(os.path.join(extension_folder, d))]

    missing_extensions = False
    for extension in extensions:
        # check for excluded extensions
        if extension in excluded_extensions:
            continue
        # check if extension is in any package inventory
        found = False
        for i, (name, spec) in enumerate(package_definitions.items()):
            inventory = spec.get("inventory", {}).get("include", [])
            if f"exts/{extension}" in inventory:
                found = True
                break
        if not found:
            missing_extensions = True
            omni.repo.man.print_log(f"The extension {extension} is not included in any package", logging.ERROR)
    if missing_extensions:
        sys.exit(1)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Check for the proper definition of the python packages"

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_check_python_package_definitions"]
        python_package_tool_config = config.get("repo_python_package", {})

        # get python packages definitions
        definition_paths = python_package_tool_config.get("definition_paths", [])
        package_definitions = omni.repo.python_package.create.load_extra_package_definitions({}, definition_paths)

        _check_omniverse_kit_version(
            package_definitions, tool_config["kit_sdk_packman"], tool_config["omniverse_kit_version"]
        )
        _check_extensions(package_definitions, tool_config["extension_folder"], tool_config["excluded_extensions"])

    return run_repo_tool
