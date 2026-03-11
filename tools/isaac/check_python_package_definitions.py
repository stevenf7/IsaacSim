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
import platform as platform_module
import shutil
import string
import subprocess
import sys
import tempfile
from collections import defaultdict
from typing import Callable, Dict, List, Optional
from xml.etree import ElementTree

import omni.repo.man
import omni.repo.python_package
import requests
import tomli
from omni.repo.man.version import OVFlowBuildIdentifier, PackmanVersion

logger = logging.getLogger(__name__)

# From kit-sdk.packman.xml we only read the package "version" attribute (e.g. for kit-kernel).
# That string is parsed by OVFlowBuildIdentifier to get: major, minor, patch, build_number,
# githash, etc., which are used for template substitution (omniverse_kit_version and
# dependencies_files URL). kit-sdk.packman.xml is not in the Kit repo; it lives in Isaac Sim's deps/.

# GitLab Kit project and URL used when resolving kit version from upstream pipeline.
KIT_GITLAB_PROJECT_ID = 6510
KIT_GITLAB_BASE_URL = "https://gitlab-master.nvidia.com"
# Path in the Kit repo (at pipeline sha) for major.minor.patch. Full version string is
# {major}.{minor}.{patch}+{ref}.{pipeline_iid}.{githash_short}, with ref/iid/githash from the pipeline API.
KIT_VERSION_PATH = "kit/VERSION"


def _get_upstream_kit_tokens() -> Optional[Dict]:
    """When running as a downstream pipeline (CI_PIPELINE_SOURCE == 'pipeline') with
    UPSTREAM_PIPELINE_ID set, get version tokens from the upstream Kit pipeline: one
    API call for sha/ref/iid, plus kit/VERSION for major.minor.patch. The version
    string is {major}.{minor}.{patch}+{ref}.{pipeline_iid}.{githash_short}.
    Returns a dict of tokens for template substitution, or None if not in upstream mode.
    """
    ci_source = os.getenv("CI_PIPELINE_SOURCE", "")
    upstream_id = os.getenv("UPSTREAM_PIPELINE_ID", "").strip()
    if ci_source != "pipeline" or not upstream_id:
        return None

    token = os.getenv("CI_GITLAB_API_TOKEN")
    if not token:
        omni.repo.man.print_log(
            "GitLab upstream mode (CI_PIPELINE_SOURCE=pipeline, UPSTREAM_PIPELINE_ID set) requires "
            "CI_GITLAB_API_TOKEN to fetch kit version from upstream pipeline",
            logging.ERROR,
        )
        sys.exit(1)

    headers = {"PRIVATE-TOKEN": token}

    # Get pipeline to read the Kit commit sha (githash)
    pipeline_url = f"{KIT_GITLAB_BASE_URL}/api/v4/projects/{KIT_GITLAB_PROJECT_ID}/pipelines/{upstream_id}"
    try:
        resp = requests.get(pipeline_url, headers=headers, timeout=30)
        resp.raise_for_status()
        pipeline = resp.json()
    except requests.RequestException as e:
        omni.repo.man.print_log(
            f"Failed to get upstream pipeline {upstream_id}: {e}",
            logging.ERROR,
        )
        sys.exit(1)

    sha = pipeline.get("sha")
    ref = pipeline.get("ref", "")
    iid = pipeline.get("iid") or pipeline.get("id")
    if not sha:
        omni.repo.man.print_log(
            f"Upstream pipeline {upstream_id} has no 'sha'; cannot resolve kit version",
            logging.ERROR,
        )
        sys.exit(1)
    # Normalize ref to branch/tag name (strip refs/heads/, refs/tags/)
    if ref.startswith("refs/heads/"):
        ref = ref[len("refs/heads/") :]
    elif ref.startswith("refs/tags/"):
        ref = ref[len("refs/tags/") :]
    if iid is None:
        omni.repo.man.print_log(
            f"Upstream pipeline {upstream_id} has no 'iid' or 'id'; cannot build version string",
            logging.ERROR,
        )
        sys.exit(1)

    # Fetch kit/VERSION at that commit (major.minor.patch)
    version_url = f"{KIT_GITLAB_BASE_URL}/omniverse/kit/-/raw/{sha}/{KIT_VERSION_PATH}"
    try:
        v_resp = requests.get(version_url, headers=headers, timeout=30)
        v_resp.raise_for_status()
        version_line = v_resp.text.strip().split("\n")[0].strip()
    except requests.RequestException as e:
        omni.repo.man.print_log(
            f"Failed to fetch kit/VERSION from upstream commit {sha}: {e}",
            logging.ERROR,
        )
        sys.exit(1)

    # Parse major.minor.patch
    parts = version_line.split(".")
    if len(parts) < 3:
        omni.repo.man.print_log(
            f"Invalid kit/VERSION content (expected major.minor.patch): {version_line!r}",
            logging.ERROR,
        )
        sys.exit(1)
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        omni.repo.man.print_log(
            f"Invalid kit/VERSION content (expected numeric major.minor.patch): {version_line!r}",
            logging.ERROR,
        )
        sys.exit(1)

    # Build number segment: {ref}.{pipeline_iid}.{githash_short} (full string is major.minor.patch+build_number)
    githash_short = sha[:8] if len(sha) >= 8 else sha
    build_number = f"{ref}.{iid}.{githash_short}"

    omni.repo.man.print_log(
        f"Using kit version from upstream pipeline {upstream_id} (commit {sha[:8]}): {major}.{minor}.{patch}+{build_number}",
        logging.INFO,
    )

    return {
        "major": major,
        "minor": minor,
        "patch": patch,
        "build_number": build_number,
        "githash": sha,
        "build_string": f"{major}.{minor}.{patch}+{build_number}",
        "build_location": "",
        "gitbranch": ref,
    }


def _parse_kit_version(kit_sdk_packman, template, exit_on_error=True):
    """Read kit version from kit_sdk_packman XML and substitute into template. Unchanged for non-downstream runs."""

    def get_by_index_or_default(elems, index, default):
        return elems[index] if len(elems) > index else default

    build_number = ""
    tree = ElementTree.parse(kit_sdk_packman)
    for dependency in tree.getroot().iter("dependency"):
        for package in dependency.iter("package"):
            if package.get("name").lower() in ["kit-sdk", "kit-kernel"]:
                build_number = (
                    package.get("version")
                    .replace(r".${platform}", "")
                    .replace(r".${platform_target_abi}", "")
                    .replace(r".${config}", "")
                )
    if not build_number:
        omni.repo.man.print_log(f"Unable to identify kit sdk/kernel version in {kit_sdk_packman}", logging.ERROR)
        if exit_on_error:
            sys.exit(1)
        return ""

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
    package_definitions,
    kit_sdk_packman,
    omniverse_kit_version,
    exit_on_error=True,
    print_errors=True,
    tokens_override=None,
):
    # get kit sdk/kernel build number (from file, or from upstream tokens when in downstream pipeline)
    if tokens_override is not None:
        target_version = string.Template(omniverse_kit_version).substitute(tokens_override)
    else:
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


_PLATFORM_TARGET_TO_ABI = {
    "linux-x86_64": "manylinux_2_35_x86_64",
    "linux-aarch64": "manylinux_2_35_aarch64",
    "windows-x86_64": "windows-x86_64",
}


def _pull_kit_sdk(kit_sdk_packman):
    """Pull the kit-sdk packman dependency so that its files are available locally."""
    try:
        import packmanapi

        host_platform = omni.repo.man.get_host_platform()
        platform_target_abi = _PLATFORM_TARGET_TO_ABI.get(host_platform, host_platform)
        omni.repo.man.print_log(
            f"Pulling kit-sdk packman dependency ({host_platform}/release) from {kit_sdk_packman}",
            logging.INFO,
        )
        packmanapi.pull(
            project_path=kit_sdk_packman,
            platform=platform_target_abi,
            include_tags=["release"],
            tokens={
                "config": "release",
                "platform_target": host_platform,
                "platform_target_abi": platform_target_abi,
            },
        )
    except Exception as e:
        omni.repo.man.print_log(f"Failed to pull kit-sdk via packman: {e}", logging.WARNING)


def _find_local_kit_dep(repo_root, platforms, filename, kit_sdk_packman=""):
    """Look for a Kit dependency file in the local kit build directory.

    The kit-kernel packman package is linked into _build/<platform>/<config>/kit/
    and ships pip dependency specs under dev/deps/.  If not found and kit_sdk_packman
    is provided, pulls the kit-sdk dependency via packman first.
    """

    def _search():
        for p in platforms:
            for cfg in ("release", "debug"):
                candidate = os.path.join(repo_root, "_build", p, cfg, "kit", "dev", "deps", filename)
                if os.path.isfile(candidate):
                    omni.repo.man.print_log(f"Using local kit dependency file: {candidate}", logging.INFO)
                    return candidate
        return None

    result = _search()
    if result:
        return result

    if kit_sdk_packman:
        _pull_kit_sdk(kit_sdk_packman)
        return _search()

    return None


def _check_dependencies(
    package_definitions,
    kit_sdk_packman,
    dependencies_files,
    platforms,
    tokens_override=None,
):
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
            # Try to find the file locally in the kit build directory before downloading.
            # The kit-kernel packman package is linked into _build/<platform>/<config>/kit/
            # and ships the pip dependency files under dev/deps/.
            repo_root = os.path.dirname(os.path.dirname(kit_sdk_packman))
            filename = os.path.basename(dependencies_file)
            local_path = _find_local_kit_dep(repo_root, platforms, filename, kit_sdk_packman=kit_sdk_packman)
            if local_path:
                path = local_path
            else:
                if tokens_override is not None:
                    url = string.Template(dependencies_file).substitute(tokens_override)
                else:
                    url = _parse_kit_version(kit_sdk_packman, dependencies_file, exit_on_error=False)
                if not url:
                    omni.repo.man.print_log(
                        f"Skipping dependency file {dependencies_file}: unable to parse kit version "
                        "(kit-sdk may not be built or the version may lack a valid git hash)",
                        logging.WARNING,
                    )
                    continue
                with tempfile.NamedTemporaryFile(delete=False, suffix=".toml") as file:
                    omni.repo.man.print_log(f"Downloading {url} to {file.name}", logging.INFO)
                    response = requests.get(url)
                    if response.status_code != 200:
                        omni.repo.man.print_log(
                            f"Skipping dependency file: failed to download {url} (HTTP {response.status_code}). "
                            "The kit-sdk version may not contain a valid git hash for resolving remote dependencies.",
                            logging.WARNING,
                        )
                        continue
                    file.write(response.content)
                    path = file.name
        # read dependencies file content
        target_dependencies = {platform: [] for platform in defined_platforms}
        omni.repo.man.print_log(f"Reading {path}", logging.INFO)
        with open(path, "rb") as file:
            try:
                content = tomli.load(file)
            except tomli.TOMLDecodeError as e:
                omni.repo.man.print_log(
                    f"Failed to parse {path} as TOML: {e}. "
                    "The downloaded file may not be valid TOML (e.g. an HTML error page). Skipping this dependencies file.",
                    logging.WARNING,
                )
                continue
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


VENV_DEPENDENCY_CHECK_DIR = "_env_dependency_check"


def _get_current_platform(platforms: List[str]) -> str:
    """Return the repo platform key for the current host. Exits with error if unsupported."""
    sys_name = platform_module.system()
    machine = platform_module.machine().lower()
    if sys_name == "Linux":
        if machine in ("x86_64", "amd64"):
            key = "linux-x86_64"
        elif machine in ("aarch64", "arm64"):
            key = "linux-aarch64"
        else:
            key = None
    elif sys_name == "Windows":
        if machine in ("x86_64", "amd64"):
            key = "windows-x86_64"
        else:
            key = None
    else:
        key = None
    if key is None or key not in platforms:
        omni.repo.man.print_log(
            f"Unsupported or unknown platform for --validate: system={sys_name!r}, machine={machine!r}. Supported: {platforms}",
            logging.ERROR,
        )
        sys.exit(1)
    return key


def _get_python312_executable(platform_key: str) -> str:
    """Return the Python 3.12 executable path for the given platform key."""
    if platform_key == "windows-x86_64":
        return os.environ.get("PYTHON_3_12", "C:\\Python312\\python.exe")
    return os.environ.get("PYTHON_3_12", "python3.12")


def _run_validate(platform_key: str, requirements_path: str, python_exe: str) -> None:
    """
    Create a fresh venv, upgrade pip, and install from the generated requirements file.
    Exits nonzero on any failure.
    """
    venv_dir = os.path.abspath(VENV_DEPENDENCY_CHECK_DIR)
    if os.path.isdir(venv_dir):
        omni.repo.man.print_log(f"Removing existing {venv_dir}", logging.INFO)
        shutil.rmtree(venv_dir)

    omni.repo.man.print_log(f"Creating virtual environment at {venv_dir}", logging.INFO)
    subprocess.run(
        [python_exe, "-m", "venv", venv_dir],
        check=True,
        capture_output=False,
    )

    if platform_key == "windows-x86_64":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")

    # Use "python -m pip" instead of pip.exe to avoid Windows self-upgrade failures
    omni.repo.man.print_log("Upgrading pip", logging.INFO)
    subprocess.run(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        capture_output=False,
    )

    omni.repo.man.print_log(f"Installing dependencies from {requirements_path}", logging.INFO)
    subprocess.run(
        [venv_python, "-m", "pip", "install", "-r", requirements_path],
        check=True,
        capture_output=False,
    )
    omni.repo.man.print_log("Dependency validation passed", logging.INFO)


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
        help="Enable GitLab CI mode: use kit version from upstream pipeline when CI_PIPELINE_SOURCE=pipeline and UPSTREAM_PIPELINE_ID set; ignore errors during dependabot kit-sdk updates",
    )
    parser.add_argument(
        "--validate",
        required=False,
        default=False,
        action="store_true",
        help="For the current platform: run checks, generate python-package-requirements file, create _env_dependency_check venv with Python 3.12, install dependencies, and pass/fail",
    )

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_check_python_package_definitions"]
        python_package_tool_config = config.get("repo_python_package", {})

        # Only when we are in a downstream pipeline do we use upstream kit version; otherwise behavior is unchanged.
        upstream_tokens = None
        if (
            options.gitlab
            and os.getenv("CI_PIPELINE_SOURCE") == "pipeline"
            and os.getenv("UPSTREAM_PIPELINE_ID", "").strip()
        ):
            upstream_tokens = _get_upstream_kit_tokens()

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
                tokens_override=upstream_tokens,
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
            tokens_override=upstream_tokens,
        )
        _check_extensions(package_definitions, tool_config["extension_folder"], tool_config["excluded_extensions"])
        _check_dependencies(
            package_definitions,
            tool_config["kit_sdk_packman"],
            tool_config["dependencies_files"],
            platforms,
            tokens_override=upstream_tokens,
        )

        if options.validate:
            platform_key = _get_current_platform(platforms)
            requirements_path = os.path.abspath(f"python-package-requirements-{platform_key}.txt")
            if not os.path.isfile(requirements_path):
                omni.repo.man.print_log(
                    f"Requirements file not found: {requirements_path}",
                    logging.ERROR,
                )
                sys.exit(1)
            python_exe = _get_python312_executable(platform_key)
            _run_validate(platform_key, requirements_path, python_exe)

    return run_repo_tool
