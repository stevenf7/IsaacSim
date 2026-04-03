#!/usr/bin/env python3
"""Tool to discover all external Python package dependencies in Isaac Sim release build."""
import csv
import email.parser
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def find_dist_info_dirs(root_path: Path, follow_symlinks: bool = True) -> list[tuple[Path, str]]:
    """Find all .dist-info directories which indicate installed Python packages.

    Returns list of tuples: (directory_path, package_name-version).
    """
    dist_info_dirs = []

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=follow_symlinks):
        for dirname in dirnames:
            if dirname.endswith(".dist-info"):
                full_path = Path(dirpath) / dirname
                dist_info_dirs.append((full_path, dirname.replace(".dist-info", "")))

    return dist_info_dirs


def parse_packages_list_txt(filepath: Path) -> list[str]:
    """Parse a packages_list.txt file to get package names and versions."""
    packages = []
    if filepath.exists():
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    packages.append(line)
    return packages


def parse_package_name_version(package_identifier: str) -> tuple[str, str]:
    """Parse package name and version from identifier string.

    Args:
        package_identifier: String like 'package-1.0.0' or 'package_name-2.3.4'

    Returns:
        Tuple of (name, version)
    """
    # Handle cases like 'package-1.0.0' or 'package_name-2.3.4.dev0'
    # Split at the first dash/underscore followed by a digit and a dot (standard version pattern)
    match = re.match(r"^(.+?)[-_](\d+\..*)$", package_identifier)
    if match:
        return match.group(1), match.group(2)
    return package_identifier, "unknown"


def _identify_license_from_text(text: str) -> str | None:
    """Identify a common license type by pattern-matching raw text."""
    upper = text.upper()
    if "MIT LICENSE" in upper:
        return "MIT License"
    if "APACHE LICENSE" in upper:
        if "2.0" in upper:
            return "Apache License 2.0"
        return "Apache License"
    if "BSD LICENSE" in upper:
        if "3-CLAUSE" in upper:
            return "BSD 3-Clause License"
        if "2-CLAUSE" in upper:
            return "BSD 2-Clause License"
        return "BSD License"
    if "GPL" in upper:
        return "GPL License"
    return None


def extract_license_from_metadata(dist_info_path: Path) -> str:
    """Extract license information from a .dist-info directory.

    Args:
        dist_info_path: Path to the .dist-info directory

    Returns:
        License string or "Unknown"
    """
    metadata_file = dist_info_path / "METADATA"
    if metadata_file.exists():
        try:
            with open(metadata_file, encoding="utf-8", errors="ignore") as f:
                parser = email.parser.Parser()
                metadata = parser.parse(f)

                # Check classifier fields for license info FIRST (most reliable)
                classifiers = metadata.get_all("Classifier", [])
                if classifiers:
                    for classifier in classifiers:
                        if classifier.startswith("License ::"):
                            license_name = classifier.split("::")[-1].strip()
                            return license_name

                license_text = metadata.get("License", "").strip()
                if license_text and license_text not in ["", "UNKNOWN", "Unknown"]:
                    if len(license_text) > 100:
                        first_line = license_text.split("\n")[0].strip()
                        if len(first_line) < 100 and first_line:
                            return first_line
                        identified = _identify_license_from_text(license_text[:500])
                        if identified:
                            return identified
                        return "See METADATA License field"
                    return license_text
        except Exception:
            pass

    license_files = list(dist_info_path.glob("LICENSE*")) + list(dist_info_path.glob("COPYING*"))
    if license_files:
        try:
            with open(license_files[0], encoding="utf-8", errors="ignore") as f:
                content = f.read(500)
                identified = _identify_license_from_text(content)
                if identified:
                    return identified
                return "See LICENSE file"
        except Exception:
            return "See LICENSE file"

    return "Unknown"


def get_package_details(dist_info_path: Path, package_identifier: str, release_root: Path) -> dict[str, str]:
    """Extract detailed package information including name, version, license, and location.

    Args:
        dist_info_path: Path to the .dist-info directory
        package_identifier: String identifier like 'package-1.0.0'
        release_root: Root path of the release directory

    Returns:
        Dictionary with package details
    """
    name, version = parse_package_name_version(package_identifier)
    license_info = extract_license_from_metadata(dist_info_path)

    # Get relative path for location
    try:
        relative_path = str(dist_info_path.parent.relative_to(release_root))
    except ValueError:
        relative_path = str(dist_info_path.parent)

    location_type = get_parent_directory_type(dist_info_path.parent, release_root)

    return {
        "name": name,
        "version": version,
        "license": license_info,
        "location": relative_path,
        "location_type": location_type,
    }


def get_parent_directory_type(package_path: Path, release_root: Path) -> str:
    """Determine what type of directory contains this package.

    Returns: 'pip_prebundle', 'site-packages', 'other', etc.
    """
    try:
        relative_path = package_path.relative_to(release_root)
        parts = relative_path.parts

        # Check if in pip_prebundle
        if "pip_prebundle" in parts:
            idx = parts.index("pip_prebundle")
            return f"pip_prebundle ({'/'.join(parts[:idx])})"

        # Check if in site-packages
        if "site-packages" in parts:
            idx = parts.index("site-packages")
            return f"site-packages ({'/'.join(parts[:idx])})"

        # Check if in python_packages
        if "python_packages" in parts:
            return f"python_packages ({'/'.join(parts[:1])})"

        # Return path up to 3 levels
        return f"other ({'/'.join(parts[:min(3, len(parts))])})"
    except ValueError:
        return "unknown"


def clean_location_path(location: str) -> str:
    """Clean the location path by removing version information from extension names.

    Removes version strings like '-0.18.1+109.0.0.lx64.cp312' from extension
    directory names in all locations.

    Args:
        location: The relative path containing the package

    Returns:
        Cleaned location path
    """
    # Split path into parts
    parts = location.split("/")
    cleaned_parts = []

    for part in parts:
        # Match patterns like: name-version where version starts with a digit
        # Examples:
        #   omni.services.pip_archive-0.18.1+109.0.0.lx64.cp312
        #   omni.kit.pip_archive-0.0.0+0e9be1d1.lx64.cp312
        #   omni.kit.debug.python-1.0.1+0e9be1d1.lx64.r.cp312
        # Match: (name)-(version starting with digit followed by anything)
        match = re.match(r"^([a-zA-Z_][\w.]*)-(\d+.*)$", part)
        if match:
            # Keep only the name part, remove version
            cleaned_parts.append(match.group(1))
        else:
            cleaned_parts.append(part)

    return "/".join(cleaned_parts)


def is_symlink_in_path(path: Path) -> bool:
    """Check if any component in the path is a symlink."""
    current = path
    while current != current.parent:
        if current.is_symlink():
            return True
        current = current.parent
    return False


def analyze_python_packages(release_dir: str) -> dict:
    """Analyze all Python packages in the release directory.

    Returns a dictionary with analysis results.

    Raises:
        FileNotFoundError: If the release directory does not exist.
    """
    release_path = Path(release_dir).resolve()

    if not release_path.exists():
        raise FileNotFoundError(f"Release directory not found: {release_path}")

    print(f"Scanning for Python packages in: {release_path}")
    print("This may take a minute...\n")

    # Single walk to collect both .dist-info dirs and packages_list.txt files
    dist_info_dirs: list[tuple[Path, str]] = []
    packages_list_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(release_path, followlinks=True):
        for dirname in dirnames:
            if dirname.endswith(".dist-info"):
                full_path = Path(dirpath) / dirname
                dist_info_dirs.append((full_path, dirname.replace(".dist-info", "")))
        if "packages_list.txt" in filenames:
            packages_list_files.append(Path(dirpath) / "packages_list.txt")

    packages_by_location: dict[str, list] = defaultdict(list)
    packages_in_pip_prebundle = []
    packages_not_in_pip_prebundle = []
    symlinked_packages = []

    for dist_info_path, package_name in dist_info_dirs:
        location_type = get_parent_directory_type(dist_info_path.parent, release_path)
        has_symlink = is_symlink_in_path(dist_info_path)

        packages_by_location[location_type].append(
            {
                "name": package_name,
                "path": str(dist_info_path.parent.relative_to(release_path)),
                "is_symlink": has_symlink,
            }
        )

        if "pip_prebundle" in location_type:
            packages_in_pip_prebundle.append(package_name)
        else:
            packages_not_in_pip_prebundle.append(
                {
                    "name": package_name,
                    "location": location_type,
                    "path": str(dist_info_path.parent.relative_to(release_path)),
                }
            )

        if has_symlink:
            symlinked_packages.append({"name": package_name, "path": str(dist_info_path.relative_to(release_path))})

    return {
        "total_packages": len(dist_info_dirs),
        "packages_by_location": dict(packages_by_location),
        "packages_in_pip_prebundle": packages_in_pip_prebundle,
        "packages_not_in_pip_prebundle": packages_not_in_pip_prebundle,
        "symlinked_packages": symlinked_packages,
        "packages_list_files": packages_list_files,
        "release_path": release_path,
    }


def print_report(analysis: dict) -> None:
    """Print a comprehensive report of the analysis."""
    print("=" * 80)
    print("PYTHON PACKAGE DEPENDENCY ANALYSIS")
    print("=" * 80)
    print(f"Release Directory: {analysis['release_path']}\n")

    print(f"Total Python Packages Found: {analysis['total_packages']}\n")

    print("-" * 80)
    print("PACKAGES BY LOCATION TYPE")
    print("-" * 80)
    for location_type in sorted(analysis["packages_by_location"].keys()):
        packages = analysis["packages_by_location"][location_type]
        print(f"\n{location_type}: {len(packages)} packages")

        # Show first 10 packages as examples
        for pkg in sorted(packages, key=lambda x: x["name"])[:10]:
            symlink_marker = " [SYMLINK]" if pkg["is_symlink"] else ""
            print(f"  - {pkg['name']}{symlink_marker}")

        if len(packages) > 10:
            print(f"  ... and {len(packages) - 10} more")

    print("\n" + "-" * 80)
    print("PACKAGES NOT IN pip_prebundle DIRECTORIES")
    print("-" * 80)
    if analysis["packages_not_in_pip_prebundle"]:
        print(f"Found {len(analysis['packages_not_in_pip_prebundle'])} packages outside pip_prebundle:\n")
        for pkg in sorted(analysis["packages_not_in_pip_prebundle"], key=lambda x: x["name"]):
            print(f"  - {pkg['name']}")
            print(f"    Location: {pkg['location']}")
            print(f"    Path: {pkg['path']}\n")
    else:
        print("✓ All packages are in pip_prebundle directories!\n")

    print("-" * 80)
    print("PACKAGES ACCESSED VIA SYMLINKS")
    print("-" * 80)
    if analysis["symlinked_packages"]:
        print(f"Found {len(analysis['symlinked_packages'])} packages with symlinks in path:\n")
        for pkg in sorted(analysis["symlinked_packages"], key=lambda x: x["name"])[:20]:
            print(f"  - {pkg['name']}")
            print(f"    Path: {pkg['path']}\n")
        if len(analysis["symlinked_packages"]) > 20:
            print(f"  ... and {len(analysis['symlinked_packages']) - 20} more")
    else:
        print("No packages accessed via symlinks.\n")

    print("-" * 80)
    print("PACKAGES_LIST.TXT FILES FOUND")
    print("-" * 80)
    if analysis["packages_list_files"]:
        print(f"Found {len(analysis['packages_list_files'])} packages_list.txt files:\n")
        for plist_file in analysis["packages_list_files"]:
            try:
                rel_path = plist_file.relative_to(analysis["release_path"])
                packages = parse_packages_list_txt(plist_file)
                print(f"\n{rel_path} ({len(packages)} packages):")
                for pkg in packages[:5]:
                    print(f"  - {pkg}")
                if len(packages) > 5:
                    print(f"  ... and {len(packages) - 5} more")
            except ValueError:
                print(f"\n{plist_file} ({len(parse_packages_list_txt(plist_file))} packages)")
    else:
        print("No packages_list.txt files found.\n")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    pip_prebundle_count = len(analysis["packages_in_pip_prebundle"])
    other_count = len(analysis["packages_not_in_pip_prebundle"])
    print(f"Packages in pip_prebundle: {pip_prebundle_count}")
    print(f"Packages in other locations: {other_count}")
    print(f"Packages with symlinks: {len(analysis['symlinked_packages'])}")

    if other_count == 0:
        print("\n✓ VALIDATION PASSED: All external Python packages are in pip_prebundle directories!")
    else:
        print(f"\n⚠ VALIDATION WARNING: {other_count} packages found outside pip_prebundle directories.")
    print("=" * 80)


def export_to_file(analysis: dict, output_file: str) -> None:
    """Export detailed package list to a file."""
    with open(output_file, "w") as f:
        f.write("# External Python Package Dependencies\n")
        f.write(f"# Generated from: {analysis['release_path']}\n\n")

        for location_type in sorted(analysis["packages_by_location"].keys()):
            packages = analysis["packages_by_location"][location_type]
            f.write(f"\n## {location_type} ({len(packages)} packages)\n\n")
            for pkg in sorted(packages, key=lambda x: x["name"]):
                symlink_marker = " [SYMLINK]" if pkg["is_symlink"] else ""
                f.write(f"- {pkg['name']}{symlink_marker}\n")
                f.write(f"  Path: {pkg['path']}\n")

    print(f"\nDetailed package list exported to: {output_file}")


def export_to_csv(release_dir: str, output_file: str) -> None:
    """Export consolidated package list to CSV with name, version, license, and location.

    Args:
        release_dir: Path to the release directory
        output_file: Output CSV file path

    Raises:
        FileNotFoundError: If the release directory does not exist.
    """
    release_path = Path(release_dir).resolve()

    if not release_path.exists():
        raise FileNotFoundError(f"Release directory not found: {release_path}")

    print(f"Scanning for Python packages in: {release_path}")
    print("Extracting package details (this may take a minute)...\n")

    # Find all .dist-info directories
    dist_info_dirs = find_dist_info_dirs(release_path, follow_symlinks=True)

    # Collect unique packages (by name-version)
    # Some packages may appear multiple times due to symlinks
    packages_map: dict[str, dict[str, str]] = {}

    for dist_info_path, package_identifier in dist_info_dirs:
        details = get_package_details(dist_info_path, package_identifier, release_path)

        # Clean location path to remove version info from extensions
        details["location"] = clean_location_path(details["location"])

        # Use name-version as key to deduplicate
        key = f"{details['name']}-{details['version']}"

        # If we've seen this package before, keep the one with shorter/simpler path
        if key in packages_map:
            existing_path = packages_map[key]["location"]
            new_path = details["location"]
            # Prefer shorter paths (typically the non-cache versions)
            if len(new_path) < len(existing_path):
                packages_map[key] = details
        else:
            packages_map[key] = details

    # Sort by package name
    sorted_packages = sorted(packages_map.values(), key=lambda x: (x["name"].lower(), x["version"]))

    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["name", "version", "license", "location"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")

        writer.writeheader()
        for pkg in sorted_packages:
            writer.writerow(pkg)

    print(f"✓ Exported {len(sorted_packages)} unique packages to: {output_file}")
    print(f"  Total package instances found: {len(dist_info_dirs)}")
    print(f"  Unique packages (deduplicated): {len(sorted_packages)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover external Python package dependencies in Isaac Sim release build"
    )
    parser.add_argument(
        "release_dir",
        nargs="?",
        default="_build/linux-x86_64/release",
        help="Path to release directory (default: _build/linux-x86_64/release)",
    )
    parser.add_argument("-o", "--output", metavar="FILE", help="Export detailed package list to markdown file")
    parser.add_argument(
        "--csv", metavar="FILE", help="Export consolidated package list (name, version, license, location) to CSV file"
    )

    args = parser.parse_args()

    try:
        if args.csv:
            export_to_csv(args.release_dir, args.csv)
        else:
            analysis = analyze_python_packages(args.release_dir)
            print_report(analysis)
            if args.output:
                export_to_file(analysis, args.output)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
