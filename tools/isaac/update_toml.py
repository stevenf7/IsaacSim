#!/usr/bin/env python3

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


def update_toml_file(toml_file, package_versions, cuda_version_map):
    """Update the versions in the TOML file while preserving structure and comments."""
    with open(toml_file, "r") as f:
        lines = f.readlines()

    # Keep track of updated packages
    updated_packages = defaultdict(list)
    in_dependency_section = False
    in_packages_block = False
    modified_lines = []
    debug_packages = []  # For debugging

    for line in lines:
        # Check if we're entering a new dependency section
        if "[[dependency]]" in line:
            in_dependency_section = True
            in_packages_block = False
            modified_lines.append(line)
            continue

        # Check if we're in a packages block inside a dependency section
        if in_dependency_section and "packages = [" in line:
            in_packages_block = True
            modified_lines.append(line)
            continue

        # Check if we're at the end of a packages block
        if in_packages_block and "]" in line and not line.strip().startswith("#"):
            in_packages_block = False
            modified_lines.append(line)
            continue

        # Process lines in a packages block
        if in_packages_block:
            # Skip comment lines or empty lines
            if line.strip().startswith("#") or not line.strip():
                modified_lines.append(line)
                continue

            # Add line to debug output for troubleshooting
            debug_packages.append(line.strip())

            # Check if this line contains a package definition
            match = re.search(r'"([^=<>]+)(?:==|>=|<=|>|<)([^=<>]+)"', line)

            if match:
                pkg_name, old_version = match.groups()
                pkg_name = pkg_name.strip().lower()

                # Check for direct version match
                found_match = False
                if pkg_name in package_versions:
                    new_version = package_versions[pkg_name]
                    updated_line = update_package_line(line, pkg_name, old_version, new_version)
                    modified_lines.append(updated_line)
                    updated_packages[pkg_name].append((old_version, new_version))
                    found_match = True

                # Special handling for NVIDIA packages with different CUDA versions
                elif pkg_name.startswith("nvidia-") and "-cu" in pkg_name:
                    base_pkg, old_cuda_ver = pkg_name.rsplit("-cu", 1)
                    old_cuda_ver = "cu" + old_cuda_ver

                    # Check if we have the base package with a different CUDA version
                    if base_pkg in cuda_version_map:
                        new_cuda_ver = cuda_version_map[base_pkg]
                        new_pkg_name = f"{base_pkg}-{new_cuda_ver}"

                        if new_pkg_name in package_versions:
                            new_version = package_versions[new_pkg_name]
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

            # Reset dependency section flag if we're at a blank line after a dependency section
            if in_dependency_section and not line.strip() and not in_packages_block:
                # This is a heuristic - a blank line might indicate end of a section
                in_dependency_section = False

    # Write the modified content back to the file
    with open(toml_file, "w") as f:
        f.writelines(modified_lines)

    # Print a summary of the changes
    print("\nPackage version updates:")
    if updated_packages:
        for pkg, versions in updated_packages.items():
            for old_ver, new_ver in versions:
                print(f"  {old_ver} -> {new_ver}")
    else:
        print("  No packages were updated.")

    # Debug output
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
