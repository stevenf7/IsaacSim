#!/usr/bin/env python3
import argparse
import re
import sys
from collections import defaultdict


def extract_generated_section(file_path):
    """Extract the 'BEGIN GENERATED PART' section from a .kit file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Find content between BEGIN GENERATED PART and END GENERATED PART
        pattern = r"# BEGIN GENERATED PART.*?# END GENERATED PART"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print(f"Warning: Could not find 'BEGIN GENERATED PART' section in {file_path}")
            return content, ""  # Return content but empty section instead of None

        return content, match.group(0)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None, None


def extract_extension_info(file_path):
    """Extract extension information from a file, including version locks."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract all extension declarations
        ext_versions = {}
        version_locks = {}
        empty_version_extensions = set()  # Track extensions with empty version specifications

        # Match pattern for version locks: "extension-name" = {version = "=version"}
        version_lock_pattern = r'"([^"]+)"\s*=\s*\{\s*version\s*=\s*"=?([^"]+)"(?:,\s*exact\s*=\s*true)?\s*\}'
        for match in re.finditer(version_lock_pattern, content):
            ext_name = match.group(1)
            version = match.group(2)
            ext_versions[ext_name] = version
            version_locks[ext_name] = version

        # Match pattern for extensions with empty version specs: "extension-name" = {}
        empty_version_pattern = r'"([^"]+)"\s*=\s*\{\s*\}'
        for match in re.finditer(empty_version_pattern, content):
            ext_name = match.group(1)
            if ext_name not in ext_versions:  # Don't overwrite version locks
                empty_version_extensions.add(ext_name)
                ext_versions[ext_name] = None  # Mark as present but with no version

        return ext_versions, version_locks, empty_version_extensions, content
    except Exception as e:
        print(f"Error reading extension info from {file_path}: {e}")
        return {}, {}, set(), ""


def parse_enabled_extensions(section):
    """Parse enabled extensions and their versions from the generated section."""
    if not section:
        return {}, {}

    extensions = {}
    exact_deps = {}

    # Extract extensions from enabled = [...] section
    enabled_pattern = r"enabled\s*=\s*\[(.*?)\]"
    enabled_match = re.search(enabled_pattern, section, re.DOTALL)

    if enabled_match:
        ext_lines = enabled_match.group(1).strip().split("\n")
        for line in ext_lines:
            line = line.strip().strip(",").strip("\"'")
            if line:
                # Parse extension name and version (format: "ext-name-version")
                parts = line.rsplit("-", 1)
                if len(parts) == 2:
                    name, version = parts
                    extensions[name] = version
                else:
                    extensions[line] = "unknown"

    # Extract exact version dependencies
    exact_deps_pattern = r"# Exact Version dependencies:(.*?)(?=#|$)"
    exact_deps_match = re.search(exact_deps_pattern, section, re.DOTALL)

    if exact_deps_match:
        deps_lines = exact_deps_match.group(1).strip().split("\n")
        for line in deps_lines:
            line = line.strip().strip("#").strip()
            if line:
                parts = line.split("-", 1)
                if len(parts) == 2:
                    name, version = parts
                    name = name.strip()
                    version = version.strip()
                    extensions[name] = version
                    exact_deps[name] = version

    return extensions, exact_deps


def compare_missing_dependencies(file1_path, file2_path):
    """Compare two kit files and show which dependencies in file1 don't exist in file2."""
    # Extract all extension information from both files
    file1_extensions, _, file1_empty_versions, _ = extract_extension_info(file1_path)
    file2_extensions, _, file2_empty_versions, _ = extract_extension_info(file2_path)

    # Combine declared extensions with empty version specs
    for ext in file1_empty_versions:
        if ext not in file1_extensions:
            file1_extensions[ext] = None

    for ext in file2_empty_versions:
        if ext not in file2_extensions:
            file2_extensions[ext] = None

    # Find dependencies in file1 that aren't in file2
    missing_deps = set(file1_extensions.keys()) - set(file2_extensions.keys())

    print(f"\n=== Dependencies in {file1_path} missing from {file2_path} ===")

    if missing_deps:
        print(f"\nFound {len(missing_deps)} missing dependencies:")
        for ext in sorted(missing_deps):
            version = file1_extensions[ext]
            if version:
                print(f"  - {ext} (version: {version})")
            else:
                print(f"  - {ext}")
    else:
        print("\nNo missing dependencies found. All dependencies in the first file exist in the second file.")

    return missing_deps


def compare_extensions(
    file1_exts,
    file2_exts,
    file1_exact_deps,
    file2_exact_deps,
    file1_name,
    file2_name,
    second_file_extensions,
    file1_version_locks,
    file2_version_locks,
    file1_empty_versions,
):
    """Compare two dictionaries of extensions and report differences."""
    file1_only = set(file1_exts.keys()) - set(file2_exts.keys())
    file2_only = set(file2_exts.keys()) - set(file1_exts.keys())

    different_versions = {}
    version_lock_changes = {}

    # Compare versions for extensions that exist in both files
    for ext in set(file1_exts.keys()) & set(file2_exts.keys()):
        if file1_exts[ext] != file2_exts[ext]:
            different_versions[ext] = (file1_exts[ext], file2_exts[ext])

    # Check for extensions in the first file that also exist in second_file_extensions
    # but might not be in file2_exts (from the generated part)
    for ext in file1_exts:
        if ext in second_file_extensions and ext not in file2_exts:
            different_versions[ext] = (file1_exts[ext], second_file_extensions[ext])
        elif ext in second_file_extensions and file1_exts[ext] != second_file_extensions[ext]:
            # If the extension exists in both but with different versions
            if ext not in different_versions:  # Avoid duplicates
                different_versions[ext] = (file1_exts[ext], second_file_extensions[ext])

    # Compare exact deps section specifically
    exact_deps_different = {}
    exact_deps1_only = set(file1_exact_deps.keys()) - set(file2_exact_deps.keys())
    exact_deps2_only = set(file2_exact_deps.keys()) - set(file1_exact_deps.keys())

    for ext in set(file1_exact_deps.keys()) & set(file2_exact_deps.keys()):
        if file1_exact_deps[ext] != file2_exact_deps[ext]:
            exact_deps_different[ext] = (file1_exact_deps[ext], file2_exact_deps[ext])
            # Also add to the main different_versions dict if not already there
            if ext not in different_versions:
                different_versions[ext] = (file1_exact_deps[ext], file2_exact_deps[ext])

    # Also check exact deps against second_file_extensions
    for ext in file1_exact_deps:
        if ext in second_file_extensions and ext not in file2_exact_deps:
            if ext not in different_versions:  # Avoid duplicates
                different_versions[ext] = (file1_exact_deps[ext], second_file_extensions[ext])
        elif ext in second_file_extensions and file1_exact_deps[ext] != second_file_extensions[ext]:
            if ext not in different_versions:  # Avoid duplicates
                different_versions[ext] = (file1_exact_deps[ext], second_file_extensions[ext])

    # Compare version locks between files
    for ext in file2_version_locks:
        # If extension exists in first file but with different version lock
        if ext in file1_version_locks and file1_version_locks[ext] != file2_version_locks[ext]:
            # Different version lock
            version_lock_changes[ext] = (file1_version_locks[ext], file2_version_locks[ext])
        # If extension has no version lock in first file but has empty version spec
        elif ext in file1_empty_versions:
            # Need to add version lock to empty version extension
            version_lock_changes[ext] = (None, file2_version_locks[ext])

    print("\n=== Comparison Results ===")

    if file1_only:
        print(f"\nExtensions only in {file1_name}:")
        for ext in sorted(file1_only):
            print(f"  - {ext} (version: {file1_exts[ext]})")

    if file2_only:
        print(f"\nExtensions only in {file2_name}:")
        for ext in sorted(file2_only):
            print(f"  - {ext} (version: {file2_exts[ext]})")

    if different_versions:
        print("\nExtensions with different versions:")
        for ext, (ver1, ver2) in sorted(different_versions.items()):
            print(f"  - {ext}:")
            print(f"      {file1_name}: {ver1}")
            print(f"      {file2_name}: {ver2}")

    # Print version lock differences
    if version_lock_changes:
        print("\n=== Version Lock Changes ===")
        for ext, (ver1, ver2) in sorted(version_lock_changes.items()):
            if ver1 is None:
                print(f"  - {ext}: Add version lock {ver2}")
            else:
                print(f"  - {ext}: Change version lock from {ver1} to {ver2}")

    # Print specific information about exact dependencies section
    if exact_deps1_only or exact_deps2_only or exact_deps_different:
        print("\n=== Exact Dependencies Section Comparison ===")

        if exact_deps1_only:
            print(f"\nExact dependencies only in {file1_name}:")
            for ext in sorted(exact_deps1_only):
                print(f"  - {ext} (version: {file1_exact_deps[ext]})")

        if exact_deps2_only:
            print(f"\nExact dependencies only in {file2_name}:")
            for ext in sorted(exact_deps2_only):
                print(f"  - {ext} (version: {file2_exact_deps[ext]})")

        if exact_deps_different:
            print("\nExact dependencies with different versions:")
            for ext, (ver1, ver2) in sorted(exact_deps_different.items()):
                print(f"  - {ext}:")
                print(f"      {file1_name}: {ver1}")
                print(f"      {file2_name}: {ver2}")

    if not (file1_only or file2_only or different_versions or version_lock_changes):
        print("\nNo differences found in extensions or their versions.")

    return different_versions, version_lock_changes


def update_file_versions(file_path, full_content, different_versions, version_lock_changes):
    """Update the first file's extension versions to match the second file's versions."""
    if not different_versions and not version_lock_changes:
        print("\nNo version differences to update.")
        return

    updated_content = full_content

    # Update the enabled extensions section
    enabled_pattern = r"enabled\s*=\s*\[(.*?)\]"
    enabled_match = re.search(enabled_pattern, updated_content, re.DOTALL)

    if enabled_match:
        enabled_section = enabled_match.group(1)
        updated_enabled_section = enabled_section

        for ext, (old_ver, new_ver) in different_versions.items():
            # Replace the version in the enabled section
            # This pattern looks for the extension name followed by a version
            pattern = r"(" + ext + r")-" + re.escape(old_ver)
            updated_enabled_section = re.sub(pattern, f"\\1-{new_ver}", updated_enabled_section)

        # Replace the old enabled section with the updated one
        updated_content = updated_content.replace(
            f"enabled = [{enabled_section}]", f"enabled = [{updated_enabled_section}]"
        )

    # Update the Exact Version dependencies section
    exact_deps_pattern = r"(# Exact Version dependencies:)(.*?)(?=#|$)"
    exact_deps_match = re.search(exact_deps_pattern, updated_content, re.DOTALL)

    if exact_deps_match:
        exact_deps_header = exact_deps_match.group(1)
        exact_deps_section = exact_deps_match.group(2)
        updated_exact_deps_section = exact_deps_section

        for ext, (old_ver, new_ver) in different_versions.items():
            # Replace the version in the exact dependencies section
            pattern = r"(#\s*" + ext + r")-" + re.escape(old_ver)
            updated_exact_deps_section = re.sub(pattern, f"\\1-{new_ver}", updated_exact_deps_section)

        # Replace the old exact deps section with the updated one
        updated_content = updated_content.replace(
            f"{exact_deps_header}{exact_deps_section}", f"{exact_deps_header}{updated_exact_deps_section}"
        )

    # Update the dependencies section at the top of the file
    deps_pattern = r'"([^"]+)"\s*=\s*\{version\s*=\s*"([^"]+)"'
    for match in re.finditer(deps_pattern, updated_content):
        ext_name = match.group(1)
        old_version = match.group(2)

        # Check if this extension is in our list of extensions to update
        for ext, (old_ver, new_ver) in different_versions.items():
            if ext_name == ext and old_version == old_ver:
                # Replace the version in the dependencies section
                updated_content = updated_content.replace(
                    f'"{ext_name}" = {{version = "{old_version}"', f'"{ext_name}" = {{version = "{new_ver}"'
                )

    # Update version locks or add new ones
    for ext, (old_ver, new_ver) in version_lock_changes.items():
        if old_ver is None:
            # The extension has no version lock in the first file, so we need to add one
            pattern = r'"' + ext + r'"\s*=\s*\{\s*\}'
            replacement = f'"{ext}" = {{version = "{new_ver}", exact = true}}'
            updated_content = re.sub(pattern, replacement, updated_content)
        else:
            # Update existing version lock
            pattern = r'"' + ext + r'"\s*=\s*\{version\s*=\s*"' + re.escape(old_ver) + r'"'
            replacement = f'"{ext}" = {{version = "{new_ver}"'
            updated_content = re.sub(pattern, replacement, updated_content)

    # Write the updated content back to the file
    try:
        with open(file_path, "w") as f:
            f.write(updated_content)
        print(f"\nSuccessfully updated versions in {file_path}")

        # Print which extensions were updated
        if different_versions:
            print("\nThe following extension versions were updated:")
            for ext, (old_ver, new_ver) in sorted(different_versions.items()):
                print(f"  - {ext}: {old_ver} → {new_ver}")

        if version_lock_changes:
            print("\nThe following version locks were updated:")
            for ext, (old_ver, new_ver) in sorted(version_lock_changes.items()):
                if old_ver is None:
                    print(f"  - {ext}: Added version lock {new_ver}")
                else:
                    print(f"  - {ext}: {old_ver} → {new_ver}")

    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Compare or check missing dependencies between two .kit files")
    parser.add_argument("file1", help="First .kit file")
    parser.add_argument("file2", help="Second .kit file")
    parser.add_argument(
        "--missing-deps",
        action="store_true",
        help="Check which dependencies in the first file are missing from the second file",
    )
    parser.add_argument(
        "--update", action="store_true", help="Update the first file to match versions from the second file"
    )

    args = parser.parse_args()

    file1_path = args.file1
    file2_path = args.file2

    if args.missing_deps:
        # Run in missing dependencies mode
        print(f"Checking for dependencies in '{file1_path}' that are missing from '{file2_path}'...")
        compare_missing_dependencies(file1_path, file2_path)
    else:
        # Run in regular comparison mode
        print(f"Comparing '{file1_path}' and '{file2_path}'...")

        # Extract extension information from both files
        file1_extensions, file1_version_locks, file1_empty_versions, file1_content_full = extract_extension_info(
            file1_path
        )
        file2_extensions, file2_version_locks, _, _ = extract_extension_info(file2_path)

        # Extract the generated sections
        file1_content, file1_section = extract_generated_section(file1_path)
        file2_content, file2_section = extract_generated_section(file2_path)

        # Skip section comparison if either section is empty or missing
        if not file1_section or not file2_section:
            print(
                "\nSkipping generated section comparison as one or both files lack the 'BEGIN GENERATED PART' section."
            )

            # If we're still able to extract extension info, compare those
            if file1_extensions and file2_extensions:
                print("\nComparing extension declarations from both files...")
                missing_deps = set(file1_extensions.keys()) - set(file2_extensions.keys())
                extra_deps = set(file2_extensions.keys()) - set(file1_extensions.keys())

                if missing_deps:
                    print(f"\nExtensions in {file1_path} missing from {file2_path}:")
                    for ext in sorted(missing_deps):
                        version = file1_extensions[ext]
                        if version:
                            print(f"  - {ext} (version: {version})")
                        else:
                            print(f"  - {ext}")

                if extra_deps:
                    print(f"\nExtensions in {file2_path} not found in {file1_path}:")
                    for ext in sorted(extra_deps):
                        version = file2_extensions[ext]
                        if version:
                            print(f"  - {ext} (version: {version})")
                        else:
                            print(f"  - {ext}")

                different_versions = {}
                for ext in set(file1_extensions.keys()) & set(file2_extensions.keys()):
                    if file1_extensions[ext] != file2_extensions[ext]:
                        different_versions[ext] = (file1_extensions[ext], file2_extensions[ext])

                if different_versions:
                    print("\nExtensions with different versions:")
                    for ext, (ver1, ver2) in sorted(different_versions.items()):
                        print(f"  - {ext}:")
                        print(f"      {file1_path}: {ver1}")
                        print(f"      {file2_path}: {ver2}")
            else:
                print("Unable to extract extension information from both files for comparison.")
        else:
            # Proceed with full comparison if both sections are available
            # Parse the extensions and their versions from the generated section
            file1_exts, file1_exact_deps = parse_enabled_extensions(file1_section)
            file2_exts, file2_exact_deps = parse_enabled_extensions(file2_section)

            # Compare the extensions
            different_versions, version_lock_changes = compare_extensions(
                file1_exts,
                file2_exts,
                file1_exact_deps,
                file2_exact_deps,
                file1_path,
                file2_path,
                file2_extensions,
                file1_version_locks,
                file2_version_locks,
                file1_empty_versions,
            )

            # Only update the file if --update flag is provided
            if (different_versions or version_lock_changes) and args.update:
                print("\nUpdating the first file to match versions from the second file...")
                update_file_versions(file1_path, file1_content_full, different_versions, version_lock_changes)
            elif different_versions or version_lock_changes:
                print("\nChanges that would be applied if --update was specified:")

                if different_versions:
                    print("\nExtension versions that would be updated:")
                    for ext, (old_ver, new_ver) in sorted(different_versions.items()):
                        print(f"  - {ext}: {old_ver} → {new_ver}")

                if version_lock_changes:
                    print("\nVersion locks that would be updated:")
                    for ext, (old_ver, new_ver) in sorted(version_lock_changes.items()):
                        if old_ver is None:
                            print(f"  - {ext}: Would add version lock {new_ver}")
                        else:
                            print(f"  - {ext}: Would change version lock from {old_ver} to {new_ver}")

                print("\nRun with --update to apply these changes.")


if __name__ == "__main__":
    main()
