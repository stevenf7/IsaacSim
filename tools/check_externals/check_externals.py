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

            # Skip duplicates
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


# Get list of files to process
if args.file:
    if not os.path.exists(args.file):
        raise FileNotFoundError(f"Specified file not found: {args.file}")
    files = [args.file]
else:
    files = glob("./deps/*.packman.xml")

results_by_file = defaultdict(list)
deps_count_by_file = {}
json_output = {}
full_package_listing = {}

for file in files:
    tree = ET.parse(file)
    root = tree.getroot()
    total_deps = len(root.findall(".//dependency"))
    deps_count_by_file[file] = total_deps

    # Create mapping of package name to link path
    package_paths = {}
    for dep in root.findall(".//dependency"):
        link_path = dep.get("linkPath")
        for pkg in dep.findall(".//package"):
            package_paths[pkg.get("name")] = link_path

    _, results = packmanapi.verify(
        file,
        exclude_local=True,
        remotes=["cloudfront"],
        tokens={"config": "release", "platform_target": platform_target, "platform_target_abi": platform_target},
        platform=platform,
        tags={"public": "true"},
    )

    print(f"Scanned {file} for packman dependencies, {len(results)} issue{'s' if len(results) != 1 else ''} found")

    results_by_file[file] = results

    # Store full package listing from results with license info
    full_package_listing[file] = [
        {
            "name": result[1].name,
            "version": result[1].version,
            **(
                {"license_file": find_license_file(package_paths.get(result[1].name, ""), result[1].name)}
                if not args.package or result[1].name == args.package
                else {}
            ),
        }
        for result in results
    ]

    # Prepare JSON output for this file
    json_output[file] = {
        "total_dependencies": total_deps,
        "issues_count": len(results),
        "problem_packages": [
            {
                "name": result[1].name,
                "version": result[1].version,
                **(
                    {"license_file": find_license_file(package_paths.get(result[1].name, ""), result[1].name)}
                    if not args.package or result[1].name == args.package
                    else {}
                ),
            }
            for result in results
        ],
    }

total_issues = 0
total_deps = 0
print("\nSummary of issues:")
print("-" * 80)
for file in sorted(results_by_file.keys()):
    issues = results_by_file[file]
    total_issues += len(issues)
    total_deps += deps_count_by_file[file]
    print(f"\n{file}:")
    print(f"  {len(issues)} issue{'s' if len(issues) != 1 else ''} out of {deps_count_by_file[file]} dependencies")

print(f"\nTotal issues found: {total_issues} across {total_deps} total dependencies")

# Write both JSON outputs
with open("packman_verification_results.json", "w") as f:
    json.dump(json_output, f, indent=2)

with open("packman_full_results.json", "w") as f:
    json.dump(full_package_listing, f, indent=2)

print("\nDetailed results written to packman_verification_results.json")
print("Full package listing written to packman_full_results.json")

# If we have anything in here then we failed verification
exit(total_issues)
