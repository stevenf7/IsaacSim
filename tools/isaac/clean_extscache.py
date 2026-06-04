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

import argparse
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


def check_dependencies(kit_file, build_dir, deprecated_dir, internal_dir=None, verbose=False):
    """
    Check that all extensions in the build, deprecated, and internal directories are listed as
    dependencies in the kit file's [dependencies] section.

    Args:
        kit_file (str): Path to the kit file
        build_dir (str): Path to the build directory
        deprecated_dir (str): Path to the deprecated directory
        internal_dir (str): Optional path to the extsInternal directory. Extensions here are
            validated in [dependencies] but are NOT removed from enabled lists (they must
            remain version-locked so ``repo_deploy_exts`` publishes them and they are
            downloaded from the registry at runtime).
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

    dir_internal_extensions = []
    if internal_dir and os.path.isdir(internal_dir):
        try:
            dir_internal_extensions = os.listdir(internal_dir)
            log(f"Found {len(dir_internal_extensions)} internal extensions in directory: {dir_internal_extensions}")
        except Exception as e:
            print(f"Error reading internal directory: {e}")
            log(f"Will continue without checking internal directory: {e}")

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

    # Check internal extensions. These must be declared in [dependencies] so that
    # ``repo_deploy_exts`` picks them up; otherwise they will silently not be published.
    for ext in dir_internal_extensions:
        ext_base = ext.split("-")[0]
        if ext_base not in dependency_bases:
            log(f"Extension {ext} is in internal directory but not listed as dependency")
            missing_dependencies.append((ext, "internal"))

    if missing_dependencies:
        print("Missing from [dependencies] section:")
        for ext, source in missing_dependencies:
            print(f"  - {ext} (found in {source} directory)")
        return False
    else:
        log("All extensions are correctly listed as dependencies.")
        return True


def check_version_locks(kit_file, verbose=False, dry_run=False, update_locks=False):
    """
    Check that any extension with a version lock hash matches the SDK Version hash in the kit file.
    Optionally update mismatched hashes to match the SDK hash.

    Args:
        kit_file (str): Path to the kit file
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't report errors, just log what would be done
        update_locks (bool): If True, update any mismatched hashes to match the SDK hash

    Returns:
        bool: True if all version locks match the SDK hash (or were updated), False otherwise
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

    # If we need to update locks, keep the original content to modify
    updated_content = content

    for match in ext_version_pattern.finditer(content):
        ext_name = match.group(1)
        version = match.group(2)
        lock_hash = match.group(3)

        log(f"Found extension {ext_name} with version {version}+{lock_hash}")

        if lock_hash != sdk_hash:
            log(f"Extension {ext_name} has lock hash {lock_hash} that doesn't match SDK hash {sdk_hash}")
            locks_mismatched.append((ext_name, version, lock_hash))

            # If update_locks is True, update the hash in the content
            if update_locks and not dry_run:
                # Create the replacement pattern with the new hash
                old_version = f"{version}+{lock_hash}"
                new_version = f"{version}+{sdk_hash}"
                log(f"Updating {ext_name} from {old_version} to {new_version}")

                # Replace all occurrences of this specific version string
                updated_content = updated_content.replace(f'"{old_version}"', f'"{new_version}"')
                updated_content = updated_content.replace(f"'{old_version}'", f"'{new_version}'")

    # Write updated content back to file if changes were made
    if update_locks and locks_mismatched and not dry_run:
        try:
            with open(kit_file, "w") as f:
                f.write(updated_content)
            print(f"Updated {len(locks_mismatched)} extension version locks to match SDK hash {sdk_hash}:")
            for ext_name, version, lock_hash in locks_mismatched:
                print(f"   - {ext_name}: {version}+{lock_hash} → {version}+{sdk_hash}")
            return True
        except Exception as e:
            print(f"Error writing updated kit file: {e}")
            return False

    # Report mismatches if not updating or in dry_run mode
    if locks_mismatched and not dry_run and not update_locks:
        print("\nERROR: The following extensions have version locks that don't match the SDK hash:")
        print(f"SDK Version: {sdk_version}.{sdk_hash}.gl (hash: {sdk_hash})")

        for ext_name, version, lock_hash in locks_mismatched:
            print(f"   - Extension: {ext_name}")
            print(f"     Version: {version}+{lock_hash}")
            print(f"     Current hash: {lock_hash}, Expected hash: {sdk_hash}")

        print("\nPlease update these extensions to use the correct SDK hash.")
        return False
    elif locks_mismatched and dry_run:
        if update_locks:
            print(f"Would update {len(locks_mismatched)} extension version locks to match SDK hash {sdk_hash}:")
            for ext_name, version, lock_hash in locks_mismatched:
                print(f"   - {ext_name}: {version}+{lock_hash} → {version}+{sdk_hash}")
        else:
            log(f"Would report {len(locks_mismatched)} mismatched version locks")
        return True
    else:
        log("All extension version locks match the SDK hash.")
        return True


def update_physics_versions(kit_file, packman_xml_file, verbose=False, dry_run=False):
    """
    Extract the physics version from the packman XML file and update all physics extensions
    in the kit file to match that version.  Updates the [dependencies] section, enabled list
    entries, and exact version dependency comments.

    Args:
        kit_file (str): Path to the kit file
        packman_xml_file (str): Path to the omni-physics.packman.xml file
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't modify the file, just report what would be done

    Returns:
        bool: True if successful, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    log("Updating physics extension versions...")

    # Check if packman XML file exists
    if not os.path.isfile(packman_xml_file):
        log(f"Packman XML file {packman_xml_file} does not exist, skipping physics version update")
        return True

    # Extract version from packman XML
    try:
        tree = ET.parse(packman_xml_file)
        root = tree.getroot()

        # Find the package element with name="omni_physics"
        physics_version = None
        for dependency in root.findall(".//dependency"):
            for package in dependency.findall(".//package"):
                if package.get("name") == "omni_physics":
                    version_attr = package.get("version")
                    if version_attr:
                        # Extract main version (e.g., "107.3.8" from "107.3.8-29124867-release_107.3-0ea8a1d1-${platform_target_abi}")
                        version_match = re.match(r"^(\d+\.\d+\.\d+)", version_attr)
                        if version_match:
                            physics_version = version_match.group(1)
                            log(f"Extracted physics version: {physics_version} from {version_attr}")
                            break
            if physics_version:
                break

        if not physics_version:
            log("Could not find omni_physics version in packman XML file")
            return True

    except Exception as e:
        print(f"Error parsing packman XML file: {e}")
        return False

    # Read the kit file
    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    updated_content = content

    # Extensions explicitly pinned in [dependencies] with exact = true
    pinned_physics_extensions = [
        "omni.physx.bundle",
        "omni.physx.fabric",
        "omni.physx.pvd",
        "omni.physics.tensors",
        "omni.physx.tensors",
        "omni.physx.tests",
        "omni.physx.tests.visual",
    ]

    PHYSICS_PREFIXES = (
        "omni.physx",
        "omni.physics",
        "omni.usdphysics",
        "omni.usd.schema.physx",
        "omni.convexdecomposition",
        "omni.kit.property.physics",
    )

    def is_physics_ext(name):
        """Check if an extension name belongs to the physics package."""
        for prefix in PHYSICS_PREFIXES:
            if name == prefix or name.startswith(prefix + "."):
                return True
        return False

    all_updates = []

    # 1. Update [dependencies] section (e.g. "omni.physx.bundle" = {version = "110.0.6", exact = true})
    for ext_name in pinned_physics_extensions:
        pattern = r'("' + re.escape(ext_name) + r'"\s*=\s*\{[^}]*?version\s*=\s*")([^"]+)(")'
        match = re.search(pattern, updated_content)
        if match:
            current_version = match.group(2)
            if current_version != physics_version:
                log(f"[dependencies] {ext_name}: {current_version} -> {physics_version}")
                all_updates.append((ext_name, current_version, "dependencies"))
                updated_content = re.sub(pattern, rf"\g<1>{physics_version}\3", updated_content)
        else:
            log(f"Could not find {ext_name} in [dependencies]")

    # 2. Update enabled list entries (e.g. "omni.physx-110.0.6")
    enabled_updates = []

    def _replace_enabled_entry(match):
        name = match.group(1)
        version = match.group(2)
        if is_physics_ext(name) and version != physics_version:
            enabled_updates.append((name, version))
            return f'"{name}-{physics_version}"'
        return match.group(0)

    updated_content = re.sub(r'"([\w.]+)-(\d+\.\d+\.\d+)"', _replace_enabled_entry, updated_content)
    for name, old_ver in enabled_updates:
        log(f"[enabled] {name}: {old_ver} -> {physics_version}")
        all_updates.append((name, old_ver, "enabled"))

    # 3. Update "# Exact Version dependencies:" comments (e.g. #\tomni.physx.bundle-110.0.6)
    comment_updates = []

    def _replace_comment_entry(match):
        prefix = match.group(1)
        name = match.group(2)
        version = match.group(3)
        if is_physics_ext(name) and version != physics_version:
            comment_updates.append((name, version))
            return f"{prefix}{name}-{physics_version}"
        return match.group(0)

    updated_content = re.sub(r"(#\s+)([\w.]+)-(\d+\.\d+\.\d+)", _replace_comment_entry, updated_content)
    for name, old_ver in comment_updates:
        log(f"[comment] {name}: {old_ver} -> {physics_version}")
        all_updates.append((name, old_ver, "comment"))

    if not all_updates:
        log("All physics extensions already at correct version.")
        return True

    if dry_run:
        print(f"Dry run: Would update {len(all_updates)} physics extension entries to version {physics_version}:")
        for name, old_ver, location in all_updates:
            print(f"  - {name}: {old_ver} -> {physics_version} ({location})")
    else:
        try:
            with open(kit_file, "w") as f:
                f.write(updated_content)
            print(f"Updated {len(all_updates)} physics extension entries to version {physics_version}:")
            for name, old_ver, location in all_updates:
                print(f"  - {name}: {old_ver} -> {physics_version} ({location})")
        except Exception as e:
            print(f"Error writing kit file: {e}")
            return False

    return True


def compare_with_template(kit_file, kit_sdk_xml, verbose=False, dry_run=False, commit_hash=None):
    """
    Compare the kit file with the template file from GitLab.
    Specifically compares the # Exact Version dependencies: and # Version lock for all dependencies: sections.

    Args:
        kit_file (str): Path to the kit file
        kit_sdk_xml (str): Path to the kit-sdk.packman.xml file (source of truth for kit version)
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't modify the file, just report what would be done
        commit_hash (str): Specific commit hash to use for the template URL. If None, derives branch from kit version.

    Returns:
        bool: True if successful, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    log("Comparing kit file with template...")

    # Read the kit file
    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    # Download the template file
    KAT_BASE_URL = "https://gitlab-master.nvidia.com/omniverse/kit-github/kit-app-template/-/raw"
    KAT_TEMPLATE_PATH = "templates/omni.all.template.extensions.kit"
    if commit_hash:
        template_url = f"{KAT_BASE_URL}/{commit_hash}/{KAT_TEMPLATE_PATH}"
        log(f"Using commit hash {commit_hash} for template URL")
    else:
        # Derive the KAT branch from the kit-kernel version in the packman XML (source of truth)
        kat_branch = None
        if os.path.isfile(kit_sdk_xml):
            try:
                with open(kit_sdk_xml, "r") as f:
                    xml_content = f.read()
                xml_match = re.search(r'name="kit-kernel"\s+version="(\d+)\.(\d+)\.\d+\+(\w+)\.', xml_content)
                if xml_match:
                    major_minor = f"{xml_match.group(1)}.{xml_match.group(2)}"
                    branch_type = xml_match.group(3)
                    if branch_type == "production":
                        kat_branch = f"production/{major_minor}"
                    else:
                        kat_branch = f"feature/{major_minor}"
                    log(f"Derived KAT branch '{kat_branch}' from kit-kernel version in {kit_sdk_xml}")
            except Exception as e:
                log(f"Could not read {kit_sdk_xml}: {e}")

        if not kat_branch:
            kat_branch = "feature/110.2"
            print(f"WARNING: Could not determine kit version from {kit_sdk_xml}, falling back to '{kat_branch}'")
        template_url = f"{KAT_BASE_URL}/{kat_branch}/{KAT_TEMPLATE_PATH}"

    print(f"Fetching template from: {template_url}")

    try:
        with urllib.request.urlopen(template_url) as response:
            template_content = response.read().decode("utf-8")
            log(f"Downloaded template file ({len(template_content)} bytes)")
    except urllib.error.HTTPError as e:
        print(f"Error downloading template file: HTTP {e.code} {e.reason}")
        print(f"  URL: {template_url}")
        return False
    except urllib.error.URLError as e:
        print(f"Error downloading template file: {e.reason}")
        print(f"  URL: {template_url}")
        print("  Check network connectivity and that the URL is accessible.")
        return False
    except Exception as e:
        print(f"Error downloading template file: {e}")
        print(f"  URL: {template_url}")
        return False

    # Extract the BEGIN GENERATED PART sections
    def extract_generated_part(content):
        begin_match = re.search(r"# BEGIN GENERATED PART.*?\n(.*?)# END GENERATED PART", content, re.DOTALL)
        if not begin_match:
            return None
        return begin_match.group(1)

    kit_generated = extract_generated_part(content)
    template_generated = extract_generated_part(template_content)

    if not kit_generated or not template_generated:
        missing = []
        if not kit_generated:
            missing.append(f"kit file ({kit_file})")
        if not template_generated:
            missing.append(f"template ({template_url})")
        print(f"Could not find '# BEGIN GENERATED PART' / '# END GENERATED PART' markers in: {', '.join(missing)}")
        if not template_generated:
            content_preview = template_content[:500].replace("\n", "\\n")
            print(f"  Template response preview: {content_preview}")
        return False

    # Extract exact version dependencies
    def extract_exact_versions(generated_part):
        versions = {}
        version_section = re.search(r"# Exact Version dependencies:(.*?)# Version lock", generated_part, re.DOTALL)
        if version_section:
            for line in version_section.group(1).split("\n"):
                if "#" in line:
                    match = re.search(r"#\s*([\w\.-]+)-([\d\.]+)", line)
                    if match:
                        name, version = match.groups()
                        versions[name] = version
        return versions

    kit_versions = extract_exact_versions(kit_generated)
    template_versions = extract_exact_versions(template_generated)

    # Compare exact versions
    version_mismatches = []
    for name, template_version in template_versions.items():
        if name in kit_versions:
            if kit_versions[name] != template_version:
                version_mismatches.append((name, kit_versions[name], template_version))
        else:
            version_mismatches.append((name, "missing", template_version))

    # Extract version locks from all enabled sections
    def extract_version_locks(generated_part):
        locks = {}
        # Find all enabled sections (including platform-specific ones)
        enabled_sections = re.findall(r"enabled\s*=\s*\[(.*?)\]", generated_part, re.DOTALL)
        for enabled_section in enabled_sections:
            for line in enabled_section.split("\n"):
                line = line.strip()
                if line and '"' in line:
                    # Extract the extension name and version
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        ext_with_version = match.group(1)
                        if "-" in ext_with_version:
                            name, version = ext_with_version.rsplit("-", 1)
                            locks[name] = version
        return locks

    kit_locks = extract_version_locks(kit_generated)
    template_locks = extract_version_locks(template_generated)

    def _parse_version(ver_str):
        """Parse a version string into a comparable tuple of ints."""
        try:
            return tuple(int(x) for x in ver_str.split("."))
        except (ValueError, AttributeError):
            return ()

    # Compare version locks — separate upgrades/new from downgrades
    lock_upgrades = []
    lock_downgrades = []
    for name, template_version in template_locks.items():
        if name in kit_locks:
            if kit_locks[name] != template_version:
                kit_ver = _parse_version(kit_locks[name])
                tmpl_ver = _parse_version(template_version)
                if tmpl_ver >= kit_ver:
                    lock_upgrades.append((name, kit_locks[name], template_version))
                else:
                    lock_downgrades.append((name, kit_locks[name], template_version))
        else:
            lock_upgrades.append((name, "missing", template_version))

    # Report mismatches
    if version_mismatches:
        print("\nExact Version dependencies mismatches:")
        for name, kit_version, template_version in version_mismatches:
            print(f"  - {name}: {kit_version} → {template_version}")

    if lock_upgrades:
        print("\nVersion lock upgrades from template:")
        for name, kit_version, template_version in lock_upgrades:
            print(f"  - {name}: {kit_version} → {template_version}")

    if lock_downgrades:
        print(f"\nSkipped {len(lock_downgrades)} version lock downgrades (template is older):")
        for name, kit_version, template_version in lock_downgrades:
            print(f"  - {name}: {kit_version} (keeping) vs {template_version} (template)")

    if lock_upgrades and not dry_run:
        updated_content = content
        for name, _, template_version in lock_upgrades:
            pattern = f'"{name}-[^"]*"'
            replacement = f'"{name}-{template_version}"'
            updated_content = re.sub(pattern, replacement, updated_content)

        try:
            with open(kit_file, "w") as f:
                f.write(updated_content)
            print(f"\nUpdated {len(lock_upgrades)} version locks in the kit file")
        except Exception as e:
            print(f"Error writing updated kit file: {e}")
            return False

    return True


def _derive_kit_sdk_branch(kit_sdk_xml, verbose=False):
    """Derive the Kit SDK source branch from the kit-kernel packman version."""

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    if not kit_sdk_xml or not os.path.isfile(kit_sdk_xml):
        log(f"Could not derive Kit SDK branch because {kit_sdk_xml} does not exist")
        return None

    try:
        with open(kit_sdk_xml, "r") as f:
            xml_content = f.read()
    except Exception as e:
        log(f"Could not read {kit_sdk_xml}: {e}")
        return None

    xml_match = re.search(r'name="kit-kernel"\s+version="(\d+)\.(\d+)\.\d+\+(\w+)\.', xml_content)
    if not xml_match:
        log(f"Could not find kit-kernel version in {kit_sdk_xml}")
        return None

    major_minor = f"{xml_match.group(1)}.{xml_match.group(2)}"
    branch_type = xml_match.group(3)
    if branch_type == "production":
        return f"production/{major_minor}"
    return f"feature/{major_minor}"


def _get_git_branch(repo_path, verbose=False):
    """Return the current branch for a git checkout."""

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    try:
        branch = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
    except Exception as e:
        log(f"Could not read git branch for {repo_path}: {e}")
        return None

    return branch


def _extract_generated_part(content):
    begin_match = re.search(r"# BEGIN GENERATED PART.*?\n(.*?)# END GENERATED PART", content, re.DOTALL)
    if not begin_match:
        return None
    return begin_match.group(1)


def _extract_enabled_version_locks(content):
    locks = {}
    enabled_sections = re.findall(r"enabled\s*=\s*\[(.*?)\]", content, re.DOTALL)
    for enabled_section in enabled_sections:
        for line in enabled_section.split("\n"):
            line = line.strip()
            if not line or '"' not in line:
                continue
            match = re.search(r'"([^"]+)"', line)
            if not match:
                continue
            ext_with_version = match.group(1)
            if "-" not in ext_with_version:
                continue
            name, version = ext_with_version.rsplit("-", 1)
            locks[name] = version
    return locks


def _parse_version(ver_str):
    """Parse a dotted numeric version string into a comparable tuple."""
    try:
        return tuple(int(x) for x in ver_str.split("."))
    except (ValueError, AttributeError):
        return ()


def compare_with_kit_sdk_version_locks(
    kit_file,
    kit_sdk_xml,
    verbose=False,
    dry_run=False,
    kit_sdk_repo=None,
    kit_sdk_version_locks=None,
):
    """
    Compare the kit file with the local kit-sdk-public version locks and update matching locks.

    Lower versions from kit-sdk-public are reported but not applied.

    Args:
        kit_file (str): Path to the kit file.
        kit_sdk_xml (str): Path to the kit-sdk.packman.xml file.
        verbose (bool): If True, print detailed debug information.
        dry_run (bool): If True, don't modify the file, just report what would be done.
        kit_sdk_repo (str): Path to the kit-sdk-public checkout.
        kit_sdk_version_locks (str): Direct path to a version_locks.kit file.

    Returns:
        bool: True if successful, False otherwise.
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    if not kit_sdk_version_locks:
        if not kit_sdk_repo:
            print("Error: --match-kit-sdk requires --kit-sdk-repo or --kit-sdk-version-locks.")
            return False
        kit_sdk_version_locks = os.path.join(kit_sdk_repo, "source", "version-locks", "version_locks.kit")

    if kit_sdk_repo:
        expected_branch = _derive_kit_sdk_branch(kit_sdk_xml, verbose)
        current_branch = _get_git_branch(kit_sdk_repo, verbose)
        if not current_branch:
            print(f"Error: Could not determine current branch for Kit SDK repo: {kit_sdk_repo}")
            return False
        if expected_branch and current_branch != expected_branch:
            print("Error: Kit SDK repo branch does not match the kit-kernel branch.")
            print(f"  Repo: {kit_sdk_repo}")
            print(f"  Current branch: {current_branch}")
            print(f"  Expected branch: {expected_branch}")
            return False
        if expected_branch:
            log(f"Kit SDK repo branch matches kit-kernel branch: {current_branch}")

    if not os.path.isfile(kit_sdk_version_locks):
        print(f"Error: Kit SDK version locks file does not exist: {kit_sdk_version_locks}")
        return False

    print(f"Using Kit SDK version locks: {kit_sdk_version_locks}")

    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    try:
        with open(kit_sdk_version_locks, "r") as f:
            locks_content = f.read()
    except Exception as e:
        print(f"Error reading Kit SDK version locks file: {e}")
        return False

    kit_generated = _extract_generated_part(content)
    if not kit_generated:
        print(f"Could not find '# BEGIN GENERATED PART' / '# END GENERATED PART' markers in: {kit_file}")
        return False

    kit_locks = _extract_enabled_version_locks(kit_generated)
    sdk_locks = _extract_enabled_version_locks(locks_content)
    if not sdk_locks:
        print(f"Could not find any enabled version locks in: {kit_sdk_version_locks}")
        return False

    lock_updates = []
    lower_locks = []
    for name, kit_version in kit_locks.items():
        sdk_version = sdk_locks.get(name)
        if sdk_version and sdk_version != kit_version:
            kit_ver = _parse_version(kit_version)
            sdk_ver = _parse_version(sdk_version)
            if kit_ver and sdk_ver and sdk_ver < kit_ver:
                lower_locks.append((name, kit_version, sdk_version))
            else:
                lock_updates.append((name, kit_version, sdk_version))

    if not lock_updates and not lower_locks:
        log("All matching extension version locks already match Kit SDK version_locks.kit.")
        return True

    if lock_updates:
        action = "Dry run: Would update" if dry_run else "Updated"
        print(f"\n{action} {len(lock_updates)} version locks from Kit SDK version_locks.kit:")
        for name, kit_version, sdk_version in lock_updates:
            print(f"  - {name}: {kit_version} -> {sdk_version}")

    if lower_locks:
        print(f"\nSkipped {len(lower_locks)} lower version locks from Kit SDK version_locks.kit:")
        for name, kit_version, sdk_version in lower_locks:
            print(f"  - {name}: {kit_version} (keeping) vs {sdk_version} (Kit SDK)")

    if dry_run:
        return True

    updated_content = content
    for name, old_version, sdk_version in lock_updates:
        pattern = r'("' + re.escape(name) + r"-)" + re.escape(old_version) + r'(")'

        def _replace_lock(match):
            return f"{match.group(1)}{sdk_version}{match.group(2)}"

        updated_content, count = re.subn(pattern, _replace_lock, updated_content)
        if count == 0:
            print(f"WARNING: Failed to update enabled version lock for {name}")

    try:
        with open(kit_file, "w") as f:
            f.write(updated_content)
    except Exception as e:
        print(f"Error writing updated kit file: {e}")
        return False

    return True


def _reconcile_file(filepath, enabled_versions, verbose=False, dry_run=False):
    """Reconcile version constraints in a single .kit file against the enabled version map.

    Returns a list of (ext_name, old_constraint, new_constraint) tuples that were applied,
    or None on error.
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    dep_pattern = re.compile(r'"([\w.]+)"\s*=\s*\{([^}]*)\}')
    updated_content = content
    updates = []

    for dep_match in dep_pattern.finditer(content):
        ext_name = dep_match.group(1)
        attrs = dep_match.group(2)

        if "exact" in attrs and "true" in attrs:
            log(f"Skipping {ext_name} (exact = true)")
            continue

        ver_match = re.search(r'version\s*=\s*"([^"]+)"', attrs)
        if not ver_match:
            continue

        constraint = ver_match.group(1)

        if ext_name not in enabled_versions:
            continue

        enabled_ver = enabled_versions[ext_name]
        enabled_parts = enabled_ver.split(".")

        if constraint.startswith("~"):
            tilde_ver = constraint[1:]
            depth = len(tilde_ver.split("."))
            enabled_prefix = ".".join(enabled_parts[:depth])

            if tilde_ver == enabled_prefix:
                log(f"{ext_name}: constraint {constraint} already compatible with {enabled_ver}")
                continue

            new_constraint = "~" + enabled_prefix
            updates.append((ext_name, constraint, new_constraint))
        else:
            if constraint == enabled_ver:
                log(f"{ext_name}: constraint {constraint} already matches {enabled_ver}")
                continue

            new_constraint = enabled_ver
            updates.append((ext_name, constraint, new_constraint))

    if not updates:
        return []

    if not dry_run:
        for ext_name, old_constraint, new_constraint in updates:
            pattern = (
                r'("' + re.escape(ext_name) + r'"\s*=\s*\{[^}]*version\s*=\s*")' + re.escape(old_constraint) + r'(")'
            )
            updated_content = re.sub(pattern, rf"\g<1>{new_constraint}\2", updated_content)

        try:
            with open(filepath, "w") as f:
                f.write(updated_content)
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return None

    return updates


def reconcile_dependency_versions(kit_file, verbose=False, dry_run=False):
    """
    After a KAT sync, reconcile version constraints in [dependencies] with the
    actual versions in the enabled list.  Scans both ``kit_file`` and all
    sibling ``.kit`` files in the same directory so that transitive constraints
    (e.g. in ``isaacsim.exp.full.kit``) are also corrected.

    Skips entries with ``exact = true`` (handled by the physics / XR updaters).

    Args:
        kit_file (str): Path to the primary kit file (must contain the enabled list)
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't modify files, just report

    Returns:
        bool: True if successful, False otherwise
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    log("Reconciling [dependencies] version constraints with enabled list...")

    try:
        with open(kit_file, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading kit file: {e}")
        return False

    # Build a canonical version map from the enabled list in the primary kit file
    enabled_versions = {}
    for m in re.finditer(r'"([\w.]+)-(\d+(?:\.\d+)+)"', content):
        enabled_versions[m.group(1)] = m.group(2)
    log(f"Found {len(enabled_versions)} extensions in enabled list")

    # Collect all .kit files to reconcile: primary file + siblings in the same directory
    apps_dir = os.path.dirname(os.path.abspath(kit_file))
    kit_files = [kit_file]
    try:
        for fname in sorted(os.listdir(apps_dir)):
            if fname.endswith(".kit"):
                full = os.path.join(apps_dir, fname)
                if os.path.abspath(full) != os.path.abspath(kit_file):
                    kit_files.append(full)
    except OSError as e:
        log(f"Could not list apps directory {apps_dir}: {e}")

    all_updates = []

    for kf in kit_files:
        basename = os.path.basename(kf)
        updates = _reconcile_file(kf, enabled_versions, verbose, dry_run)
        if updates is None:
            print(f"WARNING: Failed to reconcile {basename}")
            continue
        for ext_name, old_c, new_c in updates:
            all_updates.append((basename, ext_name, old_c, new_c))

    if not all_updates:
        log("All [dependencies] version constraints are compatible with the enabled list.")
        return True

    action = "Dry run: Would update" if dry_run else "Updated"
    print(f"{action} {len(all_updates)} dependency version constraints to match enabled list:")
    for basename, ext_name, old_c, new_c in all_updates:
        print(f"  - {ext_name}: {old_c} -> {new_c}  ({basename})")

    return True


def find_enabled_sections(lines, verbose=False):
    """
    Find all enabled sections in the kit file, including platform-specific sections.

    Args:
        lines (list): List of lines from the kit file
        verbose (bool): If True, print detailed debug information

    Returns:
        list: List of tuples (section_name, start_line, end_line) for each enabled section found
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    sections = []
    current_section = None
    bracket_level = 0
    enabled_start = None

    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Check for settings.app.exts sections (including platform-specific ones)
        if stripped_line.startswith("[settings.app.exts"):
            if current_section and enabled_start is not None:
                # We found a new section while still processing the previous one - close the previous one
                sections.append((current_section, enabled_start, i))
                log(f"Closed previous section {current_section} at line {i}")

            current_section = stripped_line
            enabled_start = None
            bracket_level = 0
            log(f"Found section {current_section} at line {i+1}")
            continue

        # Look for enabled = [ within the current section
        if current_section and "enabled = [" in stripped_line:
            enabled_start = i + 1
            bracket_level = 1  # We've opened one bracket
            log(f"Found enabled = [ at line {i+1} in section {current_section}")
            continue

        # Track bracket levels to find the end of the enabled list
        if current_section and enabled_start is not None:
            bracket_level += line.count("[") - line.count("]")

            if bracket_level == 0:
                sections.append((current_section, enabled_start, i))
                log(f"Completed section {current_section} from line {enabled_start+1} to {i+1}")
                current_section = None
                enabled_start = None

    # Handle case where file ends while we're still in a section
    if current_section and enabled_start is not None:
        sections.append((current_section, enabled_start, len(lines)))
        log(f"Completed final section {current_section} from line {enabled_start+1} to end of file")

    return sections


def process_enabled_section(
    lines, section_start, section_end, built_ext_bases, dir_deprecated_ext_bases, apps_ext_bases, verbose=False
):
    """
    Process a single enabled section and return the cleaned section with removed extensions info.

    Args:
        lines (list): All lines from the kit file
        section_start (int): Start line of the enabled section
        section_end (int): End line of the enabled section
        built_ext_bases (list): Base names of built extensions
        dir_deprecated_ext_bases (list): Base names of deprecated extensions
        apps_ext_bases (list): Base names of app extensions
        verbose (bool): If True, print detailed debug information

    Returns:
        tuple: (new_section_lines, removed_extensions_list)
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    extensions_section = lines[section_start:section_end]
    new_extensions_section = []
    removed_exts = []

    # Extension pattern: looks for quoted strings that might be extension names
    extension_pattern = re.compile(r'["\']([^"\']+?(?:-[^"\']+)?)["\']')

    for i, line in enumerate(extensions_section):
        line_num = section_start + i + 1
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
            log(f"Line {line_num}: Extension {ext_with_version} matches built extension")
            remove_extension = True
            reason = "built"
        elif ext_base in dir_deprecated_ext_bases:
            log(f"Line {line_num}: Extension {ext_with_version} matches deprecated directory extension")
            remove_extension = True
            reason = "deprecated directory"
        elif ext_base in apps_ext_bases:
            log(f"Line {line_num}: Extension {ext_with_version} matches app kit file")
            remove_extension = True
            reason = "apps directory"

        if remove_extension:
            removed_exts.append((ext_with_version, reason))
        else:
            log(f"Line {line_num}: Keeping extension {ext_with_version}")
            new_extensions_section.append(line)

    return new_extensions_section, removed_exts


def _get_local_extension_bases(build_dir, deprecated_dir, apps_dir, internal_dir=None, verbose=False):
    """Collect extension base names that are produced by this repo."""

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    local_ext_bases = set()

    extension_dirs = [(build_dir, "built"), (deprecated_dir, "deprecated")]
    if internal_dir:
        extension_dirs.append((internal_dir, "internal"))

    for directory, label in extension_dirs:
        if not os.path.isdir(directory):
            log(f"{label} directory {directory} does not exist")
            continue
        try:
            extensions = os.listdir(directory)
        except Exception as e:
            print(f"Error reading {label} directory {directory}: {e}")
            return None
        local_ext_bases.update(ext.split("-")[0] for ext in extensions)
        log(f"Found {len(extensions)} {label} extensions: {extensions}")

    if os.path.isdir(apps_dir):
        try:
            apps_extensions = [f for f in os.listdir(apps_dir) if f.endswith(".kit")]
        except Exception as e:
            print(f"Error reading apps directory {apps_dir}: {e}")
            return None
        for ext in apps_extensions:
            ext_without_kit = ext[:-4]
            local_ext_bases.add(ext_without_kit.split("-")[0])
        log(f"Found {len(apps_extensions)} app kit files: {apps_extensions}")
    else:
        log(f"Apps directory {apps_dir} does not exist")

    return local_ext_bases


def _find_generated_part(content):
    match = re.search(r"(# BEGIN GENERATED PART.*?\n)(.*?)(# END GENERATED PART)", content, re.DOTALL)
    if not match:
        return None
    return match


def _extract_comment_ext_base(line):
    match = re.search(r"#\s+([\w.]+)-(\d+(?:\.\d+)+)", line)
    if not match:
        return None
    return match.group(1)


def _extract_enabled_ext_base(line):
    match = re.search(r'["\']([^"\']+)["\']', line)
    if not match:
        return None
    ext_with_version = match.group(1)
    if "-" not in ext_with_version:
        return ext_with_version
    return ext_with_version.split("-")[0]


def _collect_local_generated_lines(generated_part, local_ext_bases):
    local_exact_lines = {}
    local_enabled_lines = {}
    in_exact_versions = False
    in_enabled = False
    bracket_level = 0

    for line in generated_part.splitlines(True):
        stripped = line.strip()

        if stripped.startswith("# Exact Version dependencies:"):
            in_exact_versions = True
            continue
        if stripped.startswith("# Version lock for all dependencies:"):
            in_exact_versions = False
            continue

        if "enabled = [" in stripped:
            in_enabled = True
            bracket_level = 1
            continue

        if in_enabled:
            bracket_level += line.count("[") - line.count("]")
            ext_base = _extract_enabled_ext_base(line)
            if ext_base in local_ext_bases:
                local_enabled_lines[ext_base] = line
            if bracket_level == 0:
                in_enabled = False
            continue

        if in_exact_versions:
            ext_base = _extract_comment_ext_base(line)
            if ext_base in local_ext_bases:
                local_exact_lines[ext_base] = line

    return local_exact_lines, local_enabled_lines


def _merge_generated_part(baseline_part, current_part, local_ext_bases):
    current_exact_lines, current_enabled_lines = _collect_local_generated_lines(current_part, local_ext_bases)
    merged_lines = []
    emitted_enabled_bases = set()
    in_exact_versions = False
    in_enabled = False
    bracket_level = 0

    for line in baseline_part.splitlines(True):
        stripped = line.strip()

        if stripped.startswith("# Exact Version dependencies:"):
            in_exact_versions = True
            merged_lines.append(line)
            continue
        if stripped.startswith("# Version lock for all dependencies:"):
            in_exact_versions = False
            merged_lines.append(line)
            continue

        if "enabled = [" in stripped:
            in_enabled = True
            bracket_level = 1
            merged_lines.append(line)
            continue

        if in_enabled:
            next_bracket_level = bracket_level + line.count("[") - line.count("]")
            if next_bracket_level == 0:
                for ext_base, current_line in current_enabled_lines.items():
                    if ext_base not in emitted_enabled_bases:
                        merged_lines.append(current_line)
                        emitted_enabled_bases.add(ext_base)
                merged_lines.append(line)
                in_enabled = False
                bracket_level = 0
                continue

            ext_base = _extract_enabled_ext_base(line)
            if ext_base in current_enabled_lines:
                merged_lines.append(current_enabled_lines[ext_base])
                emitted_enabled_bases.add(ext_base)
            else:
                merged_lines.append(line)
            bracket_level = next_bracket_level
            continue

        if in_exact_versions:
            ext_base = _extract_comment_ext_base(line)
            if ext_base in current_exact_lines:
                merged_lines.append(current_exact_lines[ext_base])
            else:
                merged_lines.append(line)
            continue

        merged_lines.append(line)

    return "".join(merged_lines)


def restore_non_local_generated_changes(
    baseline_kit_file_path,
    kit_file_path=None,
    build_dir_path=None,
    deprecated_dir_path=None,
    apps_dir_path=None,
    internal_dir_path=None,
    verbose=False,
    dry_run=False,
):
    """
    Restore generated extscache changes that do not belong to extensions produced by this repo.

    The current kit file is compared against a pre-build baseline. Generated-block entries for
    extensions in the build, deprecated, or apps directories are kept from the current file; all
    other generated-block content is restored from the baseline.
    """

    def log(msg):
        if verbose:
            print(f"DEBUG: {msg}")

    kit_file = kit_file_path or "source/apps/isaacsim.exp.extscache.kit"
    build_dir = build_dir_path or "_build/linux-x86_64/release/exts"
    deprecated_dir = deprecated_dir_path or "_build/linux-x86_64/release/extsDeprecated"
    apps_dir = apps_dir_path or "_build/linux-x86_64/release/apps"
    internal_dir = internal_dir_path or "_build/linux-x86_64/release/extsInternal"

    local_ext_bases = _get_local_extension_bases(build_dir, deprecated_dir, apps_dir, internal_dir, verbose)
    if local_ext_bases is None:
        return False
    log(f"Local extension base names: {sorted(local_ext_bases)}")

    try:
        with open(baseline_kit_file_path, "r") as f:
            baseline_content = f.read()
        with open(kit_file, "r") as f:
            current_content = f.read()
    except Exception as e:
        print(f"Error reading kit files: {e}")
        return False

    baseline_match = _find_generated_part(baseline_content)
    current_match = _find_generated_part(current_content)
    if not baseline_match or not current_match:
        missing = []
        if not baseline_match:
            missing.append(baseline_kit_file_path)
        if not current_match:
            missing.append(kit_file)
        print(f"Could not find generated part markers in: {', '.join(missing)}")
        return False

    merged_generated = _merge_generated_part(baseline_match.group(2), current_match.group(2), local_ext_bases)
    merged_content = (
        current_content[: current_match.start(2)] + merged_generated + current_content[current_match.end(2) :]
    )

    if merged_content == current_content:
        print("No non-local generated changes need to be restored.")
        return True

    if dry_run:
        print("Dry run: Would restore non-local generated changes from the baseline kit file.")
        return True

    try:
        with open(kit_file, "w") as f:
            f.write(merged_content)
    except Exception as e:
        print(f"Error writing kit file {kit_file}: {e}")
        return False

    print("Restored non-local generated changes while keeping repo extension updates.")
    return True


def clean_extscache(
    kit_file_path=None,
    build_dir_path=None,
    deprecated_dir_path=None,
    apps_dir_path=None,
    internal_dir_path=None,
    packman_xml_path=None,
    kit_sdk_xml_path=None,
    create_dir=False,
    verbose=False,
    dry_run=False,
    check_deps=True,
    check_locks=True,
    update_locks=False,
    update_physics=True,
    match_kat=False,
    match_kit_sdk=False,
    commit_hash=None,
    kit_sdk_repo=None,
    kit_sdk_version_locks=None,
):
    """
    Removes extensions from all enabled sections in the kit file if they exist in the build directory,
    the deprecated directory, or the apps directory. Also performs various validation and update tasks.

    Args:
        kit_file_path (str): Path to the kit file (default: source/apps/isaacsim.exp.extscache.kit)
        build_dir_path (str): Path to the build directory (default: _build/linux-x86_64/release/exts)
        deprecated_dir_path (str): Path to the deprecated directory (default: _build/linux-x86_64/release/extsDeprecated)
        apps_dir_path (str): Path to the apps directory (default: _build/linux-x86_64/release/apps)
        internal_dir_path (str): Path to the extsInternal directory
            (default: _build/linux-x86_64/release/extsInternal). Extensions here are validated against
            the kit file's [dependencies] section but are NOT stripped from enabled lists, since
            extsInternal is not used as a source for the extscache app; the extensions must remain
            version-locked so ``repo_deploy_exts`` publishes them and they are downloaded from the
            registry at runtime (same pattern as isaacsim.util.debug_draw).
        packman_xml_path (str): Path to the omni-physics.packman.xml file (default: deps/omni-physics.packman.xml)
        kit_sdk_xml_path (str): Path to the kit-sdk.packman.xml file (default: deps/kit-sdk.packman.xml)
        create_dir (bool): If True, create the build directory if it doesn't exist
        verbose (bool): If True, print detailed debug information
        dry_run (bool): If True, don't modify the file, just report what would be done
        check_deps (bool): If True, check that all extensions are listed in dependencies
        check_locks (bool): If True, check that version locks match the SDK hash
        update_locks (bool): If True, update any mismatched version locks to match the SDK hash
        update_physics (bool): If True, update physics extension versions to match packman XML
        match_kat (bool): If True, compare with template file and update version locks
        commit_hash (str): Specific commit hash to use for the template URL when match_kat is True
        match_kit_sdk (bool): If True, compare with kit-sdk-public version_locks.kit
        kit_sdk_repo (str): Path to the kit-sdk-public checkout
        kit_sdk_version_locks (str): Direct path to kit-sdk-public source/version-locks/version_locks.kit

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
    default_internal_dir = "_build/linux-x86_64/release/extsInternal"
    default_packman_xml = "deps/omni-physics.packman.xml"
    default_kit_sdk_xml = "deps/kit-sdk.packman.xml"

    # Use provided paths or defaults
    kit_file = kit_file_path or default_kit_file
    build_dir = build_dir_path or default_build_dir
    deprecated_dir = deprecated_dir_path or default_deprecated_dir
    apps_dir = apps_dir_path or default_apps_dir
    internal_dir = internal_dir_path or default_internal_dir
    packman_xml = packman_xml_path or default_packman_xml
    kit_sdk_xml = kit_sdk_xml_path or default_kit_sdk_xml

    log(f"Using kit file: {os.path.abspath(kit_file)}")
    log(f"Using build directory: {os.path.abspath(build_dir)}")
    log(f"Using deprecated directory: {os.path.abspath(deprecated_dir)}")
    log(f"Using apps directory: {os.path.abspath(apps_dir)}")
    log(f"Using internal directory: {os.path.abspath(internal_dir)}")
    log(f"Using packman XML: {os.path.abspath(packman_xml)}")

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

    # Find all enabled sections
    enabled_sections = find_enabled_sections(lines, verbose)

    if not enabled_sections:
        print("Could not find any enabled extensions sections!")
        if verbose:
            print("First 20 lines of file:")
            for i, line in enumerate(lines[:20]):
                print(f"{i+1}: {line.rstrip()}")
        return False

    log(f"Found {len(enabled_sections)} enabled sections")
    for section_name, start, end in enabled_sections:
        log(f"  {section_name}: lines {start+1} to {end+1}")

    # Prepare extension base names
    built_ext_bases = [ext.split("-")[0] for ext in built_extensions]
    log(f"Built extension base names: {built_ext_bases}")

    dir_deprecated_ext_bases = [ext.split("-")[0] for ext in dir_deprecated_extensions]
    log(f"Deprecated extension base names from directory: {dir_deprecated_ext_bases}")

    # Extract extension base names from apps directory
    apps_ext_bases = []
    for ext in apps_extensions:
        # Remove .kit extension first
        ext_without_kit = ext[:-4] if ext.endswith(".kit") else ext
        # Then get the base name (part before version)
        base_name = ext_without_kit.split("-")[0]
        apps_ext_bases.append(base_name)
    log(f"Apps base names: {apps_ext_bases}")

    # Process each enabled section
    new_lines = list(lines)  # Make a copy to modify
    total_removed = 0
    all_removed_exts = []

    # Process sections in reverse order to maintain line number accuracy
    for section_name, section_start, section_end in reversed(enabled_sections):
        log(f"Processing section {section_name} from line {section_start+1} to {section_end+1}")

        new_section, removed_exts = process_enabled_section(
            lines, section_start, section_end, built_ext_bases, dir_deprecated_ext_bases, apps_ext_bases, verbose
        )

        # Replace the section in new_lines
        new_lines[section_start:section_end] = new_section

        total_removed += len(removed_exts)
        all_removed_exts.extend([(ext, reason, section_name) for ext, reason in removed_exts])

        log(f"Section {section_name}: removed {len(removed_exts)} extensions")

    if total_removed == 0:
        print("No extensions need to be removed.")
    else:
        if dry_run:
            print(f"Dry run: Would remove {total_removed} extensions:")
            for ext, reason, section_name in all_removed_exts:
                print(f"  - {ext} ({reason}) from {section_name}")
        else:
            try:
                # Write the updated file
                with open(kit_file, "w") as f:
                    f.writelines(new_lines)
            except Exception as e:
                print(f"Error writing to kit file: {e}")
                return False

            # Summarize removed extensions by category and section
            built_removed = [ext for ext, reason, section in all_removed_exts if reason == "built"]
            dir_deprecated_removed = [
                ext for ext, reason, section in all_removed_exts if reason == "deprecated directory"
            ]
            apps_removed = [ext for ext, reason, section in all_removed_exts if reason == "apps directory"]

            print(f"Removed {total_removed} extensions from enabled sections:")
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
        dependencies_ok = check_dependencies(kit_file, build_dir, deprecated_dir, internal_dir, verbose)
        if not dependencies_ok and not dry_run:
            print(
                f"WARNING: Some extensions in build/deprecated/internal dirs are missing from the [dependencies] section in {kit_file}."
            )

    # Check version locks if requested
    if check_locks:
        locks_ok = check_version_locks(kit_file, verbose, dry_run, update_locks)
        if not locks_ok and not dry_run:
            print("WARNING: Some extensions have version locks that don't match the SDK hash.")

    # Compare with template if requested (runs before update_physics so
    # physics versions from packman XML take precedence over template versions)
    if match_kat:
        template_ok = compare_with_template(kit_file, kit_sdk_xml, verbose, dry_run, commit_hash)
        if not template_ok and not dry_run:
            print("WARNING: Failed to compare with template file. See errors above for details.")

        # Reconcile [dependencies] constraints that may now conflict with
        # the updated enabled list (e.g. ~209.0 vs 209.1.1)
        reconcile_ok = reconcile_dependency_versions(kit_file, verbose, dry_run)
        if not reconcile_ok and not dry_run:
            print("WARNING: Failed to reconcile dependency version constraints.")

    # Compare with kit-sdk-public version locks if requested. This runs before
    # update_physics so physics versions from packman XML take precedence.
    if match_kit_sdk:
        kit_sdk_ok = compare_with_kit_sdk_version_locks(
            kit_file,
            kit_sdk_xml,
            verbose,
            dry_run,
            kit_sdk_repo=kit_sdk_repo,
            kit_sdk_version_locks=kit_sdk_version_locks,
        )
        if not kit_sdk_ok and not dry_run:
            print("WARNING: Failed to compare with kit-sdk-public version locks. See errors above for details.")

        reconcile_ok = reconcile_dependency_versions(kit_file, verbose, dry_run)
        if not reconcile_ok and not dry_run:
            print("WARNING: Failed to reconcile dependency version constraints.")

    # Update physics versions if requested (runs after match_kat/match_kit_sdk
    # to correct any physics version overrides from external lock sources)
    if update_physics:
        update_physics_ok = update_physics_versions(kit_file, packman_xml, verbose, dry_run)
        if not update_physics_ok and not dry_run:
            print(f"WARNING: Failed to update physics extension versions (packman XML: {packman_xml}).")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
Clean the extension cache by removing extensions from the enabled section in the kit file if they:
1. Exist in the build directory (_build/linux-x86_64/release/exts)
2. Exist in the deprecated directory (_build/linux-x86_64/release/extsDeprecated)
3. Exist in the apps directory (_build/linux-x86_64/release/apps)

This script also checks that all extensions in the build, deprecated, and extsInternal
directories are properly listed in the [dependencies] section. extsInternal extensions
are NOT removed from the enabled list: they must stay version-locked so that
repo_deploy_exts publishes them and they are downloaded from the registry at runtime.

This script can also verify that extension version locks match the Kit SDK Version hash,
and optionally update them to match the current SDK hash.

It can synchronize generated extension version locks with kit-sdk-public's
source/version-locks/version_locks.kit for the matching kit-kernel branch.

Additionally, this script can synchronize physics extension versions with the version
specified in the omni-physics.packman.xml file to ensure consistency between the
physics package and extension versions.

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
    parser.add_argument(
        "--internal-dir",
        help=(
            "Path to the extsInternal directory (default: _build/linux-x86_64/release/extsInternal). "
            "Extensions here are validated against [dependencies] but are NOT removed from enabled "
            "lists, so repo_deploy_exts will publish them."
        ),
    )
    parser.add_argument(
        "--packman-xml", help="Path to the omni-physics.packman.xml file (default: deps/omni-physics.packman.xml)"
    )
    parser.add_argument(
        "--kit-sdk-xml", help="Path to the kit-sdk.packman.xml file (default: deps/kit-sdk.packman.xml)"
    )
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
    parser.add_argument(
        "--update-locks",
        action="store_true",
        help="Update extension version locks to match the SDK hash when they don't match",
    )
    parser.add_argument(
        "--update-physics",
        action="store_true",
        help="Update physics extension versions to match packman XML",
    )
    parser.add_argument(
        "--match-kat",
        action="store_true",
        help="Compare with template file and update version locks",
    )
    parser.add_argument(
        "--commit-hash",
        help="Specific commit hash to use for the template URL when match_kat is True",
    )
    parser.add_argument(
        "--match-kit-sdk",
        action="store_true",
        help="Compare with kit-sdk-public source/version-locks/version_locks.kit and update matching locks",
    )
    parser.add_argument(
        "--kit-sdk-repo",
        default="/home/hmazhar/repos/kit-sdk-public",
        help="Path to the kit-sdk-public checkout (default: /home/hmazhar/repos/kit-sdk-public)",
    )
    parser.add_argument(
        "--kit-sdk-version-locks",
        help="Direct path to kit-sdk-public source/version-locks/version_locks.kit",
    )
    parser.add_argument(
        "--restore-non-local-from",
        help=(
            "Path to a baseline kit file. Restores generated-block changes for extensions that are "
            "not present in the build, deprecated, or apps directories."
        ),
    )

    args = parser.parse_args()

    if args.match_kat and args.match_kit_sdk:
        parser.error("--match-kat and --match-kit-sdk cannot be used together")

    if args.restore_non_local_from:
        success = restore_non_local_generated_changes(
            baseline_kit_file_path=args.restore_non_local_from,
            kit_file_path=args.kit_file,
            build_dir_path=args.build_dir,
            deprecated_dir_path=args.deprecated_dir,
            apps_dir_path=args.apps_dir,
            internal_dir_path=args.internal_dir,
            verbose=args.verbose,
            dry_run=args.dry_run,
        )
    else:
        success = clean_extscache(
            kit_file_path=args.kit_file,
            build_dir_path=args.build_dir,
            deprecated_dir_path=args.deprecated_dir,
            apps_dir_path=args.apps_dir,
            internal_dir_path=args.internal_dir,
            packman_xml_path=args.packman_xml,
            kit_sdk_xml_path=args.kit_sdk_xml,
            create_dir=args.create_dir,
            verbose=args.verbose,
            dry_run=args.dry_run,
            check_deps=not args.no_deps_check,
            check_locks=not args.no_locks_check,
            update_locks=args.update_locks,
            update_physics=args.update_physics,
            match_kat=args.match_kat,
            match_kit_sdk=args.match_kit_sdk,
            commit_hash=args.commit_hash,
            kit_sdk_repo=args.kit_sdk_repo,
            kit_sdk_version_locks=args.kit_sdk_version_locks,
        )

    if not success:
        sys.exit(1)
