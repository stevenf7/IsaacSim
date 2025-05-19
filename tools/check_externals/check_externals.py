import argparse
import fnmatch
import json
import os
import platform
import xml.etree.ElementTree as ET
from collections import defaultdict
from glob import glob

import packmanapi

# Add argument parsing
parser = argparse.ArgumentParser(description="Check packman external dependencies and licenses.")
parser.add_argument(
    "--file", "-f", help="Specific packman XML file to scan. If not provided, scans all files in ./deps/*.packman.xml"
)
parser.add_argument(
    "--package", "-p", help="Specific package name to check licenses for. If not provided, checks all packages."
)
args = parser.parse_args()

# Detect platform
system = platform.system().lower()
if system == "linux":
    platform = "manylinux_2_35_x86_64"
    platform_target = "linux-x86_64"
elif system == "windows":
    platform = "windows-x86_64"
    platform_target = "windows-x86_64"
else:
    raise RuntimeError(f"Unsupported platform: {system}")


def find_license_file(link_path, package_name):
    """Search for license files in common locations."""
    possible_patterns = [
        f"PACKAGE-LICENSES/{package_name}-LICENSE*",  # Package-specific licenses first
        f"PACKAGE-LICENSES/{package_name.lower()}-LICENSE*",
        "LICENSE*",  # Root licenses next
        "*.LICENSE",
        "*.license",
        "COPYING*",
        "PACKAGE-LICENSES/*LICENSE*",  # Generic package licenses last
        "licenses/LICENSE*",
        "LICENSES/*",
    ]

    NVIDIA_PROPRIETARY_TEXT = [
        # First format
        """NVIDIA CORPORATION and its licensors retain all intellectual property
and proprietary rights in and to this software, related documentation
and any modifications thereto.  Any use, reproduction, disclosure or
distribution of this software and related documentation without an express
license agreement from NVIDIA CORPORATION is strictly prohibited.""",
        # Second format
        """NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
property and proprietary rights in and to this material, related
documentation and any modifications thereto. Any use, reproduction,
disclosure or distribution of this material and related documentation
without an express license agreement from NVIDIA CORPORATION or
its affiliates is strictly prohibited.""",
    ]

    MIT_LICENSE_TEXT = [
        # First paragraph
        """Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:""",
        # Key phrases that indicate MIT license
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND',
        "INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY",
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT",
    ]

    # Replace variables in link_path
    link_path = link_path.replace("${config}", "release")
    link_path = link_path.replace("${platform_target}", platform_target)
    link_path = link_path.replace("${platform_target_abi}", platform_target)

    # Make path absolute if relative, starting from project root
    if link_path.startswith("../"):
        # Get the project root (parent of deps directory)
        script_dir = os.path.dirname(os.path.abspath(__file__))  # tools/check_externals
        project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels to project root
        link_path = os.path.abspath(os.path.join(project_root, link_path.lstrip("../")))

    print(f"Searching for license files for {package_name} in {link_path}")
    all_matches = set()
    package_specific_matches = set()
    root_license_matches = set()

    # First pass: categorize files without scanning content
    for pattern in possible_patterns:
        full_pattern = os.path.join(link_path, pattern)
        matches = glob(full_pattern, recursive=True)
        matches = [m for m in matches if os.path.isfile(m)]
        print(f"  Trying pattern: {full_pattern}, found {len(matches)} matches")
        for match in matches:
            rel_path = os.path.relpath(match)

            # Skip PIP-packages-LICENSES.txt and duplicates
            if os.path.basename(match) == "PIP-packages-LICENSES.txt":
                print(f"    Skipping PIP packages license file: {rel_path}")
                continue
            if rel_path in all_matches:
                print(f"    Skipping exact duplicate: {rel_path}")
                continue

            # Categorize the file
            if package_name.lower() in os.path.basename(match).lower():
                package_specific_matches.add(rel_path)
            elif os.path.basename(match) == "LICENSE.txt":
                # Check if this is directly in the package directory (not in a subdirectory)
                match_dir = os.path.dirname(os.path.abspath(match))
                package_dir = os.path.abspath(link_path)
                if match_dir == package_dir:
                    print(f"    Found root license for package: {rel_path}")
                    root_license_matches.add(rel_path)
                else:
                    all_matches.add(rel_path)
            else:
                all_matches.add(rel_path)

    # Second pass: scan content of relevant files
    spdx_matches = []
    nvidia_proprietary_matches = []
    mit_license_matches = []

    files_to_scan = package_specific_matches or root_license_matches or all_matches
    for rel_path in files_to_scan:
        print(f"Checking {rel_path} for specific licenses")
        try:
            with open(rel_path, "r", encoding="utf-8") as f:
                content = f.read()
                content_normalized = content.replace("\n", " ").strip()
                if any(text.replace("\n", " ").strip() in content_normalized for text in NVIDIA_PROPRIETARY_TEXT):
                    print("      Found NVIDIA proprietary match!")
                    nvidia_proprietary_matches.append(rel_path)
                if any(indicator.replace("\n", " ").strip() in content_normalized for indicator in MIT_LICENSE_TEXT):
                    print("      Found MIT license match!")
                    mit_license_matches.append(rel_path)
                if "SPDX-License-Identifier:" in content:
                    spdx_line = next(line for line in content.splitlines() if "SPDX-License-Identifier:" in line)
                    spdx_type = spdx_line.split("SPDX-License-Identifier:", 1)[1].strip()
                    spdx_matches.append((rel_path, spdx_type))
        except Exception as e:
            print(f"    Warning: Could not check {rel_path} for license info: {e}")

    # Return results in priority order
    if len(nvidia_proprietary_matches) == 1:
        return {"type": "NVIDIA proprietary", "location": nvidia_proprietary_matches[0]}
    elif len(nvidia_proprietary_matches) > 1:
        print(f"    Found multiple NVIDIA proprietary licenses for {package_name}")

    if len(mit_license_matches) == 1:
        return {"type": "MIT", "location": mit_license_matches[0]}
    elif len(mit_license_matches) > 1:
        print(f"    Found multiple MIT licenses for {package_name}")

    if len(spdx_matches) == 1:
        return {"type": spdx_matches[0][1], "location": spdx_matches[0][0]}
    elif len(spdx_matches) > 1:
        print(f"    Found multiple SPDX identifiers for {package_name}")

    # If no special licenses found, return file lists in priority order
    if package_specific_matches:
        return sorted(package_specific_matches)
    if root_license_matches:
        return [next(iter(sorted(root_license_matches)))]
    return sorted(all_matches) if all_matches else None


def matches_current_platform(package, current_platform):
    """Check if a package matches the current platform.

    Args:
        package: XML package element
        current_platform: String representing current platform (e.g. 'windows-x86_64')

    Returns:
        bool: True if package matches current platform, False otherwise
    """
    platforms = package.get("platforms", "")
    if not platforms:
        return True  # If no platforms specified, assume it matches all
    platform_list = platforms.split()
    return current_platform in platform_list


# Get list of files to process
if args.file:
    if not os.path.exists(args.file):
        raise FileNotFoundError(f"Specified file not found: {args.file}")
    files = [args.file]
else:
    files = glob("./deps/*.packman.xml")

# Define configs to check
configs = ["release", "debug"]

results_by_file = defaultdict(lambda: defaultdict(list))  # Nested defaultdict for file->config->results
deps_count_by_file = defaultdict(lambda: defaultdict(int))  # Nested defaultdict for file->config->count
json_output = defaultdict(dict)  # Nested dict for file->config->data
full_package_listing = defaultdict(lambda: defaultdict(list))  # Nested defaultdict for file->config->packages

for file in files:
    tree = ET.parse(file)
    root = tree.getroot()

    for config in configs:
        print(f"\nChecking {file} with config: {config}")

        # Only count packages that match our platform
        total_deps = sum(
            1
            for dep in root.findall(".//dependency")
            for pkg in dep.findall("package")
            if matches_current_platform(pkg, platform)
        )
        deps_count_by_file[file][config] = total_deps
        full_package_listing[file][config] = []

        # Create mapping of package name to link path
        package_paths = {}
        for dep in root.findall(".//dependency"):
            link_path = dep.get("linkPath")
            for pkg in dep.findall("package"):
                if matches_current_platform(pkg, platform):
                    package_paths[pkg.get("name")] = link_path

        _, results = packmanapi.verify(
            file,
            exclude_local=True,
            remotes=["cloudfront"],
            tokens={"config": config, "platform_target": platform_target, "platform_target_abi": platform_target},
            platform=platform,
            tags={"public": "true"},
        )

        results_by_file[file][config] = results

        # Update the package listing
        for dependency in root.findall(".//dependency"):
            for package in dependency.findall("package"):
                if matches_current_platform(package, platform):
                    name = package.get("name")
                    version = package.get("version", "")
                    # Replace variables in version string
                    version = version.replace("${config}", config)
                    version = version.replace("${platform_target}", platform_target)
                    version = version.replace("${platform_target_abi}", platform_target)

                    package_info = {
                        "name": name,
                        "version": version,
                        "license_file": (
                            find_license_file(package_paths.get(name, ""), name)
                            if not args.package or name == args.package
                            else None
                        ),
                    }
                    full_package_listing[file][config].append(package_info)

        # Prepare JSON output for this file and config
        json_output[file][config] = {
            "problem_packages": [
                {
                    "name": result[1].name,
                    "version": result[1].version,
                }
                for result in results
            ],
        }

# Update summary output
total_issues = 0
total_deps = 0
print("\nSummary of issues:")
print("-" * 80)
for file in sorted(results_by_file.keys()):
    print(f"\n{file}:")
    for config in configs:
        issues = results_by_file[file][config]
        total_issues += len(issues)
        total_deps += deps_count_by_file[file][config]
        print(
            f"  {config}: {len(issues)} issue{'s' if len(issues) != 1 else ''} out of {deps_count_by_file[file][config]} dependencies"
        )

print(f"\nTotal issues found: {total_issues} across {total_deps} total dependencies")

# Write both JSON outputs
with open("packman_verification_results.json", "w") as f:
    json.dump(json_output, f, indent=2)

with open("packman_full_results.json", "w") as f:
    json.dump(full_package_listing, f, indent=2)

# Write CSV output
with open("packman_full_results.csv", "w") as f:
    f.write("Package Name,Version,Public/Private,License Files,License Type\n")

    # Create a dictionary to track unique package entries
    unique_packages = {}

    for file in full_package_listing:
        # First collect all packages from both configs
        for config in configs:
            private_packages = {pkg["name"] for pkg in json_output[file][config]["problem_packages"]}

            for package in full_package_listing[file][config]:
                name = package["name"]
                version = package["version"]
                is_public = "private" if name in private_packages else "public"

                # Create a key for the package based on its identifying information
                package_key = (name, version)

                # Store package info if we haven't seen it before
                if package_key not in unique_packages:
                    # Handle license file info
                    license_info = package.get("license_file")
                    if not license_info:
                        license_files = ""
                        license_type = ""
                    elif isinstance(license_info, list):
                        license_files = ";".join(license_info)
                        license_type = ""
                    elif isinstance(license_info, dict):
                        license_files = license_info["location"]
                        license_type = license_info.get("type", "")
                    else:
                        license_files = str(license_info)
                        license_type = ""

                    unique_packages[package_key] = {
                        "name": name,
                        "version": version,
                        "public_private": is_public,
                        "license_files": license_files,
                        "license_type": license_type,
                    }

    # Write unique packages to CSV
    for package_info in unique_packages.values():
        f.write(
            f"{package_info['name']},{package_info['version']},"
            f"{package_info['public_private']},{package_info['license_files']},"
            f"{package_info['license_type']}\n"
        )

print("\nDetailed results written to packman_verification_results.json")
print("Full package listing written to packman_full_results.json")
print("CSV summary written to packman_full_results.csv")

# If we have anything in here then we failed verification
exit(total_issues)
