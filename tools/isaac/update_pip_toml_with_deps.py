#!/usr/bin/env python3
"""Script to update deps/pip.toml with extension usage and transitive dependency comments."""

import json
import re
from pathlib import Path


def load_package_info(json_file: str) -> dict:
    """Load the package info with dependencies from JSON file."""
    with open(json_file, "r") as f:
        data = json.load(f)
    return data["package_info"]


def extract_package_name(package_line: str) -> str:
    """Extract package name from a pip.toml package line.

    Args:
        package_line: Line like '"numba==0.59.1",' or '"boto3",'

    Returns:
        Package name in lowercase (e.g., 'numba', 'boto3')
    """
    # Extract content between quotes
    match = re.search(r'"([^"]+)"', package_line)
    if match:
        package_spec = match.group(1)
        # Remove version specifiers
        package_name = re.split(r"[=<>!~\[]", package_spec)[0].strip()
        return package_name.lower()
    return None


def update_pip_toml(toml_file: str, package_info: dict):
    """Update pip.toml file with extension usage and dependency comments.

    Args:
        toml_file: Path to the pip.toml file
        package_info: Dictionary mapping package names to info dicts with extensions and dependencies
    """
    with open(toml_file, "r") as f:
        lines = f.readlines()

    # First pass: identify sections and calculate column widths per section
    sections = []  # List of (start_idx, end_idx, max_len) for each dependency section
    current_section_start = None
    current_section_packages = []

    for i, line in enumerate(lines):
        # Check if we're starting a new dependency section
        if "[[dependency]]" in line:
            # Save previous section if exists
            if current_section_start is not None and current_section_packages:
                max_len = max(len(pkg) for pkg in current_section_packages)
                sections.append((current_section_start, i - 1, max_len))
            current_section_start = i
            current_section_packages = []

        # Check if this is a package line
        if '"' in line and ("SWIPAT filed under:" in line or "SWIPAT:" in line):
            match = re.match(r'^(\s*"[^"]+",?\s*)', line)
            if match:
                package_part = match.group(1).rstrip()
                current_section_packages.append(package_part)

    # Save the last section
    if current_section_start is not None and current_section_packages:
        max_len = max(len(pkg) for pkg in current_section_packages)
        sections.append((current_section_start, len(lines) - 1, max_len))

    # Create a lookup for max_len by line index
    line_to_max_len = {}
    for start_idx, end_idx, max_len in sections:
        for i in range(start_idx, end_idx + 1):
            line_to_max_len[i] = max_len

    # Second pass: update lines with proper formatting
    updated_lines = []
    for i, line in enumerate(lines):
        updated_line = line

        # Check if this line contains a package definition with a SWIPAT comment (any format)
        if '"' in line and ("SWIPAT filed under:" in line or "SWIPAT:" in line):
            package_name = extract_package_name(line)

            if package_name and package_name in package_info:
                info = package_info[package_name]
                extensions = info["extensions"]
                dependency_of = info["dependency_of"]

                # Extract the package part
                match = re.match(r'^(\s*"[^"]+",?\s*)', line)
                if match:
                    package_part = match.group(1).rstrip()

                    # Normalize SWIPAT comment
                    swipat_comment = None
                    if "SWIPAT filed under:" in line:
                        swipat_match = re.search(r"# SWIPAT filed under: (https?://[^\s#]+)", line)
                        if swipat_match:
                            swipat_comment = f"# SWIPAT filed under: {swipat_match.group(1)}"
                    elif "SWIPAT:" in line:
                        swipat_match = re.search(r"# SWIPAT: (https?://[^\s#]+)", line)
                        if swipat_match:
                            swipat_comment = f"# SWIPAT filed under: {swipat_match.group(1)}"

                    if swipat_comment:
                        # Get max length for this section
                        max_package_len = line_to_max_len.get(i, len(package_part))

                        # Pad package part to align SWIPAT comments
                        padding = " " * (max_package_len - len(package_part) + 1)

                        # Build usage comment
                        if extensions:
                            ext_list = ", ".join(sorted(extensions))
                            usage_comment = f"# Used by: {ext_list}"
                        elif dependency_of:
                            dep_list = ", ".join(sorted(dependency_of))
                            usage_comment = f"# Used by: (dependency of {dep_list})"
                        else:
                            usage_comment = "# Used by: (none found)"

                        # Reconstruct line with proper alignment
                        updated_line = f"{package_part}{padding}{swipat_comment} {usage_comment}\n"

        updated_lines.append(updated_line)

    # Write updated content back to file
    with open(toml_file, "w") as f:
        f.writelines(updated_lines)

    print(f"Updated {toml_file}")


def main():
    """Main function."""
    # Get repo root (two levels up from tools/isaac)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    json_file = repo_root / "package_extensions_with_deps.json"
    deps_dir = repo_root / "deps"

    print(f"Loading package information from {json_file}")
    package_info = load_package_info(json_file)

    # Print summary
    direct_usage = sum(1 for info in package_info.values() if info["extensions"])
    transitive = sum(1 for info in package_info.values() if not info["extensions"] and info["dependency_of"])
    unused = sum(1 for info in package_info.values() if not info["extensions"] and not info["dependency_of"])

    print(f"Package summary:")
    print(f"  Directly used: {direct_usage}")
    print(f"  Transitive dependencies: {transitive}")
    print(f"  Potentially unused: {unused}")

    # Find all pip*.toml files in deps directory
    toml_files = sorted(deps_dir.glob("pip*.toml"))

    if not toml_files:
        print(f"\nNo pip*.toml files found in {deps_dir}")
        return

    print(f"\nFound {len(toml_files)} pip*.toml file(s) to update:")
    for toml_file in toml_files:
        print(f"  - {toml_file.name}")

    print()
    for toml_file in toml_files:
        update_pip_toml(toml_file, package_info)

    print("\nDone!")


if __name__ == "__main__":
    main()
