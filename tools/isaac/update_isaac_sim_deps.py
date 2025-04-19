#!/usr/bin/env python3
import argparse
import glob
import os
import re
import subprocess
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


def extract_package_names(xml_file):
    """Extract package names from an XML file.

    The function searches for package tags in the XML file and extracts
    the name attribute values from each package.

    Args:
        xml_file: Path to the XML file to extract package names from.

    Returns:
        A list of package names found in the file.

    Example:

    .. code-block:: python

        >>> extract_package_names("deps/isaac-sim.packman.xml")
        ['nv_ros2', 'lula', 'octomap', 'tinyxml2', 'doctest', 'openssl', 'omniisaacsimschemas_openusd_0.24.05_py_3.11', 'nlohmann_json', 'generic-model-output', 'rapidjson']
    """
    package_names = set()

    with open(xml_file, "r") as f:
        content = f.read()

    # Extract package names
    pattern = r'<package\s+name="([^"]+)"'
    matches = re.finditer(pattern, content)

    for match in matches:
        package_name = match.group(1)
        # Skip versions with variables as they can't be updated directly
        if "${" in package_name or "}" in package_name:
            continue
        package_names.add(package_name)

    return list(package_names)


def update_packages_with_repo_sh(package_names, repo_root):
    """Run repo.sh update for each package.

    The function executes the repo.sh update command for each package name
    in the provided list.

    Args:
        package_names: List of package names to update.
        repo_root: Path to the repository root directory.

    Returns:
        True if all commands executed successfully, False if any command failed.

    Example:

    .. code-block:: python

        >>> update_packages_with_repo_sh(['nv_ros2_humble', 'lula'], '/path/to/repo')
        Running: /path/to/repo/repo.sh update nv_ros2_humble
        Running: /path/to/repo/repo.sh update lula
        True
    """
    success = True
    repo_script = os.path.join(repo_root, "repo.sh")

    if not os.path.exists(repo_script):
        print(f"Error: repo.sh not found at {repo_script}")
        return False

    for package in package_names:
        print(f"Running: {repo_script} update {package}")
        try:
            result = subprocess.run(
                [repo_script, "update", package], check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error updating package {package}:")
            print(e.stderr)
            success = False

    return success


def main():
    """Main function that handles different modes of operation.

    The function supports two modes:
    1. Default mode (--mode=version): Updates generic-model-output version in isaac-sim.packman.xml
    2. Repo update mode (--mode=update): Extracts package names from all XML files and runs repo.sh update

    Raises:
        SystemExit: If required files are not found or if an invalid mode is specified.

    Example:

    .. code-block:: python

        >>> main()  # Default mode
        Extracted kit version: 107.3.0+master.187456.39f199e7
        Successfully updated generic-model-output version in /path/to/deps/isaac-sim.packman.xml

        >>> # With update mode
        >>> main(['--mode', 'update'])
        Found 7 XML files in deps directory
        Extracted 15 unique package names
        Running: /path/to/repo.sh update nv_ros2_humble
        ...
    """
    parser = argparse.ArgumentParser(description="Update Isaac Sim dependencies")
    parser.add_argument(
        "--mode",
        choices=["version", "update"],
        default="version",
        help="Operation mode: version (update version in isaac-sim.packman.xml) or "
        "update (run repo.sh update for each package)",
    )

    args = parser.parse_args()

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))  # Assuming script is in tools/isaac/
    deps_dir = os.path.join(repo_root, "deps")

    if args.mode == "version":
        # Original functionality: update version in isaac-sim.packman.xml
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

    elif args.mode == "update":
        # New functionality: extract package names and run repo.sh update
        xml_files = glob.glob(os.path.join(deps_dir, "*.packman.xml"))

        if not xml_files:
            print(f"Error: No XML files found in {deps_dir}")
            sys.exit(1)

        print(f"Found {len(xml_files)} XML files in deps directory")

        # Extract package names from all XML files
        all_packages = set()
        for xml_file in xml_files:
            package_names = extract_package_names(xml_file)
            all_packages.update(package_names)

        print(f"Extracted {len(all_packages)} unique package names")

        # Run repo.sh update for each package
        if update_packages_with_repo_sh(list(all_packages), repo_root):
            print("Successfully updated all packages")
        else:
            print("Some packages failed to update")
            sys.exit(1)


if __name__ == "__main__":
    main()
