#!/usr/bin/env python3
"""
Script to update and validate changelogs across extensions.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Try to import required packages with fallbacks
try:
    import tomli as toml_reader
except ImportError:
    try:
        import tomlkit as toml_reader
    except ImportError:
        print("Warning: Neither tomli nor tomlkit installed. Using built-in fallback for TOML parsing.")
        # Simple fallback for basic TOML parsing
        import json

        def parse_toml(toml_str):
            """Very simple TOML parser for basic needs"""
            result = {}
            current_section = result
            section_stack = []

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

        class TomliWrapper:
            @staticmethod
            def load(file_obj):
                return parse_toml(file_obj.read())

        toml_reader = TomliWrapper()

# Try to import tomlkit for writing TOML
try:
    import tomlkit as toml_writer
except ImportError:
    print("Warning: tomlkit not installed. Using fallback for TOML writing.")

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
        check_cpp: bool = False,
        check_modified: bool = False,
        require_unreleased: bool = True,
        require_references: bool = True,
    ):
        self.verbose = verbose
        self.check_cpp = check_cpp
        self.check_modified = check_modified
        self.require_unreleased = require_unreleased
        self.require_references = require_references

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

            # Initialize results entry
            results[extension_name] = []

            try:
                # Pre-check conditions
                if not self._should_process_extension(dirpath):
                    results[extension_name].append("Skipped due to filter conditions")
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
                    require_references=self.require_references,
                    valid_sections=self.valid_sections,
                    verbose=self.verbose,
                )

                validator.validate()

                # Add any validation errors to results
                if validator.errors:
                    results[extension_name].extend(validator.errors)

                # 2. Update the version and changelog (if requested)
                if changelog_message is not None:
                    new_version = self._update_extension_version(toml_path, rel_toml_path)
                    if new_version:
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
                        print(f"  ✅ Extension {extension_name} processed successfully")

            except Exception as e:
                error_msg = f"Error processing extension: {str(e)}"
                results[extension_name].append(error_msg)
                if self.verbose:
                    print(f"  🚨 {error_msg}")

        return results

    def _should_process_extension(self, dirpath: str) -> bool:
        """Check all conditional requirements for processing"""
        if self.check_modified and not self._has_git_changes(dirpath):
            return False
        if self.check_cpp and not self._has_cpp_files(dirpath):
            return False
        return True

    def _has_git_changes(self, dirpath: str) -> bool:
        """Check if directory has changes against develop branch"""
        try:
            # First check if develop branch is behind remote
            status_cmd = subprocess.run(["git", "fetch", "origin", "develop"], capture_output=True, text=True)

            # Check if local develop is behind remote
            status_cmd = subprocess.run(
                ["git", "rev-list", "--count", "develop..origin/develop"], capture_output=True, text=True
            )

            behind_count = status_cmd.stdout.strip()
            if behind_count and int(behind_count) > 0:
                error_msg = (
                    f"Local develop branch is {behind_count} commits behind origin/develop. Please pull latest changes."
                )
                if self.verbose:
                    print(f"  ❌ {error_msg}")
                raise Exception(error_msg)

            # Continue with original functionality to check for changes
            result = subprocess.run(
                ["git", "diff", "--quiet", "develop", "--", dirpath], capture_output=True, text=True
            )
            if result.returncode == 0:
                if self.verbose:
                    print(f"  ⏭️  No uncommitted changes vs develop branch")
                return False
            return True
        except Exception as e:
            if self.verbose:
                print(f"  ❌ Git check failed: {str(e)}")
            return False

    def _has_cpp_files(self, dirpath: str) -> bool:
        """Check for C++ source files in directory tree"""
        for root, _, files in os.walk(dirpath):
            for file in files:
                if file.endswith((".cpp", ".hpp", ".h", ".cxx")):
                    return True
        if self.verbose:
            print(f"  ⏭️  No C++ files found in extension")
        return False

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

    def _update_extension_version(self, toml_path: str, rel_toml_path: str) -> Optional[str]:
        """Update version in extension.toml and return new version"""
        try:
            with open(toml_path, "r") as f:
                data = toml_writer.load(f)

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

            parts[-1] += 1  # Increment patch version
            new_version = ".".join(map(str, parts))
            data["package"]["version"] = new_version

            with open(toml_path, "w") as f:
                toml_writer.dump(data, f)

            if self.verbose:
                print(f"  ✅ Version updated in {rel_toml_path}: {version_str} → {new_version}")
            return new_version

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
        extension_toml_path: Optional[str] = None,
        rel_changelog_path: Optional[str] = None,
        rel_extension_toml_path: Optional[str] = None,
        require_unreleased: bool = True,
        require_references: bool = True,
        valid_sections: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        self.file_path = file_path
        self.extension_toml_path = extension_toml_path
        self.rel_changelog_path = rel_changelog_path or file_path
        self.rel_extension_toml_path = rel_extension_toml_path or extension_toml_path
        self.lines = []
        self.errors = []
        self.require_unreleased = require_unreleased
        self.require_references = require_references
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

        self.validate_header()
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

        # Only check for references if required
        if self.require_references:
            # Check for Keep a Changelog reference
            found_format_reference = False
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if "keepachangelog.com" in line.lower():
                    found_format_reference = True
                    break

            if not found_format_reference:
                self.errors.append(f"Missing reference to Keep a Changelog format in {self.rel_changelog_path}")

            # Check for Semantic Versioning reference
            found_semver_reference = False
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if "semver" in line.lower() or "semantic versioning" in line.lower():
                    found_semver_reference = True
                    break

            if not found_semver_reference:
                self.errors.append(f"Missing reference to Semantic Versioning in {self.rel_changelog_path}")

    def extract_versions_and_dates(self) -> List[Tuple[str, Optional[datetime.date]]]:
        """Extract version numbers and dates from the changelog."""
        versions_and_dates = []
        version_pattern = re.compile(r"## \[([^\]]+)\](?: - (\d{4}-\d{2}-\d{2}))?")

        for line in self.lines:
            match = version_pattern.match(line.strip())
            if match:
                version_str = match.group(1)
                date_str = match.group(2)

                date_obj = None
                if date_str:
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        self.errors.append(
                            f"Invalid date format in {self.rel_changelog_path}: {date_str}. Use YYYY-MM-DD."
                        )

                versions_and_dates.append((version_str, date_obj))

        return versions_and_dates

    def validate_versions_and_dates(self) -> None:
        """Validate that version numbers and dates are monotonically increasing."""
        versions_and_dates = self.extract_versions_and_dates()

        if not versions_and_dates:
            self.errors.append(f"No version entries found in {self.rel_changelog_path}")
            return

        # Check if first entry is "Unreleased" (if required)
        if self.require_unreleased and versions_and_dates[0][0].lower() != "unreleased":
            self.errors.append(f"First version entry in {self.rel_changelog_path} should be [Unreleased]")

        # Skip "Unreleased" when checking version order
        actual_versions = [(v, d) for v, d in versions_and_dates if v.lower() != "unreleased"]

        # Check version order
        for i in range(len(actual_versions) - 1):
            current_ver_str, current_date = actual_versions[i]
            next_ver_str, next_date = actual_versions[i + 1]

            try:
                current_ver = parse_version(current_ver_str)
                next_ver = parse_version(next_ver_str)

                if current_ver <= next_ver:
                    self.errors.append(
                        f"Version {current_ver_str} should be greater than {next_ver_str} "
                        f"in {self.rel_changelog_path} (versions should be in descending order)"
                    )
            except Exception as e:
                self.errors.append(
                    f"Invalid version format in {self.rel_changelog_path}: {current_ver_str} or {next_ver_str}. Error: {e}"
                )

            # Check date order if both dates exist
            if current_date and next_date and current_date < next_date:
                self.errors.append(
                    f"Date {current_date} for version {current_ver_str} should not be before "
                    f"{next_date} for version {next_ver_str} in {self.rel_changelog_path}"
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
                            f"Line {i+1} in {self.rel_changelog_path}: Section '{section_name}' has incorrect capitalization. "
                            f"Should be one of: {', '.join(self.valid_sections)}"
                        )
                    else:
                        self.errors.append(
                            f"Line {i+1} in {self.rel_changelog_path}: Invalid section '{section_name}'. "
                            f"Should be one of: {', '.join(self.valid_sections)}"
                        )

    def validate_bullet_points(self) -> None:
        """Validate that all entries are bullet points."""
        in_version = False
        in_section = False

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
                    self.errors.append(
                        f"Line {line_num} in {self.rel_changelog_path} should start with a bullet point (- or *)"
                    )

    def validate_extension_version(self) -> None:
        """Validate that the latest version in the changelog matches the version in extension.toml."""
        # Get the latest version from the changelog (excluding "Unreleased")
        versions = self.extract_versions_and_dates()
        actual_versions = [(v, d) for v, d in versions if v.lower() != "unreleased"]

        if not actual_versions:
            self.errors.append(f"No actual version entries found in {self.rel_changelog_path}")
            return

        latest_version_str = actual_versions[0][0]

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
                    f"Version mismatch: {latest_version_str} in {self.rel_changelog_path} doesn't match "
                    f"{toml_version} in {self.rel_extension_toml_path}"
                )

        except Exception as e:
            self.errors.append(f"Error reading {self.rel_extension_toml_path}: {e}")

    def format_changelog(self) -> List[str]:
        """Format the changelog file correctly, removing extra empty lines."""
        if not self.lines:
            return []

        formatted_lines = []
        in_version_section = False
        in_subsection = False
        empty_line_count = 0
        last_line_was_version = False

        version_pattern = re.compile(r"## \[([^\]]+)\]")
        section_pattern = re.compile(r"### (\w+)")

        for i, line in enumerate(self.lines):
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
            formatted_lines.append(line)

        # Ensure file ends with a newline
        if formatted_lines and formatted_lines[-1] != "":
            formatted_lines.append("")

        return formatted_lines

    def format_and_save(self) -> bool:
        """Format the changelog file and save it."""
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


def main():
    """Main function to parse arguments and run the tool."""
    parser = argparse.ArgumentParser(
        description="Update and validate changelogs across extensions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Root directory
    parser.add_argument(
        "root", nargs="?", default=os.getcwd(), help="Root directory to process (default: current directory)"
    )

    # Mode options
    mode_group = parser.add_argument_group("Operation Mode")
    mode_group.add_argument("--validate", action="store_true", help="Validate changelogs without updating versions")
    mode_group.add_argument("--format", action="store_true", help="Format changelog files (fix spacing, etc.)")
    mode_group.add_argument(
        "--update", action="store_true", help="Update versions and changelogs (default if no mode specified)"
    )

    # Update options
    update_group = parser.add_argument_group("Update Options")
    update_group.add_argument(
        "--message",
        "-m",
        help="Custom changelog message (default: Update extension description and add extension specific test settings)",
    )
    update_group.add_argument("--check-cpp", action="store_true", help="Only update extensions with C++ source files")
    update_group.add_argument(
        "--check-modified", action="store_true", help="Only update extensions with changes vs develop branch"
    )

    # Validation options
    validation_group = parser.add_argument_group("Validation Options")
    validation_group.add_argument(
        "--check-unreleased", action="store_true", help="Check if changelog has an Unreleased section"
    )
    validation_group.add_argument(
        "--check-references", action="store_true", help="Check for Keep a Changelog and Semantic Versioning references"
    )
    validation_group.add_argument("--check-all", action="store_true", help="Enable all validation checks")

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument("--quiet", action="store_false", dest="verbose", help="Disable verbose output")

    # Directory options
    directory_group = parser.add_argument_group("Directory Options")
    directory_group.add_argument(
        "--extensions-dir",
        action="append",
        default=["source/extensions"],
        help="Directory containing extensions (can be specified multiple times)",
    )

    args = parser.parse_args()

    # Default to update mode if no mode specified
    if not (args.validate or args.format or args.update):
        args.update = True

    # Set validation options based on check-all
    if args.check_all:
        args.check_unreleased = True
        args.check_references = True

    # Create changelog manager
    manager = ChangelogManager(
        verbose=args.verbose,
        check_cpp=args.check_cpp,
        check_modified=args.check_modified,
        require_unreleased=args.check_unreleased,
        require_references=args.check_references,
    )

    # Process each extensions directory
    error_count = 0
    success_count = 0
    all_results = {}

    for extensions_dir in args.extensions_dir:
        # Get the full path to extensions directory
        full_extensions_dir = os.path.join(args.root, extensions_dir)

        if args.verbose:
            print(f"\n💼 Processing extensions in: {full_extensions_dir}")

        # Process extensions based on mode
        if args.update:
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

    for ext_name, errors in all_results.items():
        if errors:
            print(f"❌ Extension '{ext_name}' had {len(errors)} issues:")
            for error in errors:
                print(f"  - {error}")
            error_count += len(errors)
        else:
            success_count += 1
            if args.verbose:
                print(f"✅ Extension '{ext_name}' processed successfully")

    print(
        "\nProcessed {0} extensions: {1} successful, {2} with issues".format(
            len(all_results), success_count, len(all_results) - success_count
        )
    )

    if error_count > 0:
        print(f"Found {error_count} total issues")
        return 1
    else:
        print("All operations completed successfully!")
        return 0


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> callable:
    """Setup function for the repo tool."""
    # Get default values from config
    tool_config = config.get("repo_update_changelogs", {})

    # Mode options
    parser.add_argument(
        "--validate",
        action="store_true",
        default=not tool_config.get("update", False),
        help="Validate changelogs without updating versions",
    )
    parser.add_argument(
        "--format",
        action="store_true",
        default=tool_config.get("format", True),
        help="Format changelog files (fix spacing, etc.)",
    )
    parser.add_argument(
        "--update", action="store_true", default=tool_config.get("update", False), help="Update versions and changelogs"
    )

    # Update options
    parser.add_argument(
        "--message",
        "-m",
        help="Custom changelog message (default: Update extension description and add extension specific test settings)",
    )
    parser.add_argument(
        "--check-cpp",
        action="store_true",
        default=tool_config.get("check_cpp", False),
        help="Only update extensions with C++ source files",
    )
    parser.add_argument(
        "--check-modified",
        action="store_true",
        default=tool_config.get("check_modified", False),
        help="Only update extensions with changes vs develop branch",
    )

    # Validation options
    # --check-version is removed as it's always enabled
    parser.add_argument(
        "--check-unreleased",
        action="store_true",
        default=tool_config.get("check_unreleased", False),
        help="Check if changelog has an Unreleased section",
    )
    parser.add_argument(
        "--check-references",
        action="store_true",
        default=tool_config.get("check_references", False),
        help="Check for Keep a Changelog and Semantic Versioning references",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        default=tool_config.get("check_all", False),
        help="Enable all validation checks",
    )

    # Output options
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=tool_config.get("verbose", False), help="Enable verbose output"
    )
    parser.add_argument("--quiet", action="store_false", dest="verbose", help="Disable verbose output")

    # Directory options
    extensions_dirs = tool_config.get("extensions_dir", ["source/extensions"])
    # If extensions_dir is a string, convert it to a list
    if isinstance(extensions_dirs, str):
        extensions_dirs = [extensions_dirs]

    parser.add_argument(
        "--extensions-dir",
        action="append",
        default=extensions_dirs,
        help="Directory containing extensions (can be specified multiple times)",
    )

    # Return function to run
    return run_repo_tool


def run_repo_tool(args: argparse.Namespace, config: Dict[str, Any]) -> int:
    """Run the changelog update and validation tool in repo mode."""
    # Set the check_all fields if requested
    if args.check_all:
        args.check_unreleased = True
        args.check_references = True

    # Create changelog manager
    manager = ChangelogManager(
        verbose=args.verbose,
        check_cpp=args.check_cpp,
        check_modified=args.check_modified,
        require_unreleased=args.check_unreleased,
        require_references=args.check_references,
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

    for ext_name, errors in all_results.items():
        if errors:
            print(f"❌ Extension '{ext_name}' had {len(errors)} issues:")
            for error in errors:
                print(f"  - {error}")
            error_count += len(errors)
        else:
            success_count += 1
            if args.verbose:
                print(f"✅ Extension '{ext_name}' processed successfully")

    print(
        "\nProcessed {0} extensions: {1} successful, {2} with issues".format(
            len(all_results), success_count, len(all_results) - success_count
        )
    )

    if error_count > 0:
        print(f"Found {error_count} total issues")
        return 1
    else:
        print("All operations completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
