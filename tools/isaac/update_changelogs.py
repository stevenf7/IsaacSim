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
"""
Script to update and validate changelogs across extensions.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


# Define parse_toml at the module level
def parse_toml(toml_str):
    """Very simple TOML parser for basic needs."""
    result = {}
    current_section = result

    for line in toml_str.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Handle section headers
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section = result

            # Handle nested sections
            if "." in section_name:
                parts = section_name.split(".")
                for part in parts:
                    if part not in current_section:
                        current_section[part] = {}
                    current_section = current_section[part]
            else:
                if section_name not in result:
                    result[section_name] = {}
                current_section = result[section_name]
            continue

        # Handle key-value pairs
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Handle string values
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            # Handle numbers
            elif value.isdigit():
                value = int(value)
            elif value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False

            current_section[key] = value

    return result


# Try to import required packages with fallbacks
try:
    import tomli as toml_reader
except ImportError:
    try:
        import tomlkit as toml_reader
    except ImportError:

        class TomliWrapper:
            @staticmethod
            def load(file_obj):
                return parse_toml(file_obj.read())

        toml_reader = TomliWrapper()

# Try to import tomlkit for writing TOML
try:
    import tomlkit as toml_writer
except ImportError:
    # Simple fallback for TOML writing
    class TomlWriterWrapper:
        @staticmethod
        def load(file_obj):
            return parse_toml(file_obj.read())

        @staticmethod
        def dump(data, file_obj):
            """Simple TOML writer"""
            lines = []

            def write_section(section_data, prefix=""):
                section_lines = []
                regular_items = {}
                table_items = {}

                # Separate regular key-value pairs from nested tables
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        table_items[key] = value
                    else:
                        regular_items[key] = value

                # Write regular key-value pairs
                for key, value in sorted(regular_items.items()):
                    if isinstance(value, str):
                        value_str = f'"{value}"'
                    else:
                        value_str = str(value).lower() if isinstance(value, bool) else str(value)
                    section_lines.append(f"{key} = {value_str}")

                # Add a blank line if we have both regular items and tables
                if regular_items and table_items:
                    section_lines.append("")

                # Write nested tables
                for key, value in sorted(table_items.items()):
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    table_section = f"[{new_prefix}]"
                    section_lines.append(table_section)
                    nested_lines = write_section(value, new_prefix)
                    section_lines.extend(nested_lines)
                    section_lines.append("")

                return section_lines

            # Handle top-level items that aren't in a section
            top_level = {k: v for k, v in data.items() if not isinstance(v, dict)}
            for key, value in sorted(top_level.items()):
                if isinstance(value, str):
                    value_str = f'"{value}"'
                else:
                    value_str = str(value).lower() if isinstance(value, bool) else str(value)
                lines.append(f"{key} = {value_str}")

            if top_level:
                lines.append("")

            # Handle sections
            sections = {k: v for k, v in data.items() if isinstance(v, dict)}
            for section, section_data in sorted(sections.items()):
                lines.append(f"[{section}]")
                section_lines = write_section(section_data, section)
                lines.extend(section_lines)

            file_obj.write("\n".join(lines))

    toml_writer = TomlWriterWrapper()

# Try to import packaging.version for version comparison
try:
    from packaging import version as pkg_version

    def parse_version(version_str):
        return pkg_version.parse(version_str)

except ImportError:
    print("Warning: packaging module not installed. Using simple version comparison.")

    class SimpleVersion:
        def __init__(self, version_str):
            self.version_str = version_str
            parts = version_str.split(".")

            # Parse major.minor.patch
            self.major = int(parts[0]) if parts and parts[0].isdigit() else 0
            self.minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            self.patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

            # Handle pre-release suffixes like -alpha, -beta, etc.
            if len(parts) > 3 or (len(parts) > 2 and not parts[2].isdigit()):
                self.is_prerelease = True
            else:
                self.is_prerelease = False

        def __lt__(self, other):
            if self.major != other.major:
                return self.major < other.major
            if self.minor != other.minor:
                return self.minor < other.minor
            if self.patch != other.patch:
                return self.patch < other.patch
            # If one is a pre-release and the other isn't, the pre-release is less
            if self.is_prerelease and not other.is_prerelease:
                return True
            if not self.is_prerelease and other.is_prerelease:
                return False
            # If both are pre-releases, compare lexicographically
            return self.version_str < other.version_str

        def __le__(self, other):
            return self < other or self.version_str == other.version_str

        def __gt__(self, other):
            return not (self <= other)

        def __ge__(self, other):
            return not (self < other)

        def __eq__(self, other):
            return self.version_str == other.version_str

        def __ne__(self, other):
            return not (self == other)

    def parse_version(version_str):
        return SimpleVersion(version_str)


class ChangelogManager:
    """
    Combined class for updating and validating changelogs.
    """

    def __init__(
        self,
        verbose: bool = True,
        check_modified_branch: Optional[str] = None,
        require_unreleased: bool = True,
        force: bool = False,
    ):
        self.verbose = verbose
        self.check_modified_branch = check_modified_branch
        self.require_unreleased = require_unreleased
        self.force = force

        # Standard sections in a Keep a Changelog file - with proper capitalization
        self.valid_sections = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

    def process_extensions(self, root_folder: str, changelog_message: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Main function to process all extensions in a directory.

        Args:
            root_folder: Root directory to search for extensions
            changelog_message: Optional message to include in changelog updates

        Returns:
            Dict with extension names as keys and lists of errors/warnings as values
        """
        results = {}

        for dirpath, dirnames, filenames in os.walk(root_folder):
            # Prune non-extension directories early
            if "config" not in dirnames or "docs" not in dirnames:
                continue

            dirnames[:] = []  # Prevent descending into subdirectories
            extension_name = os.path.basename(dirpath)

            if self.verbose:
                print(f"\n📦 Processing extension: {extension_name}")
            else:
                print(f"Processing: {extension_name}")

            # Initialize results entry
            results[extension_name] = []
            version_info = None

            try:
                # Pre-check conditions
                should_process, error_message = self._should_process_extension(dirpath, extension_name)
                if not should_process:
                    if error_message:
                        results[extension_name].append(error_message)
                        print(f"  ⏭️  Skipped {extension_name}: {error_message}")
                    else:
                        results[extension_name].append("Skipped due to filter conditions")
                        print(f"  ⏭️  Skipped {extension_name} due to filter conditions")
                    continue

                # Path validation
                config_path = os.path.join(dirpath, "config")
                docs_path = os.path.join(dirpath, "docs")
                toml_path = os.path.join(config_path, "extension.toml")
                changelog_path = os.path.join(docs_path, "CHANGELOG.md")

                # Store relative paths for error reporting
                rel_toml_path = os.path.relpath(toml_path, root_folder)
                rel_changelog_path = os.path.relpath(changelog_path, root_folder)

                if not self._validate_paths(toml_path, changelog_path, rel_toml_path, rel_changelog_path):
                    # Error messages already added by _validate_paths
                    continue

                # Core processing
                # 1. First validate the changelog
                validator = ChangelogValidator(
                    changelog_path,
                    extension_toml_path=toml_path,
                    rel_changelog_path=rel_changelog_path,
                    rel_extension_toml_path=rel_toml_path,
                    require_unreleased=self.require_unreleased,
                    valid_sections=self.valid_sections,
                    verbose=self.verbose,
                )

                validator.validate()

                # Add any validation errors to results
                if validator.errors:
                    results[extension_name].extend(validator.errors)

                # 2. Update the version and changelog (if requested)
                if changelog_message is not None:
                    version_result = self._update_extension_version(toml_path, rel_toml_path)
                    if version_result:
                        old_version, new_version = version_result
                        version_info = (old_version, new_version)
                        updated_lines = self._update_changelog_file(
                            changelog_path, rel_changelog_path, new_version, changelog_message
                        )
                        if updated_lines:
                            validator.lines = updated_lines
                    else:
                        results[extension_name].append(f"Failed to update version in {rel_toml_path}")

                # 3. Format the changelog
                validator.format_and_save()

                if not results[extension_name]:
                    if self.verbose:
                        version_display = f" ({version_info[0]} → {version_info[1]})" if version_info else ""
                        print(f"  ✅ Extension {extension_name} processed successfully{version_display}")
                    else:
                        version_display = f" ({version_info[0]} → {version_info[1]})" if version_info else ""
                        print(f"  ✅ Processed {extension_name} successfully{version_display}")
                    results[extension_name] = version_info if version_info else []

            except Exception as e:
                error_msg = f"Error processing extension: {str(e)}"
                results[extension_name].append(error_msg)
                if self.verbose:
                    print(f"  🚨 {error_msg}")
                else:
                    print(f"  ❌ {extension_name}: {error_msg}")

        return results

    def _should_process_extension(self, dirpath: str, extension_name: str = None) -> tuple:
        """Check all conditional requirements for processing"""
        if self.check_modified_branch:
            git_status, git_message = self._has_git_changes(dirpath, extension_name)
            if not git_status:
                if git_message and "behind" in git_message:
                    return False, git_message
                return False, f"No uncommitted changes vs {self.check_modified_branch} branch"
        return True, None

    def _has_git_changes(self, dirpath: str, extension_name: str = None) -> tuple:
        """Check if directory has changes against the specified branch."""
        branch = self.check_modified_branch
        try:
            # Parse branch to determine if we need to fetch and check for remote updates
            # Format can be "origin/develop", "develop", or any other branch reference
            if "/" in branch:
                remote, remote_branch = branch.split("/", 1)
                # Fetch the remote branch
                subprocess.run(["git", "fetch", remote, remote_branch], capture_output=True, text=True)

                # Check if we have a local tracking branch that's behind (skip if --force)
                if not self.force:
                    local_branch = remote_branch
                    status_cmd = subprocess.run(
                        ["git", "rev-list", "--count", f"{local_branch}..{branch}"], capture_output=True, text=True
                    )

                    behind_count = status_cmd.stdout.strip()
                    if behind_count and behind_count.isdigit() and int(behind_count) > 0:
                        error_msg = (
                            f"Local {local_branch} branch is {behind_count} commits behind {branch}. "
                            f"Please pull latest changes or use --force to skip this check."
                        )
                        if self.verbose:
                            print(f"  ❌ {error_msg}")
                        return False, error_msg

            # Check for changes against the specified branch
            result = subprocess.run(["git", "diff", "--quiet", branch, "--", dirpath], capture_output=True, text=True)
            if result.returncode == 0:
                if self.verbose:
                    print(f"  ⏭️  No uncommitted changes vs {branch} branch")
                return False, None
            return True, None
        except Exception as e:
            error_msg = f"Git check failed: {str(e)}"
            if self.verbose:
                print(f"  ❌ {error_msg}")
            return False, error_msg

    def _validate_paths(self, toml_path: str, changelog_path: str, rel_toml_path: str, rel_changelog_path: str) -> bool:
        """Validate required files exist"""
        if not os.path.exists(toml_path):
            if self.verbose:
                print(f"  ❌ Missing extension.toml at {toml_path}")
            return False
        if not os.path.exists(changelog_path):
            if self.verbose:
                print(f"  ❌ Missing CHANGELOG.md at {changelog_path}")
            return False
        return True

    def _update_extension_version(self, toml_path: str, rel_toml_path: str) -> Optional[Tuple[str, str]]:
        """Update version in extension.toml and return old and new versions"""
        try:
            # First read the file to get the current version
            with open(toml_path, "r") as f:
                content = f.read()

            # Load TOML data to extract the current version
            with open(toml_path, "rb") as f:
                data = toml_reader.load(f)

            package = data.get("package", {})
            version_str = package.get("version", "")

            if not version_str:
                if self.verbose:
                    print(f"  ❌ Missing 'package.version' in {rel_toml_path}")
                return None

            try:
                parts = list(map(int, version_str.split(".")))
                if len(parts) != 3:
                    raise ValueError
            except ValueError:
                if self.verbose:
                    print(f"  ❌ Invalid version format '{version_str}' in {rel_toml_path}, expected X.Y.Z")
                return None

            old_version = version_str
            parts[-1] += 1  # Increment patch version
            new_version = ".".join(map(str, parts))

            # Update only the version line directly in the file content
            # Look for the version pattern in package section
            version_pattern = re.compile(r'(version\s*=\s*")([^"]+)(")')

            # Find the pattern within the file content
            match = version_pattern.search(content)
            if not match:
                if self.verbose:
                    print(f"  ❌ Could not find version pattern in {rel_toml_path}")
                return None

            # Replace only the version part
            updated_content = content[: match.start(2)] + new_version + content[match.end(2) :]

            # Write the updated content back
            with open(toml_path, "w") as f:
                f.write(updated_content)

            if self.verbose:
                print(f"  ✅ Version updated in {rel_toml_path}: {version_str} → {new_version}")
            return (old_version, new_version)

        except Exception as e:
            if self.verbose:
                print(f"  ❌ Failed to update version in {rel_toml_path}: {str(e)}")
            return None

    def _update_changelog_file(
        self, changelog_path: str, rel_changelog_path: str, new_version: str, changelog_message: str
    ) -> List[str]:
        """Add new entry to changelog"""
        try:
            with open(changelog_path, "r") as f:
                content = f.read()

            changelog_header = "# Changelog"
            if changelog_header not in content:
                if self.verbose:
                    print(f"  ❌ Changelog header not found in {rel_changelog_path}")
                return

            today = datetime.date.today().strftime("%Y-%m-%d")
            default_message = "Update extension description and add extension specific test settings"
            message = changelog_message or default_message

            new_entry = f"\n## [{new_version}] - {today}\n" "### Changed\n" f"- {message}\n"

            updated_content = content.replace(changelog_header, f"{changelog_header}{new_entry}", 1)

            with open(changelog_path, "w") as f:
                f.write(updated_content)

            if self.verbose:
                print(f"  ✅ Changelog updated in {rel_changelog_path} with version {new_version}")

            return updated_content.split("\n")

        except Exception as e:
            if self.verbose:
                print(f"  ❌ Failed to update changelog in {rel_changelog_path}: {str(e)}")

        return None


class ChangelogValidator:
    """Validator for changelog files."""

    def __init__(
        self,
        file_path: str,
        extension_toml_path: str,
        rel_changelog_path: str,
        rel_extension_toml_path: str,
        require_unreleased: bool = True,
        valid_sections: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        self.file_path = file_path
        self.extension_toml_path = extension_toml_path
        self.rel_changelog_path = rel_changelog_path
        self.rel_extension_toml_path = rel_extension_toml_path
        self.lines = []
        self.errors = []
        self.require_unreleased = require_unreleased
        self.valid_sections = valid_sections or ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
        self.verbose = verbose

    def read_file(self) -> bool:
        """Read the changelog file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
            return True
        except Exception as e:
            self.errors.append(f"Error reading file {self.rel_changelog_path}: {e}")
            return False

    def validate(self) -> bool:
        """Run all validation checks."""
        if not self.read_file():
            return False

        # First run all validation checks
        self.validate_header()
        self.validate_line_format()
        self.validate_versions_and_dates()
        self.validate_sections()
        self.validate_bullet_points()

        # Always validate extension version when extension_toml_path is provided
        if self.extension_toml_path:
            self.validate_extension_version()

        return len(self.errors) == 0

    def validate_header(self) -> None:
        """Validate the changelog header."""
        if not self.lines:
            self.errors.append(f"File {self.rel_changelog_path} is empty")
            return

        if not self.lines[0].strip().startswith("# Changelog"):
            self.errors.append(f"File {self.rel_changelog_path} should start with '# Changelog'")

    def extract_versions_and_dates(self) -> List[Tuple[str, Optional[datetime.date], int]]:
        """Extract version numbers, dates, and line numbers from the changelog."""
        versions_and_dates = []
        # This pattern now captures any separator character between the version and date
        version_pattern = re.compile(r"## \[([^\]]+)\](?:[ ]([^\w\s])[ ](\d{4}-\d{2}-\d{2}))?")
        # Pattern to detect malformed dates (e.g., 2023-12-1 instead of 2023-12-01)
        malformed_date_pattern = re.compile(r"## \[([^\]]+)\][ ][-][ ](.+)")

        for line_num, line in enumerate(self.lines, 1):
            match = version_pattern.match(line.strip())
            if match:
                version_str = match.group(1)
                separator = match.group(2)  # Will be None if there's no date
                date_str = match.group(3)  # Will be None if there's no date

                # Check for invalid separator
                if separator and separator != "-":
                    self.errors.append(
                        f"Line {line_num}: Invalid separator '{separator}': '{line.strip()}'. "
                        f"Use a hyphen (-) between version and date."
                    )

                date_obj = None
                if date_str:
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        self.errors.append(f"Line {line_num}: Invalid date format: {date_str}. Use YYYY-MM-DD.")
                else:
                    # Check if there's a malformed date (something after the version that didn't match)
                    malformed_match = malformed_date_pattern.match(line.strip())
                    if malformed_match and malformed_match.group(1) == version_str:
                        malformed_date_text = malformed_match.group(2).strip()
                        # Only flag as malformed if it's not "Unreleased"
                        if version_str.lower() != "unreleased" and malformed_date_text:
                            self.errors.append(
                                f"Line {line_num}: Invalid date format for version [{version_str}]: '{malformed_date_text}'. "
                                f"Use YYYY-MM-DD format with zero-padded months and days (e.g., 2023-12-01, not 2023-12-1)."
                            )

                versions_and_dates.append((version_str, date_obj, line_num))

        return versions_and_dates

    def validate_versions_and_dates(self) -> None:
        """Validate that version numbers and dates are monotonically increasing."""
        versions_and_dates = self.extract_versions_and_dates()

        if not versions_and_dates:
            self.errors.append(f"No version entries found")
            return

        # Check if first entry is "Unreleased" (if required)
        if self.require_unreleased and versions_and_dates[0][0].lower() != "unreleased":
            line_num = versions_and_dates[0][2]
            self.errors.append(f"Line {line_num}: First version entry should be [Unreleased]")

        # Skip "Unreleased" when checking version order
        actual_versions = [(v, d, ln) for v, d, ln in versions_and_dates if v.lower() != "unreleased"]

        # Check that all released versions have dates
        # Note: malformed dates are already caught in extract_versions_and_dates()
        # so we only report "missing date" for truly missing dates (no date text at all)
        for ver_str, date_obj, line_num in actual_versions:
            if date_obj is None:
                # Check if this was already reported as a malformed date
                already_reported = any(f"Invalid date format for version [{ver_str}]" in err for err in self.errors)
                if not already_reported:
                    self.errors.append(
                        f"Line {line_num}: Version [{ver_str}] is missing a date. "
                        f"Released versions must have a date in format: ## [{ver_str}] - YYYY-MM-DD"
                    )

        # Check version order
        for i in range(len(actual_versions) - 1):
            current_ver_str, current_date, current_line_num = actual_versions[i]
            next_ver_str, next_date, next_line_num = actual_versions[i + 1]

            try:
                current_ver = parse_version(current_ver_str)
                next_ver = parse_version(next_ver_str)

                if current_ver <= next_ver:
                    self.errors.append(
                        f"Line {current_line_num}: Version {current_ver_str} should be greater than {next_ver_str} "
                        f"(line {next_line_num}) - versions should be in descending order"
                    )
            except Exception as e:
                self.errors.append(
                    f"Lines {current_line_num}/{next_line_num}: Invalid version format: {current_ver_str} or {next_ver_str}. Error: {e}"
                )

            # Check date order if both dates exist
            if current_date and next_date and current_date < next_date:
                self.errors.append(
                    f"Line {current_line_num}: Date {current_date} for version {current_ver_str} should not be before "
                    f"{next_date} for version {next_ver_str} (line {next_line_num})"
                )

    def validate_sections(self) -> None:
        """Validate that all sections are properly formatted."""
        section_pattern = re.compile(r"^### (.+)$")

        for i, line in enumerate(self.lines):
            match = section_pattern.match(line.strip())
            if match:
                section_name = match.group(1)

                # Check if section name is valid (case-sensitive)
                if section_name not in self.valid_sections:
                    # Check if it's just a case issue
                    if section_name.lower() in [s.lower() for s in self.valid_sections]:
                        self.errors.append(
                            f"Line {i+1}: Section '{section_name}' has incorrect capitalization. "
                            f"Should be one of: {', '.join(self.valid_sections)}"
                        )
                    else:
                        self.errors.append(
                            f"Line {i+1}: Invalid section '{section_name}'. "
                            f"Should be one of: {', '.join(self.valid_sections)}"
                        )

    def validate_line_format(self) -> None:
        """Validate that all lines follow proper format (strict line pattern checking)."""
        # Allowed line start patterns based on Keep a Changelog format
        allowed_patterns = ("# Changelog", "## [", "### ", "-", "The format is based on")

        for line_num, line in enumerate(self.lines, 1):
            # Skip empty lines
            if not line.strip():
                continue

            # Check for bullet points with indentation (nested lists)
            # Allow any amount of leading whitespace followed by a dash
            stripped_line = line.lstrip()
            if stripped_line.startswith("-") and line[0] in (" ", "\t"):
                # This is a nested bullet point (indented dash), which is valid
                continue

            # Check if line starts with allowed patterns
            if not line.startswith(allowed_patterns):
                line_preview = line.rstrip()[:50] + "..." if len(line.rstrip()) > 50 else line.rstrip()
                self.errors.append(
                    f"Line {line_num}: Incorrect format. "
                    f"Lines should start with: '# Changelog', '## [', '### ', '-', or nested bullet points. "
                    f"Got: '{line_preview}'"
                )

    def validate_bullet_points(self) -> None:
        """Validate that all entries are bullet points."""
        in_version = False
        in_section = False

        # Use a more generic version pattern to match both correct and incorrect formats
        version_pattern = re.compile(r"## \[([^\]]+)\]")
        section_pattern = re.compile(r"### (\w+)")

        for line_num, line in enumerate(self.lines, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for version header
            if version_pattern.match(line):
                in_version = True
                in_section = False
                continue

            # Check for section header
            if section_pattern.match(line):
                in_section = True
                continue

            # Check bullet points in sections
            if in_version and in_section:
                # Skip lines that are not entries (e.g., additional description)
                if line.startswith("#") or line.startswith("```"):
                    continue

                # Check if line starts with a bullet point
                if not line.startswith("-") and not line.startswith("*"):
                    self.errors.append(f"Line {line_num} should start with a bullet point (- or *)")

    def validate_extension_version(self) -> None:
        """Validate that the latest version in the changelog matches the version in extension.toml."""
        # Get the latest version from the changelog (excluding "Unreleased")
        versions = self.extract_versions_and_dates()
        actual_versions = [(v, d, ln) for v, d, ln in versions if v.lower() != "unreleased"]

        if not actual_versions:
            self.errors.append(f"No actual version entries found")
            return

        latest_version_str, _, latest_line_num = actual_versions[0]

        # Check if extension.toml exists
        if not self.extension_toml_path or not os.path.exists(self.extension_toml_path):
            self.errors.append(f"extension.toml not found at {self.rel_extension_toml_path}")
            return

        # Read the extension.toml file
        try:
            with open(self.extension_toml_path, "rb") as f:
                extension_data = toml_reader.load(f)

            # Check for version in the package section
            if "package" not in extension_data:
                self.errors.append(f"No [package] section found in {self.rel_extension_toml_path}")
                return

            if "version" not in extension_data["package"]:
                self.errors.append(f"No version field found in [package] section of {self.rel_extension_toml_path}")
                return

            toml_version = extension_data["package"]["version"]

            # Compare versions
            if toml_version != latest_version_str:
                self.errors.append(
                    f"Line {latest_line_num}: Version mismatch: {latest_version_str} in CHANGELOG.md doesn't match "
                    f"{toml_version} in extension.toml"
                )

        except Exception as e:
            self.errors.append(f"Error reading {self.rel_extension_toml_path}: {e}")

    def format_changelog(self) -> List[str]:
        """Format the changelog file correctly, removing extra empty lines and capitalizing bullet points."""
        if not self.lines:
            return []

        formatted_lines = []
        in_version_section = False
        in_subsection = False
        empty_line_count = 0
        last_line_was_version = False

        version_pattern = re.compile(r"## \[([^\]]+)\]")
        section_pattern = re.compile(r"### (\w+)")

        for line in self.lines:
            line = line.rstrip()

            # Check if this is a version header
            if version_pattern.match(line):
                # Add one blank line before a new version section (except for the first one)
                if in_version_section and formatted_lines:
                    # Ensure exactly one blank line before new version
                    if formatted_lines[-1] != "":
                        formatted_lines.append("")

                in_version_section = True
                in_subsection = False
                empty_line_count = 0
                last_line_was_version = True
                formatted_lines.append(line)
                continue

            # Check if this is a section header
            if section_pattern.match(line) and in_version_section:
                # If this is the first section after a version header, don't add a blank line
                if in_subsection and not last_line_was_version and formatted_lines[-1] != "":
                    formatted_lines.append("")

                in_subsection = True
                empty_line_count = 0
                last_line_was_version = False
                formatted_lines.append(line)
                continue

            # Handle empty lines
            if not line.strip():
                # Skip empty lines right after a version header
                if last_line_was_version:
                    continue

                empty_line_count += 1
                # Only add one empty line, skip others
                if empty_line_count <= 1:
                    formatted_lines.append("")
                continue

            # Reset empty line counter for non-empty lines
            empty_line_count = 0
            last_line_was_version = False

            # Capitalize first character of bullet points
            line = self._capitalize_bullet_point(line)

            formatted_lines.append(line)

        # Ensure file ends with a newline
        if formatted_lines and formatted_lines[-1] != "":
            formatted_lines.append("")

        return formatted_lines

    def _capitalize_bullet_point(self, line: str) -> str:
        """Capitalize the first character of a bullet point entry.

        Skips capitalization for code references (backticks), function names,
        variable names, and other technical terms that should remain lowercase.

        Args:
            line: The line to process.

        Returns:
            The line with the first character of the bullet point content capitalized,
            unless it appears to be code or a technical reference.
        """
        # Match bullet points (with optional leading whitespace for nested items)
        # Pattern: optional whitespace, dash, space, then content
        bullet_pattern = re.compile(r"^(\s*-\s+)(.*)$")
        match = bullet_pattern.match(line)

        if match:
            prefix = match.group(1)  # "- " or "  - " etc.
            content = match.group(2)

            if content and self._should_capitalize(content):
                return prefix + content[0].upper() + content[1:]

        return line

    def _should_capitalize(self, content: str) -> bool:
        """Determine if content should have its first character capitalized.

        Args:
            content: The content to check.

        Returns:
            True if the content should be capitalized, False otherwise.
        """
        if not content:
            return False

        first_char = content[0]

        # Skip if not a lowercase letter (already capitalized, digit, backtick, etc.)
        if not first_char.islower():
            return False

        # Get the first word to check if it looks like code
        # Include special characters to catch patterns like "semantics:add_labels" or "opencv-python==4.9.0"
        first_word_match = re.match(r"^([a-zA-Z0-9_.\[\]():=<>!-]+)", content)
        if first_word_match:
            first_word = first_word_match.group(1)

            # Skip if first word contains code-like patterns:
            # - underscores (snake_case variables/functions)
            # - parentheses (function calls)
            # - dots (module.function or object.method)
            # - square brackets (array access)
            # - colons (namespace:function patterns)
            # - equals/comparison operators (version specs like ==4.9.0, >=1.0)
            # - hyphens in the middle (package names like opencv-python)
            if re.search(r"[_().\[\]:=<>!]", first_word):
                return False

            # Skip if contains hyphen not at the start (package names like opencv-python-headless)
            if "-" in first_word[1:]:
                return False

            # Skip camelCase words (lowercase start, has uppercase later)
            if re.search(r"^[a-z]+[A-Z]", first_word):
                return False

        return True

    def format_and_save(self) -> bool:
        """Format the changelog file and save it."""
        # First fix any incorrect version formats
        self.fix_version_format()

        # Then format the file
        formatted_lines = self.format_changelog()

        if not formatted_lines:
            return False

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(formatted_lines))
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error writing to file {self.rel_changelog_path}: {e}")
            return False

    def fix_version_format(self) -> None:
        """Fix incorrect version format in changelog lines, such as replacing '=' with '-'."""
        # This pattern captures any separator character between the version and date
        version_pattern = re.compile(r"(## \[([^\]]+)\])[ ]([^\w\s])[ ](\d{4}-\d{2}-\d{2})")

        for i, line in enumerate(self.lines):
            match = version_pattern.match(line.strip())
            if match and match.group(3) != "-":
                # Replace the incorrect separator with a hyphen
                version_header = match.group(1)
                date = match.group(4)
                corrected_line = f"{version_header} - {date}"

                if self.verbose:
                    print(f"  ✅ Fixed version format in line {i+1}: '{line.strip()}' -> '{corrected_line}'")

                # Update the line in the list
                self.lines[i] = corrected_line + "\n" if line.endswith("\n") else corrected_line


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> callable:
    """Setup function for the repo tool."""
    # Get default values from config
    tool_config = config.get("repo_update_changelogs", {})

    # Mode options
    parser.add_argument(
        "--validate",
        action="store_true",
        default=tool_config.get("validate", False),
        help="Validate changelogs without updating versions",
    )
    parser.add_argument(
        "--format",
        action="store_true",
        default=tool_config.get("format", False),
        help="Format changelog files (fix spacing, etc.)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        default=tool_config.get("update", False),
        help="Update versions and changelogs (default if no mode specified)",
    )

    # Update options
    parser.add_argument(
        "--message",
        "-m",
        help="Custom changelog message (default: Update extension description and add extension specific test settings)",
    )
    parser.add_argument(
        "--check-modified",
        nargs="?",
        const="origin/develop",
        default=tool_config.get("check_modified", None),
        metavar="BRANCH",
        help="Only update extensions with changes vs specified branch (default: origin/develop)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        default=tool_config.get("force", False),
        help="Force update even if local branch is behind the specified branch",
    )

    # Validation options
    parser.add_argument(
        "--check-unreleased",
        action="store_true",
        default=tool_config.get("check_unreleased", False),
        help="Check if changelog has an Unreleased section",
    )

    # Output options
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=tool_config.get("verbose", False), help="Enable verbose output"
    )

    # Directory options
    extensions_dirs_default = tool_config.get("extensions_dir", ["source/extensions"])
    # If extensions_dir is a string, convert it to a list
    if isinstance(extensions_dirs_default, str):
        extensions_dirs_default = [extensions_dirs_default]

    parser.add_argument(
        "--extensions-dir",
        action="append",
        default=None,
        help=f"Directory containing extensions (can be specified multiple times, default: {extensions_dirs_default})",
    )

    # Store default for later use in run_repo_tool
    parser.set_defaults(extensions_dir_default=extensions_dirs_default)

    # Return function to run
    return run_repo_tool


def run_repo_tool(args: argparse.Namespace, config: Dict[str, Any]) -> int:
    """Run the changelog update and validation tool in repo mode."""
    # Default to update mode if no mode specified (this should have been handled in __main__ already,
    # but we add it here as a fallback)
    if not (args.validate or args.format or args.update):
        print("No mode specified, defaulting to update mode")
        args.update = True

    # Apply default extensions_dir if none specified (avoids argparse append-to-default bug)
    if args.extensions_dir is None:
        args.extensions_dir = getattr(args, "extensions_dir_default", ["source/extensions"])

    # Create changelog manager
    manager = ChangelogManager(
        verbose=args.verbose,
        check_modified_branch=args.check_modified,
        require_unreleased=args.check_unreleased,
        force=args.force,
    )

    # Process each extensions directory
    error_count = 0
    success_count = 0
    all_results = {}

    for extensions_dir in args.extensions_dir:
        # Get the full path to extensions directory
        full_extensions_dir = os.path.join(config.get("root", "."), extensions_dir)

        if args.verbose:
            print(f"\n💼 Processing extensions in: {full_extensions_dir}")

        # Process extensions based on mode
        if args.update:
            # Update mode - process with message
            results = manager.process_extensions(full_extensions_dir, args.message)
        elif args.message:
            # If a message is provided, force update even in other modes
            print(f"Message provided with -m, forcing update mode")
            args.update = True
            results = manager.process_extensions(full_extensions_dir, args.message)
        else:
            # For validation or formatting only, pass None as changelog_message
            results = manager.process_extensions(full_extensions_dir, None)

        # Add to combined results
        all_results.update(results)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # First show all successful extensions
    successful_extensions = []
    extensions_with_errors = []

    for ext_name, errors in all_results.items():
        if not errors or not isinstance(errors, list) or not errors:
            success_count += 1
            version_info = errors if isinstance(errors, tuple) and len(errors) == 2 else None
            successful_extensions.append((ext_name, version_info))
        else:
            extensions_with_errors.append((ext_name, errors))
            error_count += len(errors)

    # Display successful extensions first
    for ext_name, version_info in successful_extensions:
        version_display = f" ({version_info[0]} → {version_info[1]})" if version_info else ""
        print(f"✅ Extension '{ext_name}' processed successfully{version_display}")

    # Then display extensions with errors
    if extensions_with_errors:
        print("\nExtensions with issues:")
        for ext_name, errors in extensions_with_errors:
            # Show changelog path once per extension
            changelog_path = f"{ext_name}/docs/CHANGELOG.md"
            print(
                f"❌ Extension '{ext_name}' ({changelog_path}) had {len(errors)} issue{'s' if len(errors) != 1 else ''}:"
            )
            for error in errors:
                print(f"  - {error}")

    total_count = len(all_results)
    failed_count = total_count - success_count
    print(f"\nProcessed {total_count} extensions: {success_count} successful, {failed_count} with issues")

    if error_count > 0:
        print(f"Found {error_count} total issues")
        return 1
    else:
        print("All operations completed successfully!")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update and validate changelogs across extensions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Setup repo tool will add all the arguments
    run_tool = setup_repo_tool(parser, {"root": os.getcwd()})

    # Parse arguments and run the tool
    args = parser.parse_args()

    # Default to update mode if no mode specified
    if not (args.validate or args.format or args.update):
        print("No mode specified, defaulting to update mode")
        args.update = True

    sys.exit(run_tool(args, {"root": os.getcwd()}))
