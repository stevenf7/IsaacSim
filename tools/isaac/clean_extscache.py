#!/usr/bin/env python3

import argparse
import os
import re
import sys


def check_dependencies(kit_file, build_dir, deprecated_dir, verbose=False):
    """
    Check that all extensions in the build and deprecated directories are listed as dependencies
    in the kit file's [dependencies] section.

    Args:
        kit_file (str): Path to the kit file
        build_dir (str): Path to the build directory
        deprecated_dir (str): Path to the deprecated directory
        verbose (bool): If True, print detailed debug information

    Returns:
        bool: True if all extensions are listed as dependencies, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    log("Checking for missing dependencies...")

    # Check if directories exist
    built_extensions = []
    if os.path.isdir(build_dir):
        try:
            built_extensions = os.listdir(build_dir)
            log(f"Found {len(built_extensions)} built extensions: {built_extensions}")
        except Exception as e:
            print(f"Error reading build directory: {e}")
            return False

    dir_deprecated_extensions = []
    if os.path.isdir(deprecated_dir):
        try:
            dir_deprecated_extensions = os.listdir(deprecated_dir)
            log(
                f"Found {len(dir_deprecated_extensions)} deprecated extensions in directory: {dir_deprecated_extensions}"
            )
        except Exception as e:
            print(f"Error reading deprecated directory: {e}")
            log(f"Will continue without checking deprecated directory: {e}")

    # Read the kit file
    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    # Find the dependencies section
    dependencies_section = None
    dependencies_section_match = re.search(r"\[dependencies\](.*?)(?=\[|\Z)", content, re.DOTALL)
    if dependencies_section_match:
        dependencies_section = dependencies_section_match.group(1)
        log("Found dependencies section")
    else:
        log("Warning: Could not find dependencies section in the kit file")
        log("Skipping dependency check")
        return True

    # Extract all dependencies using the pattern "extension_name" = { ... } or "extension_name" = {}
    dependencies = []
    dependency_pattern = re.compile(r'["\'](.*?)["\']\s*=\s*\{')
    if dependencies_section:
        for dep_match in dependency_pattern.finditer(dependencies_section):
            dependency = dep_match.group(1)
            dependencies.append(dependency)
        log(f"Found {len(dependencies)} dependencies: {dependencies}")

    # Also handle filter:platform section entries
    platform_dependencies_match = re.search(r'\[dependencies\."filter:platform".*?\](.*?)(?=\[|\Z)', content, re.DOTALL)
    if platform_dependencies_match:
        platform_section = platform_dependencies_match.group(1)
        for dep_match in dependency_pattern.finditer(platform_section):
            dependency = dep_match.group(1)
            dependencies.append(dependency)
            log(f"Found platform-specific dependency: {dependency}")

    # Extract base names of dependencies (without versions)
    dependency_bases = [dep.split("-")[0] for dep in dependencies]
    log(f"Dependency base names: {dependency_bases}")

    # Check that all extensions in build and deprecated directories are listed as dependencies
    missing_dependencies = []

    # Check built extensions
    for ext in built_extensions:
        ext_base = ext.split("-")[0]
        if ext_base not in dependency_bases:
            log(f"Extension {ext} is in build directory but not listed as dependency")
            missing_dependencies.append((ext, "built"))

    # Check deprecated extensions
    for ext in dir_deprecated_extensions:
        ext_base = ext.split("-")[0]
        if ext_base not in dependency_bases:
            log(f"Extension {ext} is in deprecated directory but not listed as dependency")
            missing_dependencies.append((ext, "deprecated"))

    # Report missing dependencies
    if missing_dependencies:
        print("\nERROR: The following extensions are missing from the dependencies section:")
        missing_built = [ext for ext, category in missing_dependencies if category == "built"]
        missing_deprecated = [ext for ext, category in missing_dependencies if category == "deprecated"]

        if missing_built:
            print(f"  {len(missing_built)} built extensions:")
            for ext in missing_built:
                print(f"   - {ext}")

        if missing_deprecated:
            print(f"  {len(missing_deprecated)} deprecated extensions:")
            for ext in missing_deprecated:
                print(f"   - {ext}")

        print("\nPlease add these extensions to the [dependencies] section.")
        return False
    else:
        log("All extensions are correctly listed as dependencies.")
        return True


def check_version_locks(kit_file, verbose=False, dry_run=False):
    """
    Check that any extension with a version lock hash matches the SDK Version hash in the kit file.

    Args:
        kit_file (str): Path to the kit file
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't report errors, just log what would be done

    Returns:
        bool: True if all version locks match the SDK hash, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    log("Checking extension version locks against SDK hash...")

    # Read the kit file
    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    # Extract the Kit SDK Version hash
    # Pattern to extract the hash before .gl from "Kit SDK Version: 107.3.0+master.187175.a64e0341.gl"
    sdk_version_match = re.search(r"Kit SDK Version: ([\d\.]+\+.*?)\.([a-f0-9]+)\.gl", content)
    if not sdk_version_match:
        log("Warning: Could not find Kit SDK Version in the kit file")
        return True

    sdk_version = sdk_version_match.group(1)
    sdk_hash = sdk_version_match.group(2)
    log(f"Found Kit SDK Version: {sdk_version}")
    log(f"Extracted SDK hash: {sdk_hash}")

    # Find all extension entries with version locks
    # Pattern matches: "ext.name" = {version = "ver.num-something+hash", ...}
    ext_version_pattern = re.compile(r'["\']([\w\.\-]+)["\'].*?version\s*=\s*["\'](.*?)\+([\w\d]+)["\']')
    locks_mismatched = []

    for match in ext_version_pattern.finditer(content):
        ext_name = match.group(1)
        version = match.group(2)
        lock_hash = match.group(3)

        log(f"Found extension {ext_name} with version {version}+{lock_hash}")

        if lock_hash != sdk_hash:
            log(f"Extension {ext_name} has lock hash {lock_hash} that doesn't match SDK hash {sdk_hash}")
            locks_mismatched.append((ext_name, version, lock_hash))

    # Report mismatches
    if locks_mismatched and not dry_run:
        print("\nERROR: The following extensions have version locks that don't match the SDK hash:")
        print(f"SDK Version: {sdk_version}.{sdk_hash}.gl (hash: {sdk_hash})")

        for ext_name, version, lock_hash in locks_mismatched:
            print(f"   - Extension: {ext_name}")
            print(f"     Version: {version}+{lock_hash}")
            print(f"     Current hash: {lock_hash}, Expected hash: {sdk_hash}")

        print("\nPlease update these extensions to use the correct SDK hash.")
        return False
    elif locks_mismatched and dry_run:
        log(f"Would report {len(locks_mismatched)} mismatched version locks")
        return True
    else:
        log("All extension version locks match the SDK hash.")
        return True


def clean_extscache(
    kit_file_path=None,
    build_dir_path=None,
    deprecated_dir_path=None,
    apps_dir_path=None,
    create_dir=False,
    verbose=False,
    dry_run=False,
    check_deps=True,
    check_locks=True,
):
    """
    Removes extensions from the enabled section in the kit file if they exist in the build directory,
    the deprecated directory, or the apps directory.

    Args:
        kit_file_path (str): Path to the kit file (default: source/apps/isaacsim.exp.extscache.kit)
        build_dir_path (str): Path to the build directory (default: _build/linux-x86_64/release/exts)
        deprecated_dir_path (str): Path to the deprecated directory (default: _build/linux-x86_64/release/extsDeprecated)
        apps_dir_path (str): Path to the apps directory (default: _build/linux-x86_64/release/apps)
        create_dir (bool): If True, create the build directory if it doesn't exist
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't modify the file, just report what would be done
        check_deps (bool): If True, check that all extensions are listed in dependencies
        check_locks (bool): If True, check that version locks match the SDK hash

    Returns:
        bool: True if successful, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    # Default paths
    default_kit_file = "source/apps/isaacsim.exp.extscache.kit"
    default_build_dir = "_build/linux-x86_64/release/exts"
    default_deprecated_dir = "_build/linux-x86_64/release/extsDeprecated"
    default_apps_dir = "_build/linux-x86_64/release/apps"

    # Use provided paths or defaults
    kit_file = kit_file_path or default_kit_file
    build_dir = build_dir_path or default_build_dir
    deprecated_dir = deprecated_dir_path or default_deprecated_dir
    apps_dir = apps_dir_path or default_apps_dir

    log(f"Using kit file: {os.path.abspath(kit_file)}")
    log(f"Using build directory: {os.path.abspath(build_dir)}")
    log(f"Using deprecated directory: {os.path.abspath(deprecated_dir)}")
    log(f"Using apps directory: {os.path.abspath(apps_dir)}")

    if dry_run:
        print("Running in dry-run mode - no changes will be made to files")

    # Check if kit file exists
    if not os.path.isfile(kit_file):
        print(f"Error: Kit file {kit_file} does not exist!")
        return False

    # Check if build directory exists
    if not os.path.isdir(build_dir):
        if create_dir:
            try:
                os.makedirs(build_dir, exist_ok=True)
                print(f"Created build directory {build_dir}")
            except Exception as e:
                print(f"Error creating build directory: {e}")
                return False
        else:
            print(f"Build directory {build_dir} does not exist!")
            log("Will only check for deprecated extensions and apps")

    # Get list of built extensions
    built_extensions = []
    if os.path.isdir(build_dir):
        try:
            built_extensions = os.listdir(build_dir)
            log(f"Found {len(built_extensions)} built extensions: {built_extensions}")
        except Exception as e:
            print(f"Error reading build directory: {e}")
            return False
    else:
        log("Build directory doesn't exist, will only check for deprecated extensions and apps")

    # Get list of deprecated extensions from directory
    dir_deprecated_extensions = []
    if os.path.isdir(deprecated_dir):
        try:
            dir_deprecated_extensions = os.listdir(deprecated_dir)
            log(
                f"Found {len(dir_deprecated_extensions)} deprecated extensions in directory: {dir_deprecated_extensions}"
            )
        except Exception as e:
            print(f"Error reading deprecated directory: {e}")
            log(f"Will continue without checking deprecated directory: {e}")
    else:
        log("Deprecated directory doesn't exist, will only check for built extensions and apps")

    # Get list of apps from directory
    apps_extensions = []
    if os.path.isdir(apps_dir):
        try:
            all_files = os.listdir(apps_dir)
            # Filter for .kit files only
            apps_extensions = [f for f in all_files if f.endswith(".kit")]
            log(f"Found {len(apps_extensions)} .kit files in apps directory: {apps_extensions}")
        except Exception as e:
            print(f"Error reading apps directory: {e}")
            log(f"Will continue without checking apps directory: {e}")
    else:
        log("Apps directory doesn't exist, will only check for built and deprecated extensions")

    # Read the kit file
    try:
        with open(kit_file, "r") as f:
            content = f.read()

        # Check if file seems to have correct format
        if "[settings.app.exts]" not in content or "enabled = [" not in content:
            log(f"Warning: Kit file {kit_file} doesn't appear to have the expected format")
            if verbose:
                log(f"File content (first 500 chars): {content[:500]}")

        lines = content.splitlines(True)  # Keep line endings
        log(f"Read {len(lines)} lines from kit file")
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    # Find the enabled section
    enabled_start = None
    enabled_end = None
    section_found = False
    bracket_level = 0

    # First, try precise section search
    for i, line in enumerate(lines):
        if "[settings.app.exts]" in line:
            section_found = True
            log(f"Found [settings.app.exts] section at line {i+1}")

        if section_found and "enabled = [" in line:
            enabled_start = i + 1
            bracket_level = 1  # We've opened one bracket
            log(f"Found enabled = [ at line {i+1}, setting start to line {enabled_start+1}")
            break

    # If we found the start, look for the end by matching brackets
    if enabled_start is not None:
        for i in range(enabled_start, len(lines)):
            line = lines[i]
            # Count brackets in this line
            bracket_level += line.count("[") - line.count("]")

            if bracket_level == 0:
                enabled_end = i
                log(f"Found matching closing bracket at line {i+1}")
                break

    # If precise section search failed, try regex as fallback
    if enabled_start is None or enabled_end is None:
        log("Precise section search failed, trying regex fallback")
        # Find the section using regex
        try:
            content = "".join(lines)
            match = re.search(r"\[settings\.app\.exts\].*?enabled\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if match:
                log("Found enabled section using regex")
                # Get the index in the content where the extensions list starts
                start_idx = match.start(1)
                end_idx = match.end(1)

                # Convert to line numbers
                content_before_start = content[:start_idx]
                content_before_end = content[:end_idx]
                enabled_start = content_before_start.count("\n")
                enabled_end = content_before_end.count("\n")

                # Now we have line numbers
                log(f"Regex found enabled section from lines {enabled_start+1} to {enabled_end+1}")
            else:
                log("Regex search also failed")
        except Exception as e:
            log(f"Regex search failed with error: {e}")

    if enabled_start is None or enabled_end is None:
        print("Could not find enabled extensions section!")
        log("enabled_start = " + str(enabled_start))
        log("enabled_end = " + str(enabled_end))
        if verbose:
            print("First 20 lines of file:")
            for i, line in enumerate(lines[:20]):
                print(f"{i+1}: {line.rstrip()}")
        return False

    # Process the enabled extensions list
    log(f"Processing extensions from line {enabled_start+1} to {enabled_end+1}")
    extensions_section = lines[enabled_start:enabled_end]
    log(f"Extensions section has {len(extensions_section)} lines")
    new_extensions_section = []
    removed_count = 0
    removed_exts = []

    # Extract extension names from the build directory (remove version part)
    built_ext_bases = [ext.split("-")[0] for ext in built_extensions]
    log(f"Built extension base names: {built_ext_bases}")

    # Extract extension base names from deprecated directories
    dir_deprecated_ext_bases = [ext.split("-")[0] for ext in dir_deprecated_extensions]
    log(f"Deprecated extension base names from directory: {dir_deprecated_ext_bases}")

    # Extract extension base names from apps directory
    # Remove both the version part and the .kit extension
    apps_ext_bases = []
    for ext in apps_extensions:
        # Remove .kit extension first
        ext_without_kit = ext[:-4] if ext.endswith(".kit") else ext
        # Then get the base name (part before version)
        base_name = ext_without_kit.split("-")[0]
        apps_ext_bases.append(base_name)
    log(f"Apps base names: {apps_ext_bases}")

    # Extension pattern: looks for quoted strings that might be extension names
    extension_pattern = re.compile(r'["\']([^"\']+?(?:-[^"\']+)?)["\']')

    for i, line in enumerate(extensions_section):
        line_num = enabled_start + i + 1
        line_stripped = line.strip()

        if not line_stripped or line_stripped.startswith("#"):
            log(f"Line {line_num}: Keeping comment or empty line: {line_stripped}")
            new_extensions_section.append(line)
            continue

        # Try to extract extension using regex
        match = extension_pattern.search(line_stripped)
        if match:
            ext_with_version = match.group(1)
            log(f"Line {line_num}: Found extension {ext_with_version} using regex")
        else:
            # Fallback to manual extraction if regex fails
            ext_with_version = line_stripped.strip('",').strip("',").rstrip(",")
            log(f"Line {line_num}: Extracted extension {ext_with_version} manually")

        # Get base name without version
        if "-" in ext_with_version:
            ext_base = ext_with_version.split("-")[0]
            log(f"Line {line_num}: Processing extension {ext_with_version} (base: {ext_base})")
        else:
            ext_base = ext_with_version
            log(f"Line {line_num}: Processing extension {ext_with_version} (no version found)")

        # Check if this extension exists in the build directory, deprecated directory, or apps directory
        remove_extension = False
        reason = None

        if ext_base in built_ext_bases:
            matching_built_ext = [ext for ext in built_extensions if ext.split("-")[0] == ext_base][0]
            log(f"Line {line_num}: Matched {ext_with_version} to built extension {matching_built_ext}")
            remove_extension = True
            reason = "built"
        elif ext_base in dir_deprecated_ext_bases:
            matching_dep_ext = [ext for ext in dir_deprecated_extensions if ext.split("-")[0] == ext_base][0]
            log(f"Line {line_num}: Matched {ext_with_version} to deprecated directory extension {matching_dep_ext}")
            remove_extension = True
            reason = "deprecated directory"
        elif ext_base in apps_ext_bases:
            # Find the matching app extension with .kit extension
            matching_app_exts = [
                ext for ext in apps_extensions if ext.endswith(".kit") and ext[:-4].split("-")[0] == ext_base
            ]
            if matching_app_exts:
                matching_app_ext = matching_app_exts[0]
                log(f"Line {line_num}: Matched {ext_with_version} to app kit file {matching_app_ext}")
                remove_extension = True
                reason = "apps directory"

        if remove_extension:
            removed_exts.append((ext_with_version, reason))
            removed_count += 1
        else:
            log(f"Line {line_num}: Keeping extension {ext_with_version}")
            new_extensions_section.append(line)

    if removed_count == 0:
        print("No extensions need to be removed.")
    else:
        # Update the file
        log(f"Updating file with {len(new_extensions_section)} extension entries (removed {removed_count})")
        new_lines = lines[:enabled_start] + new_extensions_section + lines[enabled_end:]

        if dry_run:
            print(f"Dry run: Would remove {removed_count} extensions:")
            for ext, reason in removed_exts:
                print(f"  - {ext} ({reason})")
        else:
            try:
                # Write the updated file
                with open(kit_file, "w") as f:
                    f.writelines(new_lines)
            except Exception as e:
                print(f"Error writing to kit file: {e}")
                return False

            # Summarize removed extensions by category
            built_removed = [ext for ext, reason in removed_exts if reason == "built"]
            dir_deprecated_removed = [ext for ext, reason in removed_exts if reason == "deprecated directory"]
            apps_removed = [ext for ext, reason in removed_exts if reason == "apps directory"]

            print(f"Removed {removed_count} extensions from the enabled list:")
            if built_removed:
                print(f"  {len(built_removed)} built extensions:")
                for ext in built_removed:
                    print(f"   - {ext}")
            if dir_deprecated_removed:
                print(f"  {len(dir_deprecated_removed)} extensions from deprecated directory:")
                for ext in dir_deprecated_removed:
                    print(f"   - {ext}")
            if apps_removed:
                print(f"  {len(apps_removed)} extensions from apps directory:")
                for ext in apps_removed:
                    print(f"   - {ext}")

    # Check dependencies if requested
    if check_deps:
        dependencies_ok = check_dependencies(kit_file, build_dir, deprecated_dir, verbose)
        if not dependencies_ok and not dry_run:
            print("WARNING: Some extensions are missing from the dependencies section.")

    # Check version locks if requested
    if check_locks:
        locks_ok = check_version_locks(kit_file, verbose, dry_run)
        if not locks_ok and not dry_run:
            print("WARNING: Some extensions have version locks that don't match the SDK hash.")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
Clean the extension cache by removing extensions from the enabled section in the kit file if they:
1. Exist in the build directory (_build/linux-x86_64/release/exts)
2. Exist in the deprecated directory (_build/linux-x86_64/release/extsDeprecated)
3. Exist in the apps directory (_build/linux-x86_64/release/apps)

This script also checks that all extensions in the build and deprecated directories
are properly listed in the [dependencies] section.

This script can also verify that extension version locks match the Kit SDK Version hash.

This is useful for development when you want to avoid loading both the built and the prebuilt 
versions of the same extension, and to ensure deprecated extensions aren't loaded.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--create-dir", action="store_true", help="Create the build directory if it does not exist")
    parser.add_argument("--kit-file", help="Path to the kit file (default: source/apps/isaacsim.exp.extscache.kit)")
    parser.add_argument("--build-dir", help="Path to the build directory (default: _build/linux-x86_64/release/exts)")
    parser.add_argument(
        "--deprecated-dir",
        help="Path to the deprecated directory (default: _build/linux-x86_64/release/extsDeprecated)",
    )
    parser.add_argument("--apps-dir", help="Path to the apps directory (default: _build/linux-x86_64/release/apps)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output for debugging")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without actually modifying files"
    )
    parser.add_argument(
        "--no-deps-check", action="store_true", help="Skip checking if extensions are properly listed in dependencies"
    )
    parser.add_argument(
        "--no-locks-check", action="store_true", help="Skip checking if extension version locks match the SDK hash"
    )

    args = parser.parse_args()

    success = clean_extscache(
        kit_file_path=args.kit_file,
        build_dir_path=args.build_dir,
        deprecated_dir_path=args.deprecated_dir,
        apps_dir_path=args.apps_dir,
        create_dir=args.create_dir,
        verbose=args.verbose,
        dry_run=args.dry_run,
        check_deps=not args.no_deps_check,
        check_locks=not args.no_locks_check,
    )

    if not success:
        sys.exit(1)
