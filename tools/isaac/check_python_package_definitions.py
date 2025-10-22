# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import fnmatch
import logging
import os
import string
import subprocess
import sys
import tempfile
from collections import defaultdict
from typing import Callable, Dict
from xml.etree import ElementTree

import omni.repo.man
import omni.repo.python_package
import requests
import tomli
from omni.repo.man.version import OVFlowBuildIdentifier, PackmanVersion

logger = logging.getLogger(__name__)


def _parse_kit_version(kit_sdk_packman, template, exit_on_error=True):
    def get_by_index_or_default(elems, index, default):
        return elems[index] if len(elems) > index else default

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
        return ""

    # parse kit sdk/kernel build number to get the omniverse-kit target version
    ov_flow_version = OVFlowBuildIdentifier.from_build_string(build_number)
    packman_version = PackmanVersion(ov_flow_version.version)
    tokens = {
        "major": get_by_index_or_default(packman_version.components, 0, 0),
        "minor": get_by_index_or_default(packman_version.components, 1, 0),
        "patch": get_by_index_or_default(packman_version.components, 2, 0),
        "build_number": ov_flow_version.build_number,
        "build_string": build_number,
        "build_location": ov_flow_version.build_location,
        "gitbranch": ov_flow_version.gitbranch,
        "githash": ov_flow_version.githash,
    }
    return string.Template(template).substitute(tokens)


def _check_omniverse_kit_version(
    package_definitions, kit_sdk_packman, omniverse_kit_version, exit_on_error=True, print_errors=True
):
    # get kit sdk/kernel build number
    target_version = _parse_kit_version(kit_sdk_packman, omniverse_kit_version, exit_on_error)
    if not target_version:
        return [], ""

    # get packages that depend on omniverse-kit
    packages = []
    for i, (name, spec) in enumerate(package_definitions.items()):
        dependencies = spec.get("pyproject", {}).get("dependencies", [])
        for dependency in dependencies:
            if dependency.startswith("omniverse-kit"):
                packages.append({"name": name, "dependency": dependency})
    if not packages:
        omni.repo.man.print_log(
            f"Skipping checking: No packages found that depend on omniverse-kit=={target_version}", logging.WARN
        )

    # compare versions
    incompatible_versions = set()
    for package in packages:
        version = package["dependency"].split("==")[-1]
        if target_version != version:
            incompatible_versions.add(version)
            if print_errors:
                omni.repo.man.print_log(
                    f"Package {package['name']} has an omniverse-kit version ({version}) incompatible with {target_version}",
                    logging.ERROR,
                )
    if exit_on_error and len(incompatible_versions):
        sys.exit(1)
    return list(incompatible_versions), target_version


def _is_dependabot_kit_update():
    """Check if we're on a dependabot kit-sdk update branch with only kit-sdk.packman.xml changed"""
    try:
        # Check the current branch name
        branch_cmd = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        )
        branch_name = branch_cmd.stdout.strip()

        if branch_name != "dependabot/update-kit-sdk":
            return False

        # Check which files are changed in this branch
        files_cmd = subprocess.run(["git", "diff", "--name-only", "HEAD^"], capture_output=True, text=True, check=True)
        changed_files = files_cmd.stdout.strip().split("\n")

        # Return True only if kit-sdk.packman.xml is the only file changed
        return len(changed_files) == 1 and "kit-sdk.packman.xml" in changed_files[0]
    except subprocess.SubprocessError:
        # If git commands fail (e.g., not in a git repo), return False
        return False


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
        if os.path.isdir(folder):
            extensions += [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

    missing_extensions = False
    for extension in extensions:
        # check for excluded extensions
        if extension in excluded_extensions:
            continue
        # check if extension is in any package inventory
        found = False
        for i, (name, spec) in enumerate(package_definitions.items()):
            includes = [item for items in spec.get("inventory", {}).get("includes", {}).values() for item in items]
            if f"exts/{extension}" in includes or f"extsDeprecated/{extension}" in includes:
                found = True
                break
        if not found:
            missing_extensions = True
            omni.repo.man.print_log(f"The extension {extension} is not included in any package", logging.ERROR)
    if missing_extensions:
        sys.exit(1)


def _check_dependencies(package_definitions, kit_sdk_packman, dependencies_files, platforms):
    def _should_exclude_dependency(dependency):
        for item in ["isaacsim-", "nvidia-"]:
            if dependency.startswith(item):
                return True
        return False

    def _dependencies_in(dependency, dependencies):
        def _get_name(dependency):
            return dependency.replace("=", "#").replace("<", "#").replace(">", "#").split("#")[0]

        def _handle_special_cases(dependency):
            if dependency.startswith("torch"):
                dependency = dependency.split("+")[0]  # ignore cuda version in PyTorch
            dependency = dependency.replace("typing_extensions", "typing-extensions")
            return dependency

        # handle special cases
        dependency = _handle_special_cases(dependency)
        dependencies = [_handle_special_cases(d) for d in dependencies]
        # check for missing/mismatching dependencies
        if dependency not in dependencies:
            name = _get_name(dependency)
            names = [_get_name(d) for d in dependencies]
            if name in names:
                return False, dependencies[names.index(name)]
            return False, ""
        return True, None

    def _get_platforms_from_target(target_platforms, platforms, path):
        matched_platforms = []
        for target_platform in target_platforms:
            found = False
            for platform in platforms:
                if fnmatch.fnmatch(platform, target_platform):
                    matched_platforms.append(platform)
                    found = True
            if not found:
                omni.repo.man.print_log(
                    f"Unable to find target platform '{target_platform}' in {platforms} ({path})",
                    logging.ERROR,
                )
                sys.exit(1)
        matched_platforms = sorted(list(set(matched_platforms)))
        return ["all"] if matched_platforms == platforms else matched_platforms

    missing_dependencies = False
    defined_dependencies = defaultdict(list)
    defined_platforms = ["all", *platforms]
    for item in defined_platforms:
        defined_dependencies[item].extend([])
    for _, spec in package_definitions.items():
        for k, v in spec.get("pyproject", {}).get("dependencies", {}).items():
            for dependency in v:
                if not _should_exclude_dependency(dependency):
                    defined_dependencies[k].append(dependency)
    if len(defined_dependencies) != len(defined_platforms):
        omni.repo.man.print_log(
            f"Expected specification: {defined_platforms}, got: {list(defined_dependencies.keys())}",
            logging.ERROR,
        )
        sys.exit(1)

    # read dependencies files (.toml)
    all_target_dependencies = {platform: [] for platform in defined_platforms}
    for dependencies_file in dependencies_files:
        # process file
        if os.path.isfile(dependencies_file):
            path = dependencies_file
        else:
            url = _parse_kit_version(kit_sdk_packman, dependencies_file, exit_on_error=False)
            if not url:
                omni.repo.man.print_log(f"Unable to parse kit version from {dependencies_file}", logging.ERROR)
                sys.exit(1)
            # get file name from url using python built-in libraries and store it in a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".toml") as file:
                omni.repo.man.print_log(f"Downloading {url} to {file.name}", logging.INFO)
                file.write(requests.get(url).content)
                path = file.name
        # read dependencies file content
        target_dependencies = {platform: [] for platform in defined_platforms}
        omni.repo.man.print_log(f"Reading {path}", logging.INFO)
        with open(path, "rb") as file:
            content = tomli.load(file)
            for dependency in content.get("dependency", []):
                # skip untargeted dependencies
                skip_target_deps = False
                for item in ["target-deps/pip_sensors", "target-deps/pip_debugpy"]:
                    if item in dependency.get("target", ""):
                        skip_target_deps = True
                        break
                if skip_target_deps:
                    continue
                # get depedencies according to target platforms
                target_platforms = _get_platforms_from_target(dependency.get("platforms", []), platforms, path)
                for target_platform in target_platforms:
                    for package in dependency.get("packages", []):
                        if not _should_exclude_dependency(package):
                            target_dependencies[target_platform].append(package)
        # update all target dependencies
        for k, v in target_dependencies.items():
            all_target_dependencies[k].extend(v)
        # check if target dependencies are in defined dependencies
        for platform in defined_platforms:
            for target_dependency in target_dependencies[platform]:
                result, msg = _dependencies_in(target_dependency, defined_dependencies[platform])
                if not result:
                    missing_dependencies = True
                    msg = f"Mismatch with defined dependency {msg}" if msg else "Missing"
                    omni.repo.man.print_log(
                        f"[file: {dependencies_file}, platform: {platform}] Expected dependency: {target_dependency}. {msg}",
                        logging.ERROR,
                    )
    # check if defined dependencies are in all target dependencies
    for platform in defined_platforms:
        for defined_dependency in defined_dependencies[platform]:
            result, msg = _dependencies_in(defined_dependency, all_target_dependencies[platform])
            if not result:
                missing_dependencies = True
                if msg:
                    omni.repo.man.print_log(
                        f"[source: definition_paths, platform: {platform}] Defined dependency has a different version: {defined_dependency}. Expected: {msg}",
                        logging.ERROR,
                    )
                else:
                    omni.repo.man.print_log(
                        f"[source: definition_paths, platform: {platform}] Defined dependency not found in target dependencies: {defined_dependency}",
                        logging.ERROR,
                    )
    # export defined dependencies to a requirements.txt file
    for platform in platforms:
        with open(f"python-package-requirements-{platform}.txt", "w") as file:
            file.write("# common dependencies\n")
            file.write("\n".join(defined_dependencies["all"]))
            file.write("\n# platform-specific dependencies\n")
            file.write("\n".join(defined_dependencies[platform]))
    if missing_dependencies:
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
    parser.add_argument(
        "--gitlab",
        required=False,
        default=False,
        action="store_true",
        help="Enable GitLab CI mode - ignores errors during dependabot kit-sdk updates",
    )

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_check_python_package_definitions"]
        python_package_tool_config = config.get("repo_python_package", {})

        # get python packages definitions
        definition_paths = python_package_tool_config.get("definition_paths", [])
        package_definitions = omni.repo.python_package.create.load_extra_package_definitions({}, definition_paths)
        platforms = sorted(list(python_package_tool_config.get("wheel", {}).get("platforms", {}).keys()))

        # update
        if options.update_omniverse_kit:
            incompatible_versions, target_version = _check_omniverse_kit_version(
                package_definitions,
                tool_config["kit_sdk_packman"],
                tool_config["omniverse_kit_version"],
                exit_on_error=False,
                print_errors=False,
            )
            _update_omniverse_kit_version(definition_paths, incompatible_versions, target_version)
            return

        # check if we're in GitLab mode with dependabot update
        skip_exit_on_error = options.gitlab and _is_dependabot_kit_update()
        if skip_exit_on_error:
            omni.repo.man.print_log(
                "GitLab mode detected with dependabot/update-kit-sdk branch and kit-sdk.packman.xml changes - errors will be reported but not fail the build",
                logging.INFO,
            )

        # checking
        _check_omniverse_kit_version(
            package_definitions,
            tool_config["kit_sdk_packman"],
            tool_config["omniverse_kit_version"],
            exit_on_error=not skip_exit_on_error,
        )
        _check_extensions(package_definitions, tool_config["extension_folder"], tool_config["excluded_extensions"])
        _check_dependencies(
            package_definitions, tool_config["kit_sdk_packman"], tool_config["dependencies_files"], platforms
        )

    return run_repo_tool
