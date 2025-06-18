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
import os
import re
import sys


def extract_kit_version(file_path):
    """Extract the kit version from kit-sdk.packman.xml.

    The function searches for the kit-kernel version pattern in the file and extracts
    the core version part (e.g., "107.3.0+master.187456.39f199e7").

    Args:
        file_path: Path to the kit-sdk.packman.xml file.

    Returns:
        The extracted kit version string.

    Raises:
        SystemExit: If the version cannot be extracted from the file.

    Example:

    .. code-block:: python

        >>> extract_kit_version("deps/kit-sdk.packman.xml")
        '107.3.0+master.187456.39f199e7'
    """
    with open(file_path, "r") as f:
        content = f.read()

    # Look for the kit-kernel version pattern
    pattern = r'name="kit-kernel"\s+version="([^"]+)"'
    match = re.search(pattern, content)

    if match:
        full_version = match.group(1)
        # Extract base version pattern (e.g., "107.3.0+master.187456.39f199e7")
        base_version_pattern = r"(\d+\.\d+\.\d+\+\w+\.\d+\.[0-9a-f]+)"
        base_version_match = re.search(base_version_pattern, full_version)

        if base_version_match:
            return base_version_match.group(1)

    print("Error: Could not extract kit version from kit-sdk.packman.xml")
    sys.exit(1)


def update_isaac_sim_version(file_path, new_version):
    """Update the generic-model-output version in isaac-sim.packman.xml.

    The function finds the generic-model-output package entry and updates its version
    to match the specified new version while preserving the rest of the version string.

    Args:
        file_path: Path to the isaac-sim.packman.xml file.
        new_version: The new version string to be used.

    Returns:
        True if the update was successful, False otherwise.

    Example:

    .. code-block:: python

        >>> update_isaac_sim_version("deps/isaac-sim.packman.xml", "107.3.0+master.187456.39f199e7")
        True
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if 'name="generic-model-output"' in line and "version=" in line:
            # Extract the current version pattern
            current_version_match = re.search(r'version="([^"]+)"', line)
            if current_version_match:
                current_version = current_version_match.group(1)
                # Extract base version pattern from current version
                base_version_pattern = r"(\d+\.\d+\.\d+\+\w+\.\d+\.[0-9a-f]+)"
                base_version_match = re.search(base_version_pattern, current_version)

                if base_version_match:
                    # Replace only the base version part while keeping the rest
                    new_full_version = current_version.replace(base_version_match.group(1), new_version)
                    lines[i] = line.replace(f'version="{current_version}"', f'version="{new_full_version}"')
                    updated = True
                    break

    if not updated:
        print("Warning: Could not find the generic-model-output version pattern.")
        return False

    with open(file_path, "w") as f:
        f.writelines(lines)

    return True


def main():
    """Main function that updates generic-model-output version in isaac-sim.packman.xml.

    The function extracts the kit version from kit-sdk.packman.xml and updates
    the generic-model-output version in isaac-sim.packman.xml to match.

    Raises:
        SystemExit: If required files are not found.

    Example:

    .. code-block:: python

        >>> main()
        Extracted kit version: 107.3.0+master.187456.39f199e7
        Successfully updated generic-model-output version in /path/to/deps/isaac-sim.packman.xml
    """
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))  # Assuming script is in tools/isaac/
    deps_dir = os.path.join(repo_root, "deps")

    # Paths to required files
    kit_sdk_path = os.path.join(deps_dir, "kit-sdk.packman.xml")
    isaac_sim_path = os.path.join(deps_dir, "isaac-sim.packman.xml")

    # Check if files exist
    if not os.path.exists(kit_sdk_path):
        print(f"Error: File not found: {kit_sdk_path}")
        sys.exit(1)

    if not os.path.exists(isaac_sim_path):
        print(f"Error: File not found: {isaac_sim_path}")
        sys.exit(1)

    # Extract kit version
    kit_version = extract_kit_version(kit_sdk_path)
    print(f"Extracted kit version: {kit_version}")

    # Update isaac-sim.packman.xml
    if update_isaac_sim_version(isaac_sim_path, kit_version):
        print(f"Successfully updated generic-model-output version in {isaac_sim_path}")
    else:
        print("Failed to update version.")
        sys.exit(1)


if __name__ == "__main__":
    main()
