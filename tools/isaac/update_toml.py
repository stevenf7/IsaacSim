# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import re
import sys
from collections import defaultdict


def parse_requirements(requirements_file):
    """Parse the requirements.txt file to get package versions."""
    package_versions = {}
    cuda_version_map = {}

    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Handle special cases like git+ URLs
                if "==" in line and not line.startswith("git+"):
                    package, version = line.split("==", 1)
                    package_versions[package.lower()] = version

                    # Special handling for NVIDIA CUDA packages to track CUDA versions
                    # Example: nvidia-cublas-cu12-12.6.4.1 -> base: nvidia-cublas, cuda: cu12
                    if package.startswith("nvidia-") and "-cu" in package:
                        base_pkg, cuda_ver = package.rsplit("-cu", 1)
                        cuda_ver = "cu" + cuda_ver
                        cuda_version_map[base_pkg] = cuda_ver

    return package_versions, cuda_version_map


def strip_local_version(version):
    """Strip the local version segment (everything after '+') from a version string."""
    return version.split("+")[0]


def format_version(new_version, old_version):
    """Format new_version to match the style of old_version.

    If old_version has no local segment (no '+'), strip local segment from new_version.
    """
    if "+" not in old_version and "+" in new_version:
        return strip_local_version(new_version)
    return new_version


def update_toml_file(toml_file, package_versions, cuda_version_map):
    """Update the versions in the TOML file while preserving structure and comments."""
    with open(toml_file, "r") as f:
        lines = f.readlines()

    updated_packages = defaultdict(list)
    in_array_block = False
    modified_lines = []
    debug_packages = []

    for line in lines:
        stripped = line.strip()

        # Detect start of a TOML array block (e.g. "packages = [" or "pyproject.dependencies.linux-x86_64 = [")
        if not in_array_block and "= [" in line and not stripped.startswith("#"):
            in_array_block = True
            modified_lines.append(line)
            # Check if the array is single-line (opens and closes on same line)
            if stripped.endswith("]"):
                in_array_block = False
            continue

        # Detect end of array block
        if in_array_block and "]" in line and not stripped.startswith("#"):
            bracket_content = stripped.lstrip()
            if bracket_content.startswith("]"):
                in_array_block = False
                modified_lines.append(line)
                continue

        if in_array_block:
            if stripped.startswith("#") or not stripped:
                modified_lines.append(line)
                continue

            debug_packages.append(stripped)

            match = re.search(r'"([^=<>]+)(?:==|>=|<=|>|<)([^=<>]+)"', line)

            if match:
                pkg_name, old_version = match.groups()
                pkg_name = pkg_name.strip().lower()
                base_pkg_name = strip_local_version(pkg_name) if "+" in pkg_name else pkg_name

                found_match = False

                # Direct version match (exact package name in pip freeze)
                if pkg_name in package_versions:
                    new_version = format_version(package_versions[pkg_name], old_version)
                    updated_line = update_package_line(line, pkg_name, old_version, new_version)
                    modified_lines.append(updated_line)
                    updated_packages[pkg_name].append((old_version, new_version))
                    found_match = True

                # Match by base name without local version (e.g. "torch" matches "torch==2.11.0+cu130")
                elif base_pkg_name != pkg_name and base_pkg_name in package_versions:
                    new_version = format_version(package_versions[base_pkg_name], old_version)
                    updated_line = update_package_line(line, pkg_name, old_version, new_version)
                    modified_lines.append(updated_line)
                    updated_packages[base_pkg_name].append((old_version, new_version))
                    found_match = True

                # NVIDIA packages with different CUDA versions (e.g. -cu12 -> -cu13)
                elif pkg_name.startswith("nvidia-") and "-cu" in pkg_name:
                    base_pkg, old_cuda_ver = pkg_name.rsplit("-cu", 1)
                    old_cuda_ver = "cu" + old_cuda_ver

                    if base_pkg in cuda_version_map:
                        new_cuda_ver = cuda_version_map[base_pkg]
                        new_pkg_name = f"{base_pkg}-{new_cuda_ver}"

                        if new_pkg_name in package_versions:
                            new_version = format_version(package_versions[new_pkg_name], old_version)
                            updated_line = update_package_line(line, pkg_name, old_version, new_version, new_pkg_name)
                            modified_lines.append(updated_line)
                            updated_packages[new_pkg_name].append(
                                (f"{pkg_name}=={old_version}", f"{new_pkg_name}=={new_version}")
                            )
                            found_match = True

                if not found_match:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    with open(toml_file, "w") as f:
        f.writelines(modified_lines)

    print("\nPackage version updates:")
    if updated_packages:
        for pkg, versions in updated_packages.items():
            for old_ver, new_ver in versions:
                print(f"  {old_ver} -> {new_ver}")
    else:
        print("  No packages were updated.")

    print("\nDebug: Packages in TOML file:")
    for pkg in debug_packages:
        print(f"  {pkg}")

    print("\nDebug: Available packages from pip freeze:")
    for pkg in sorted(package_versions.keys()):
        print(f"  {pkg}=={package_versions[pkg]}")


def update_package_line(line, pkg_name, old_version, new_version, new_pkg_name=None):
    """Update the package line with the new version, preserving formatting."""
    prefix = line[: line.find('"')]
    suffix = line[line.rfind('"') + 1 :]

    if new_pkg_name:
        # Replace both package name and version
        updated_line = f'{prefix}"{new_pkg_name}=={new_version}"{suffix}'
    else:
        # Replace version only
        updated_line = f'{prefix}"{pkg_name}=={new_version}"{suffix}'

    return updated_line


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <requirements_file> <toml_file>")
        sys.exit(1)

    requirements_file = sys.argv[1]
    toml_file = sys.argv[2]

    package_versions, cuda_version_map = parse_requirements(requirements_file)
    update_toml_file(toml_file, package_versions, cuda_version_map)


if __name__ == "__main__":
    main()
