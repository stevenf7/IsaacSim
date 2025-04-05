# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

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


def _check_omniverse_kit_version(package_definitions, kit_sdk_packman, omniverse_kit_version, exit_on_error=True):
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
        if exit_on_error:
            sys.exit(1)
        return [], ""

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
    incompatible_versions = set()
    for package in packages:
        version = package["dependency"].split("==")[-1]
        if target_version != version:
            incompatible_versions.add(version)
            omni.repo.man.print_log(
                f"Package {package['name']} has an omniverse-kit version ({version}) incompatible with {target_version}",
                logging.ERROR,
            )
    if exit_on_error and len(incompatible_versions):
        sys.exit(1)
    return list(incompatible_versions), target_version


def _update_omniverse_kit_version(definition_paths, incompatible_versions, target_version):
    if not incompatible_versions:
        return
    # iterate for each Python packages definition file
    for definition_path in definition_paths:
        # check if file exists
        if not os.path.isfile(definition_path):
            omni.repo.man.print_log(f"Skipping package definition: {definition_path} doesn't exist", logging.WARN)
            continue
        # get file content
        with open(definition_path, "r") as f:
            content = f.read()
        # replace incompatible version occurrences
        version_updated = False
        for incompatible_version in incompatible_versions:
            if incompatible_version in content:
                content = content.replace(incompatible_version, target_version)
                omni.repo.man.print_log(
                    f"Updating omniverse-kit version in {definition_path} ({incompatible_version} -> {target_version})",
                    logging.INFO,
                )
                version_updated = True
        # update file content
        if version_updated:
            with open(definition_path, "w") as file:
                file.write(content)


def _check_extensions(package_definitions, extension_folder, excluded_extensions):
    # get extension names
    extensions = []
    for folder in extension_folder:
        extensions += [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

    missing_extensions = False
    for extension in extensions:
        # check for excluded extensions
        if extension in excluded_extensions:
            continue
        # check if extension is in any package inventory
        found = False
        for i, (name, spec) in enumerate(package_definitions.items()):
            inventory = spec.get("inventory", {}).get("include", [])
            if f"exts/{extension}" in inventory or f"extsDeprecated/{extension}" in inventory:
                found = True
                break
        if not found:
            missing_extensions = True
            omni.repo.man.print_log(f"The extension {extension} is not included in any package", logging.ERROR)
    if missing_extensions:
        sys.exit(1)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Check for the proper definition of the python packages"
    parser.add_argument(
        "--update-omniverse-kit",
        required=False,
        default=False,
        action="store_true",
        help="Update the omniverse-kit dependency version to match kit-sdk/kit-kernel one",
    )

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_check_python_package_definitions"]
        python_package_tool_config = config.get("repo_python_package", {})

        # get python packages definitions
        definition_paths = python_package_tool_config.get("definition_paths", [])
        package_definitions = omni.repo.python_package.create.load_extra_package_definitions({}, definition_paths)

        # update
        if options.update_omniverse_kit:
            incompatible_versions, target_version = _check_omniverse_kit_version(
                package_definitions,
                tool_config["kit_sdk_packman"],
                tool_config["omniverse_kit_version"],
                exit_on_error=False,
            )
            _update_omniverse_kit_version(definition_paths, incompatible_versions, target_version)
            return

        # checking
        _check_omniverse_kit_version(
            package_definitions, tool_config["kit_sdk_packman"], tool_config["omniverse_kit_version"]
        )
        _check_extensions(package_definitions, tool_config["extension_folder"], tool_config["excluded_extensions"])

    return run_repo_tool
