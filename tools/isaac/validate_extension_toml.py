#!/usr/bin/env python3
# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

"""
Validate extension.toml files to ensure they follow the specified structure and ordering rules.

This script checks:
1. Sections appear in the correct order as defined in the rules
2. Fields in the [package] section appear in the correct order
3. Settings entries have descriptive comments above them
4. Proper spacing between sections (one blank line)
5. Dependencies in the [dependencies] section are alphabetically sorted
6. Dependencies in the [[test]] section are alphabetically sorted
7. (Optional) Required field writeTarget.kit is present and set to true in the [package] section
   (only when --check-write-target is specified)

When run without arguments, it validates all extension.toml files in the repository
against all validation rules. It can also fix various issues automatically with the --fix option.
"""

import argparse
import difflib
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import toml


# Define color codes for terminal output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"


# Check if terminal supports colors
USE_COLORS = sys.stdout.isatty()

# Define the expected section order
SECTION_ORDER = [
    "core",
    "package",
    "deprecation",  # Deprecation information (if applicable)
    "dependencies",
    "python.module",
    "native.library",  # Native library paths
    "python.pipapi",  # Python package requirements for the extension
    "native.plugin",
    "settings",
    "trigger",
    "fswatcher.patterns",  # File system watcher patterns
    "fswatcher.paths",  # File system watcher path exclusions
    "test",
    "documentation",
]

# Define the expected order of fields in the [package] section
PACKAGE_FIELD_ORDER = [
    "version",
    "category",
    "title",
    "description",
    "authors",
    "repository",
    "keywords",
    "changelog",
    "readme",
    "preview_image",
    "icon",
    "writeTarget.kit",
    "writeTarget.platform",
    "feature",
    "deprecation",
]

# Define the expected order of fields in the [[test]] section
TEST_FIELD_ORDER = [
    "name",
    "timeout",
    "dependencies",
    "args",
    "stdoutFailPatterns.exclude",
    "stdoutFailPatterns.include",
]

# Define the expected fields in the [deprecation] section
DEPRECATION_FIELDS = ["warning"]


class ValidationError:
    """Class representing a validation error."""

    def __init__(self, file_path: str, error_type: str, message: str, line_number: Optional[int] = None):
        self.file_path = file_path
        self.error_type = error_type
        self.message = message
        self.line_number = line_number

    def __str__(self) -> str:
        location = f" at line {self.line_number}" if self.line_number is not None else ""
        return f"{self.file_path}{location}: {self.error_type}: {self.message}"


class ExtensionTomlValidator:
    """Validator for extension.toml files."""

    def __init__(self):
        self.errors = []
        self.fixes_applied = []
        self._verbose = False  # Add internal flag

    def _create_line_mapping(self, content: str) -> Dict[str, int]:
        """
        Create a mapping of section names to line numbers.

        Args:
            content: TOML content as string

        Returns:
            Dictionary mapping section names to line numbers
        """
        line_mapping = {}
        lines = content.split("\n")

        for i, line in enumerate(lines):
            is_header, section_name, _ = self._is_section_header(line)
            if is_header:
                # Regular section or array section
                if section_name not in line_mapping:
                    line_mapping[section_name] = i + 1

        return line_mapping

    def _is_section_header(self, line: str) -> Tuple[bool, str, str]:
        """
        Check if a line is a section header and return its type and name.

        Args:
            line: Line to check

        Returns:
            Tuple of (is_header, section_name, section_type)
            where section_type is 'regular' or 'array'
        """
        line_stripped = line.strip()
        if line_stripped.startswith("[") and line_stripped.endswith("]") and not line_stripped.startswith("[["):
            # Regular section like [core], [package], etc.
            return True, line_stripped[1:-1], "regular"
        elif line_stripped.startswith("[[") and line_stripped.endswith("]]"):
            # Array section like [[python.module]], [[test]], etc.
            return True, line_stripped[2:-2], "array"
        return False, "", ""

    def _has_blank_line_before(self, lines: List[str], index: int) -> bool:
        """
        Check if there's a blank line before the given index.

        Args:
            lines: List of lines
            index: Current line index

        Returns:
            True if there's a blank line before the index
        """
        for j in range(index - 1, max(0, index - 3), -1):
            if not lines[j].strip():
                return True
        return False

    def _fix_whitespace(self, content: str) -> str:
        """
        Fix whitespace between sections by ensuring each section is preceded by exactly one blank line.
        If there are more than one consecutive blank lines, reduce them to exactly one.
        Don't add blank lines between comments and the section headers they describe.
        Also removes any extra empty lines at the start or end of the file.
        Ensures lines with only whitespace characters are treated as empty lines.
        Standardizes line endings to \n.

        Args:
            content: The file content to fix

        Returns:
            Fixed content with proper blank lines between sections
        """
        # First normalize line endings to \n
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        lines = content.split("\n")
        fixed_lines = []
        reduced_excessive_whitespace = False
        removed_leading_trailing = False
        removed_whitespace_only_lines = False

        # Remove leading empty lines and lines with only whitespace
        start_idx = 0
        while start_idx < len(lines) and not lines[start_idx].strip():
            start_idx += 1
            removed_leading_trailing = True

        # Collect section information
        section_info = []
        for i, line in enumerate(lines):
            is_header, section_name, section_type = self._is_section_header(line)
            if is_header:
                section_info.append((i, section_name, section_type))

        # Process the content
        i = start_idx
        while i < len(lines):
            line = lines[i]
            # Standardize: replace lines with only whitespace characters with empty lines
            if line and not line.strip():
                line = ""
                removed_whitespace_only_lines = True

            is_header, section_name, section_type = self._is_section_header(line)

            # If this is a section header (not the first one)
            if is_header and i > start_idx:
                # Check if previous line is a comment (starts with #)
                prev_line_is_comment = False
                j = i - 1
                while j >= start_idx:
                    if lines[j].strip():  # Skip empty lines and lines with only whitespace
                        prev_line_is_comment = lines[j].strip().startswith("#")
                        break
                    j -= 1

                # If the previous non-empty line is not a comment, ensure proper spacing
                if not prev_line_is_comment:
                    # Count consecutive blank lines before this section
                    consecutive_blank_lines = 0
                    j = i - 1
                    while j >= start_idx and not lines[j].strip():
                        consecutive_blank_lines += 1
                        j -= 1

                    # Remove all consecutive blank lines from the buffer
                    while fixed_lines and not fixed_lines[-1].strip():
                        fixed_lines.pop()

                    # Now add exactly one blank line (regardless of whether it's a same array section or not)
                    if consecutive_blank_lines == 0:
                        # Add one blank line if none exists
                        fixed_lines.append("")
                    elif consecutive_blank_lines > 1:
                        # Reduce to exactly one blank line
                        fixed_lines.append("")
                        reduced_excessive_whitespace = True
                    else:
                        # Keep the existing blank line
                        fixed_lines.append("")

            fixed_lines.append(line)
            i += 1

        # Remove trailing empty lines and lines with only whitespace
        while fixed_lines and not fixed_lines[-1].strip():
            fixed_lines.pop()
            removed_leading_trailing = True

        # Add a message if we reduced excessive whitespace
        if reduced_excessive_whitespace:
            if "Added required blank lines between sections" in self.fixes_applied:
                # Update existing message
                idx = self.fixes_applied.index("Added required blank lines between sections")
                self.fixes_applied[idx] = (
                    "Fixed spacing between sections (added missing blank lines and reduced excessive blank lines)"
                )
            else:
                # Add new message
                self.fixes_applied.append("Reduced excessive blank lines between sections to exactly one")

        # Add a message if we removed leading/trailing empty lines
        if removed_leading_trailing:
            self.fixes_applied.append("Removed extra empty lines at start and/or end of file")

        # Add a message if we standardized whitespace-only lines
        if removed_whitespace_only_lines:
            self.fixes_applied.append("Standardized lines with only whitespace characters to empty lines")

        return "\n".join(fixed_lines)

    def _check_section_spacing(self, file_path: str, content: str) -> bool:
        """
        Check if sections are properly separated by blank lines.
        Ensures each section has exactly one blank line before it (not more or less),
        except when a section is preceded by a comment that describes it.
        Also checks for extra empty lines at the start or end of the file.

        Args:
            file_path: Path to the file being validated
            content: The file content to check

        Returns:
            True if spacing issues were found, False otherwise
        """
        lines = content.split("\n")
        has_spacing_issue = False

        # Check for leading empty lines
        leading_empty_lines = 0
        for line in lines:
            if not line.strip():
                leading_empty_lines += 1
            else:
                break

        if leading_empty_lines > 0:
            self.errors.append(
                ValidationError(
                    file_path,
                    "File Spacing",
                    f"Extra empty lines ({leading_empty_lines}) at the start of the file",
                    1,
                )
            )
            has_spacing_issue = True

        # Check for trailing empty lines
        trailing_empty_lines = 0
        for line in reversed(lines):
            if not line.strip():
                trailing_empty_lines += 1
            else:
                break

        if trailing_empty_lines > 0:
            self.errors.append(
                ValidationError(
                    file_path,
                    "File Spacing",
                    f"Extra empty lines ({trailing_empty_lines}) at the end of the file",
                    len(lines),
                )
            )
            has_spacing_issue = True

        # Check section spacing (blank lines before sections)
        section_line_numbers = []
        for i, line in enumerate(lines):
            is_header, section_name, section_type = self._is_section_header(line)
            if is_header:
                # Include the section type to properly handle array sections
                section_line_numbers.append((i, section_name, section_type))

        # Check for missing or excessive blank lines between sections
        for i in range(1, len(section_line_numbers)):
            current_line, section_name, section_type = section_line_numbers[i]
            prev_line, prev_section_name, prev_section_type = section_line_numbers[i - 1]

            # Skip checking if the current section and previous section are part of the same array section
            # This handles cases like multiple [[test]] sections
            if section_type == "array" and prev_section_type == "array" and section_name == prev_section_name:
                # Don't enforce blank line requirements between array items of the same type
                continue

            # Check if there's a comment directly before this section
            has_preceding_comment = False
            j = current_line - 1
            while j > prev_line:
                if lines[j].strip():  # Found non-empty line
                    has_preceding_comment = lines[j].strip().startswith("#")
                    break
                j -= 1

            # If there's a comment directly before this section, no blank line is required
            if has_preceding_comment:
                continue

            # Count consecutive blank lines before current section
            consecutive_blank_lines = 0
            j = current_line - 1
            while j >= 0 and not lines[j].strip():
                consecutive_blank_lines += 1
                j -= 1

            blank_line_details = []
            if consecutive_blank_lines > 0:
                # Store line numbers and representation for debugging
                for k in range(current_line - consecutive_blank_lines, current_line):
                    line_repr = repr(lines[k])
                    blank_line_details.append(f"Line {k+1}: {line_repr}")

            # Check for missing blank lines
            if consecutive_blank_lines == 0:
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Section Spacing",
                        f"Missing blank line before section [{section_name}] at line {current_line + 1}",
                        current_line + 1,
                    )
                )
                has_spacing_issue = True
            # Check for excessive blank lines (more than 1)
            elif consecutive_blank_lines > 1:
                error_msg = f"Excessive blank lines ({consecutive_blank_lines}) before section [{section_name}] at line {current_line + 1}, maximum is 1"
                # Add detailed debug info in verbose mode
                if __debug__:
                    error_msg += f". Context: Section [{prev_section_name}] at line {prev_line + 1}, blank lines: {', '.join(blank_line_details)}"

                self.errors.append(
                    ValidationError(
                        file_path,
                        "Section Spacing",
                        error_msg,
                        current_line + 1,
                    )
                )
                has_spacing_issue = True

        return has_spacing_issue

    def _extract_sections(self, content: str) -> Tuple[List[str], Dict[str, str], Dict[str, List[str]], Dict[str, str]]:
        """
        Extract sections from TOML content.

        Args:
            content: TOML content

        Returns:
            Tuple of (ordered_section_names, section_types, regular_sections, array_sections)
        """
        sections = []
        found_sections = set()
        section_types = {}  # Maps section name to 'regular' or 'array'

        lines = content.split("\n")

        # First pass: identify all sections and their types
        for line in lines:
            is_header, section_name, section_type = self._is_section_header(line)
            if is_header and section_name not in found_sections:
                sections.append(section_name)
                found_sections.add(section_name)
                section_types[section_name] = section_type

        # Second pass: extract content for each section
        regular_sections = {}
        array_sections = {}

        current_section = None
        current_content = []
        current_type = None

        # Get preamble (comments before first section)
        preamble = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                preamble.append(line)
            else:
                break

        # Process each line to group content by section
        for i, line in enumerate(lines):
            is_header, section_name, section_type = self._is_section_header(line)

            if is_header:
                # Save previous section if any
                if current_section:
                    if current_type == "regular":
                        regular_sections[current_section] = current_content
                    else:  # 'array'
                        if current_section not in array_sections:
                            array_sections[current_section] = []
                        array_sections[current_section].append(current_content)

                # Start new section
                current_section = section_name
                current_content = [line]
                current_type = section_type
            # Content line
            elif current_section:
                current_content.append(line)

        # Save the last section
        if current_section:
            if current_type == "regular":
                regular_sections[current_section] = current_content
            else:  # 'array'
                if current_section not in array_sections:
                    array_sections[current_section] = []
                array_sections[current_section].append(current_content)

        return sections, section_types, regular_sections, array_sections

    def _extract_package_fields(
        self, content: str
    ) -> Tuple[int, int, List[Tuple[str, str]], Dict[str, List[Tuple[int, str]]]]:
        """
        Extract fields from the [package] section.

        Args:
            content: TOML content

        Returns:
            Tuple of (section_start, section_end, field_lines, field_comments)
        """
        package_section_start = None
        package_section_end = None
        package_section_lines = []
        package_section_comments = {}

        lines = content.split("\n")
        in_package_section = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if line_stripped == "[package]":
                in_package_section = True
                package_section_start = i
                continue
            elif in_package_section and (
                (line_stripped.startswith("[") and not line_stripped.startswith("[[")) or line_stripped.startswith("[[")
            ):
                # We've reached the next section
                package_section_end = i
                break
            elif in_package_section:
                package_section_lines.append((i, line))

                # Check if this is a field definition or a comment
                if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                    field_name = line_stripped.split("=")[0].strip()

                    # Collect any comments preceding this field
                    field_comments = []
                    j = len(package_section_lines) - 2
                    while j >= 0:
                        prev_line = package_section_lines[j][1].strip()
                        if prev_line.startswith("#") or not prev_line:
                            field_comments.insert(0, package_section_lines[j])
                            j -= 1
                        else:
                            break

                    package_section_comments[field_name] = field_comments

        # If we didn't find the end, it's the last section
        if package_section_end is None:
            package_section_end = len(lines)

        # Extract field lines (not comments or empty lines)
        field_lines = []
        for i, line in package_section_lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("#") and "=" in line_stripped:
                field_name = line_stripped.split("=")[0].strip()
                field_lines.append((field_name, (i, line)))

        return package_section_start, package_section_end, field_lines, package_section_comments

    def _validate_settings_comments(self, file_path: str, content: str) -> bool:
        """
        Check if each setting in the [settings] section has at least one comment line above it.
        Also checks platform-specific settings sections like [settings."filter:platform=linux*"].
        For multiline lists, only requires one comment at the top of the list declaration.

        Args:
            file_path: Path to the file being validated
            content: The file content to check

        Returns:
            True if comment issues were found, False otherwise
        """
        lines = content.split("\n")
        has_comment_issue = False
        in_settings_section = False
        current_settings_section = ""
        in_multiline_list = False
        multiline_list_indentation = 0

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check for settings section start (including platform-specific settings)
            if (
                line_stripped == "[settings]"
                or line_stripped.startswith('[settings."filter:platform=')
                or line_stripped.startswith("[settings.filter:platform=")
            ):
                in_settings_section = True
                current_settings_section = line_stripped
                continue
            # Check for end of settings section
            elif (
                in_settings_section
                and (
                    (line_stripped.startswith("[") and not line_stripped.startswith("[["))
                    or line_stripped.startswith("[[")
                )
                and not (line_stripped == current_settings_section)
            ):
                in_settings_section = False
                in_multiline_list = False
                continue

            # Track multiline list state
            if in_settings_section:
                # Check if we're entering a multiline list
                if "=" in line_stripped and line_stripped.endswith("["):
                    in_multiline_list = True
                    # Get indentation level for this list to detect when it ends
                    multiline_list_indentation = len(line) - len(line.lstrip())

                # Check if we're exiting a multiline list
                elif in_multiline_list:
                    current_indentation = len(line) - len(line.lstrip())
                    if line_stripped == "]" and current_indentation <= multiline_list_indentation:
                        in_multiline_list = False
                    # Skip validation for lines inside a multiline list
                    if line_stripped and not line_stripped.startswith("#"):
                        continue

            # Check settings entries
            if in_settings_section and line_stripped and not line_stripped.startswith("#"):
                # This is a setting line, check if it has a comment above it
                if (
                    "=" in line_stripped and not in_multiline_list
                ):  # Make sure it's a key-value pair and not inside a list
                    # Check previous line for comment
                    has_comment = False
                    for j in range(i - 1, max(0, i - 5), -1):  # Look up to 5 lines back
                        prev_line = lines[j].strip()
                        if prev_line.startswith("#"):
                            has_comment = True
                            break
                        elif prev_line and not prev_line.startswith("#") and not prev_line.startswith("[settings"):
                            # Found non-empty, non-comment, non-section-header line, so stop looking
                            break
                        elif prev_line.startswith("[settings"):
                            # Reached the section header with no comment in between
                            break

                    if not has_comment:
                        # Extract the setting key for better error reporting
                        setting_key = line_stripped.split("=")[0].strip()
                        self.errors.append(
                            ValidationError(
                                file_path,
                                "Settings Documentation",
                                f"Setting '{setting_key}' at line {i+1} is missing a descriptive comment above it",
                                i + 1,
                            )
                        )
                        has_comment_issue = True

        return has_comment_issue

    def _validate_and_fix_dependencies_order(
        self, file_path: str, content: str, toml_data: Dict, line_mapping: Dict[str, int], fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that dependencies in the [dependencies] section are alphabetically sorted and fix if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            toml_data: Parsed TOML data
            line_mapping: Mapping of section names to line numbers
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # If there's no dependencies section, nothing to do
        if "dependencies" not in toml_data or not toml_data["dependencies"]:
            return False, content

        # Extract the dependencies section
        dependencies = toml_data["dependencies"]

        # Check if dependencies are alphabetically sorted
        dependency_names = list(dependencies.keys())
        sorted_dependency_names = sorted(dependency_names)

        has_order_issue = dependency_names != sorted_dependency_names
        if has_order_issue:
            self.errors.append(
                ValidationError(
                    file_path,
                    "Dependencies Order",
                    f"Dependencies in [dependencies] section should be alphabetically sorted",
                    line_mapping.get("dependencies", 0),
                )
            )

            # Fix the order if needed
            if fix:
                # Find the dependencies section in the content
                lines = content.split("\n")
                in_dependencies_section = False
                section_start = 0
                section_end = 0

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # Find start of dependencies section
                    if line_stripped == "[dependencies]":
                        in_dependencies_section = True
                        section_start = i
                        continue

                    # Find end of dependencies section
                    if in_dependencies_section and line_stripped.startswith("[") and not line_stripped.startswith('["'):
                        section_end = i
                        break

                # If we didn't find the end, it's the last section
                if section_end == 0:
                    section_end = len(lines)

                # Get the dependencies section content
                dependency_lines = lines[section_start + 1 : section_end]

                # Parse dependency entries
                dependency_entries = {}
                current_dependency = None
                current_lines = []
                in_multiline = False

                for line in dependency_lines:
                    line_stripped = line.strip()

                    # Skip empty lines and comments
                    if not line_stripped or line_stripped.startswith("#"):
                        continue

                    # Parse simple dependency line: "dependency.name" = {}
                    if not in_multiline and "=" in line_stripped:
                        # Start a new dependency
                        if current_dependency and current_lines:
                            dependency_entries[current_dependency] = current_lines

                        # Parse the dependency name
                        parts = line_stripped.split("=", 1)
                        name = parts[0].strip().strip('"')
                        current_dependency = name
                        current_lines = [line]

                        # Check if multiline starts
                        if "{" in parts[1] and "}" not in parts[1]:
                            in_multiline = True

                    # End of multiline
                    elif in_multiline and "}" in line_stripped:
                        current_lines.append(line)
                        in_multiline = False

                    # Content inside multiline
                    elif in_multiline:
                        current_lines.append(line)

                # Add the last dependency if any
                if current_dependency and current_lines:
                    dependency_entries[current_dependency] = current_lines

                # Create new sorted content
                new_dependency_lines = []
                for dependency in sorted_dependency_names:
                    if dependency in dependency_entries:
                        new_dependency_lines.extend(dependency_entries[dependency])

                # Rebuild the dependencies section
                new_section = ["[dependencies]"] + new_dependency_lines

                # Replace in original content
                fixed_content = "\n".join(lines[:section_start] + new_section + lines[section_end:])

                self.fixes_applied.append("Sorted dependencies alphabetically in [dependencies] section")
                return True, fixed_content

        return False, content

    def _validate_and_fix_test_dependencies_order(
        self, file_path: str, content: str, toml_data: Dict, line_mapping: Dict[str, int], fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that dependencies in the [[test]] section(s) are alphabetically sorted and fix if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            toml_data: Parsed TOML data
            line_mapping: Mapping of section names to line numbers
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # If there's no test section, nothing to do
        if "test" not in toml_data or not isinstance(toml_data["test"], list) or not toml_data["test"]:
            return False, content

        # Extract all test sections
        test_sections = toml_data["test"]

        # Check if any test section has unsorted dependencies
        has_order_issue = False
        test_section_indices = []

        for i, test_section in enumerate(test_sections):
            if (
                not test_section
                or "dependencies" not in test_section
                or not isinstance(test_section["dependencies"], list)
            ):
                continue

            dependencies = test_section["dependencies"]
            sorted_dependencies = sorted(dependencies)

            if dependencies != sorted_dependencies:
                has_order_issue = True
                test_section_indices.append(i)
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Test Dependencies Order",
                        f"Dependencies in [[test]] section #{i+1} should be alphabetically sorted",
                        line_mapping.get("test", 0),
                    )
                )

        # Fix the test dependencies order if needed
        if has_order_issue and fix:
            fixed_content = content

            # Extract sections from the content to preserve structure
            lines = content.split("\n")
            test_section_starts = []

            # Find all test section starts
            for i, line in enumerate(lines):
                if line.strip() == "[[test]]":
                    test_section_starts.append(i)

            # Process each test section with issues
            for section_idx in test_section_indices:
                if section_idx >= len(test_section_starts):
                    continue

                # Find dependencies block in this test section
                section_start = test_section_starts[section_idx]
                section_end = len(lines)
                if section_idx + 1 < len(test_section_starts):
                    section_end = test_section_starts[section_idx + 1]

                section_lines = lines[section_start:section_end]

                # Find and extract dependencies array
                deps_start = None
                deps_end = None
                in_dependencies = False

                for i, line in enumerate(section_lines):
                    line_stripped = line.strip()

                    if line_stripped.startswith("dependencies = ["):
                        deps_start = i
                        in_dependencies = True
                        if line_stripped.endswith("]"):
                            deps_end = i
                            break
                    elif in_dependencies and line_stripped == "]":
                        deps_end = i
                        break

                if deps_start is not None and deps_end is not None:
                    # Extract dependency lines
                    dep_lines = section_lines[deps_start : deps_end + 1]

                    # Parse dependency values
                    dependencies = []
                    for line in dep_lines[1 : deps_end - deps_start]:  # Skip start and end lines
                        line_stripped = line.strip()
                        if line_stripped and line_stripped != "]" and not line_stripped.startswith("#"):
                            # Remove trailing comma if any
                            if line_stripped.endswith(","):
                                line_stripped = line_stripped[:-1]
                            dependencies.append((line_stripped, line))

                    # Sort dependencies by their values
                    sorted_deps = sorted(dependencies, key=lambda x: x[0])

                    # Create new dependency block
                    new_deps = [dep_lines[0]]  # Start line with "dependencies = ["
                    for dep_value, _ in sorted_deps:
                        # Ensure there's a comma at the end
                        if not dep_value.endswith(","):
                            dep_value += ","
                        new_deps.append("    " + dep_value)
                    new_deps.append(dep_lines[-1])  # End line with "]"

                    # Replace in section lines
                    section_lines[deps_start : deps_end + 1] = new_deps

                    # Replace in original lines
                    lines[section_start:section_end] = section_lines

            # Rebuild content
            fixed_content = "\n".join(lines)
            self.fixes_applied.append("Sorted dependencies alphabetically in [[test]] section(s)")
            return True, fixed_content

        return False, content

    def validate_file(
        self,
        file_path: str,
        fix_whitespace: bool = False,
        fix_section_order: bool = False,
        fix_package_order: bool = False,
        fix_dependencies_order: bool = False,
        check_settings_comments: bool = True,
        dry_run: bool = False,
        show_diff: bool = False,
        check_write_target: bool = False,
        verbose: bool = False,  # Add verbose parameter
    ) -> List[ValidationError]:
        """
        Validate a TOML file against the extension.toml style guide.

        Args:
            file_path: Path to the TOML file
            fix_whitespace: Whether to fix whitespace issues
            fix_section_order: Whether to fix section order issues
            fix_package_order: Whether to fix package field order issues
            fix_dependencies_order: Whether to fix dependency alphabetical order issues
            check_settings_comments: Whether to check for missing comments in [settings] section
            dry_run: Whether to show changes without applying them
            show_diff: Whether to show diff of changes
            check_write_target: Whether to check for writeTarget.kit field
            verbose: Enable verbose output for debugging

        Returns:
            List of validation errors
        """
        self._verbose = verbose  # Store verbose flag for use in other methods
        if verbose:
            print(f"DEBUG: Starting validation of {file_path}")
        if not os.path.exists(file_path):
            self.errors.append(ValidationError(file_path, "File Not Found", f"File {file_path} does not exist"))
            return self.errors

        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(ValidationError(file_path, "File Read Error", str(e)))
            return self.errors

        # Reset the errors list for this file
        self.errors = []
        self.fixes_applied = []

        try:
            toml_data = toml.loads(content)
        except Exception as e:
            self.errors.append(ValidationError(file_path, "TOML Parse Error", str(e)))
            return self.errors

        # Create a mapping of section names to line numbers for error reporting
        line_mapping = self._create_line_mapping(content)

        # If we're using the fix flag, these will be set to true
        fixed = False
        fixed_content = content

        # Check for whitespace issues and fix if requested
        if fix_whitespace:
            fixed_whitespace = self._fix_whitespace(fixed_content)
            if fixed_whitespace != fixed_content:
                fixed_content = fixed_whitespace
                fixed = True
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check for section order issues and fix if requested
        if fix_section_order:
            sections_fixed, fixed_content = self._validate_and_fix_section_order(
                file_path, fixed_content, toml_data, line_mapping, True
            )
            if sections_fixed:
                fixed = True
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check [package] section
        if "package" in toml_data:
            # Check and fix [package] field order
            if fix_package_order:
                package_fields_fixed, fixed_content = self._validate_and_fix_package_fields(
                    file_path, fixed_content, toml_data["package"], line_mapping.get("package", 0), True
                )
                if package_fields_fixed:
                    fixed = True
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

            # Check for appropriate writeTarget.kit presence
            if check_write_target:
                write_target_fixed, fixed_content = self._validate_required_write_target_kit(
                    file_path, fixed_content, toml_data["package"], line_mapping.get("package", 0), True
                )
                if write_target_fixed:
                    fixed = True
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

        # Check spacing between sections
        self._check_section_spacing(file_path, fixed_content)

        # Check [settings] section comments
        if check_settings_comments and "settings" in toml_data:
            self._validate_settings_comments(file_path, fixed_content)

        # Check and fix test section field order
        if "test" in toml_data and fix_package_order:  # Reuse fix_package_order flag for test order fixes
            test_fields_fixed, fixed_content = self._validate_and_fix_test_fields(
                file_path, fixed_content, toml_data, line_mapping, True
            )

            if test_fields_fixed:
                fixed = True

        # Check and fix test section order
        # print("DEBUG: About to call _validate_test_section_order") # <<< Removed debug print
        has_multiple_unnamed, has_order_issue = self._validate_test_section_order(file_path, fixed_content)
        # print(f"DEBUG: _validate_test_section_order returned: multiple_unnamed={has_multiple_unnamed}, order_issue={has_order_issue}") # <<< Removed debug print

        if (has_order_issue or has_multiple_unnamed) and fix_section_order:  # Reuse fix_section_order flag
            # print("DEBUG: Order issue detected, fixing with _validate_and_fix_test_section_order") # <<< Removed debug print
            test_order_fixed, fixed_content = self._validate_and_fix_test_section_order(file_path, fixed_content, True)
            # print(f"DEBUG: _validate_and_fix_test_section_order returned: {test_order_fixed}") # <<< Removed debug print
            if test_order_fixed:
                fixed = True
                # print(f"DEBUG: Fixed content length after test order fix: {len(fixed_content)}") # <<< Removed debug print
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check and fix dependencies alphabetical order
        if fix_dependencies_order:
            # Fix dependencies section
            if "dependencies" in toml_data:
                deps_fixed, fixed_content = self._validate_and_fix_dependencies_order(
                    file_path, fixed_content, toml_data, line_mapping, True
                )
                if deps_fixed:
                    fixed = True
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

            # Fix test dependencies
            if "test" in toml_data:
                test_deps_fixed, fixed_content = self._validate_and_fix_test_dependencies_order(
                    file_path, fixed_content, toml_data, line_mapping, True
                )
                if test_deps_fixed:
                    fixed = True

        # If the file was fixed, apply changes
        if fixed and not dry_run:
            self._apply_fixes(file_path, fixed_content, toml_data)
        elif fixed and dry_run:
            self._report_fixes(file_path, content, fixed_content, show_diff)

        return self.errors

    def _apply_fixes(self, file_path: str, fixed_content: str, original_toml_data: Dict) -> None:
        """
        Apply fixes to the file and verify the result.

        Args:
            file_path: Path to the file being fixed
            fixed_content: Fixed content to write
            original_toml_data: Original parsed TOML data for verification
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        print(f"Fixed issues in {file_path}")
        for fix_msg in self.fixes_applied:
            print(f"  - {fix_msg}")

        # Verify that the fixed content is valid and preserves important sections
        try:
            # Parse the fixed content to ensure it's valid TOML
            fixed_toml = toml.loads(fixed_content)

            # Verify that important sections are preserved
            if "package" in original_toml_data and "package" not in fixed_toml:
                print(f"  - ERROR: [package] section missing in fixed content!")

            # Check for array sections like python.module or native.plugin
            array_sections = ["python.module", "native.plugin", "native.library", "test", "trigger"]
            for section in array_sections:
                # In TOML, array sections appear as lists in the parsed data
                array_in_original = isinstance(original_toml_data.get(section), list)
                array_in_fixed = isinstance(fixed_toml.get(section), list)

                if array_in_original and not array_in_fixed:
                    print(f"  - ERROR: [[{section}]] sections missing in fixed content!")

            # Check for regular sections
            for section in original_toml_data:
                if (
                    section not in fixed_toml
                    and section != "package"
                    and not isinstance(original_toml_data[section], list)
                ):
                    print(f"  - ERROR: [{section}] section missing in fixed content!")

        except Exception as e:
            print(f"  - ERROR: Failed to parse fixed content: {str(e)}")

    def _report_fixes(self, file_path: str, original_content: str, fixed_content: str, show_diff: bool) -> None:
        """
        Report fixes that would be applied in dry-run mode.

        Args:
            file_path: Path to the file being checked
            original_content: Original file content
            fixed_content: Fixed content
            show_diff: Whether to show diffs
        """
        print(f"Would fix issues in {file_path} (dry run)")
        for fix_msg in self.fixes_applied:
            print(f"  - {fix_msg}")

        # Print diff in dry-run mode
        if show_diff:
            print("\nChanges that would be made:")
            diff = self._generate_diff(file_path, original_content, fixed_content)
            if diff:
                print(diff)
            else:
                # If no diff, show before and after anyway for debugging
                print("\nOriginal content:")
                print("```")
                print(original_content)
                print("```")
                print("\nFixed content:")
                print("```")
                print(fixed_content)
                print("```")

    def _validate_and_fix_section_order(
        self, file_path: str, content: str, toml_data: Dict, line_mapping: Dict[str, int], fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that sections appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            toml_data: Parsed TOML data
            line_mapping: Mapping of section names to line numbers
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # Extract sections from the content to preserve order
        sections, section_types, regular_sections, array_sections = self._extract_sections(content)

        # Check for order issues
        has_order_issue = self._check_section_order(file_path, sections, line_mapping)

        # If there's an order issue, reorder the sections
        if has_order_issue and fix:
            return self._reorder_sections(content, regular_sections, array_sections)

        return False, content

    def _check_section_order(self, file_path: str, sections: List[str], line_mapping: Dict[str, int]) -> bool:
        """
        Check if sections are in the correct order.

        Args:
            file_path: Path to the file being validated
            sections: List of section names in order
            line_mapping: Mapping of section names to line numbers

        Returns:
            True if order issues were found, False otherwise
        """
        has_order_issue = False
        last_index = -1

        for section in sections:
            # Handle platform-specific settings sections
            normalized_section = section
            if section.startswith('settings."filter:platform"') or section.startswith("settings.filter:platform"):
                normalized_section = "settings"

            if normalized_section in SECTION_ORDER:
                current_index = SECTION_ORDER.index(normalized_section)
                if current_index < last_index:
                    self.errors.append(
                        ValidationError(
                            file_path,
                            "Section Order",
                            f"Section [{section}] appears out of order. Expected order: {', '.join(SECTION_ORDER)}",
                            line_mapping.get(section),
                        )
                    )
                    has_order_issue = True
                last_index = current_index
            else:
                # Unknown section, not in our defined order
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Unknown Section",
                        f"Unknown section [{section}] found. Known sections: {', '.join(SECTION_ORDER)}",
                        line_mapping.get(section),
                    )
                )

        return has_order_issue

    def _reorder_sections(
        self, content: str, regular_sections: Dict[str, List[str]], array_sections: Dict[str, List[List[str]]]
    ) -> Tuple[bool, str]:
        """
        Reorder sections according to the expected order.

        Args:
            content: Original content
            regular_sections: Regular sections extracted from content
            array_sections: Array sections extracted from content

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # Get preamble (comments before first section)
        preamble = []
        for line in content.split("\n"):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                preamble.append(line)
            else:
                break

        # Build the new content in correct order
        new_content_parts = []

        # Add preamble first
        if preamble:
            new_content_parts.append("\n".join(preamble))

        # Track sections we've added
        ordered_sections = []

        # Add regular sections in the correct order
        for section_name in SECTION_ORDER:
            # Regular section
            if section_name in regular_sections:
                new_content_parts.append("\n".join(regular_sections[section_name]))
                ordered_sections.append(section_name)

            # Platform-specific settings sections
            if section_name == "settings":
                for section in regular_sections:
                    if section.startswith('settings."filter:platform"') or section.startswith(
                        "settings.filter:platform"
                    ):
                        new_content_parts.append("\n".join(regular_sections[section]))
                        ordered_sections.append(section)

            # Array sections
            if section_name in array_sections:
                for array_content in array_sections[section_name]:
                    new_content_parts.append("\n".join(array_content))
                ordered_sections.append(f"{section_name} (array)")

        # Add any remaining regular sections not in our order list
        for section in regular_sections:
            if section not in SECTION_ORDER and not (
                section.startswith('settings."filter:platform"') or section.startswith("settings.filter:platform")
            ):
                new_content_parts.append("\n".join(regular_sections[section]))
                ordered_sections.append(section)

        # Add any remaining array sections not in our order list
        for section_name in array_sections:
            if section_name not in SECTION_ORDER:
                for array_content in array_sections[section_name]:
                    new_content_parts.append("\n".join(array_content))
                ordered_sections.append(f"{section_name} (array)")

        # Join with a single newline between sections, we'll fix spacing after
        new_content = ""
        for i, part in enumerate(new_content_parts):
            if i > 0 and part:
                new_content += "\n"  # Add just a newline between parts
            new_content += part

        # Now use _fix_whitespace to properly handle spacing between sections
        new_content = self._fix_whitespace(new_content)

        # Remove spacing-related messages that might have been added by _fix_whitespace
        # since we're doing reordering and don't want to confuse the user
        self.fixes_applied = [
            fix
            for fix in self.fixes_applied
            if not (
                fix.startswith("Reduced excessive")
                or fix.startswith("Added required")
                or fix.startswith("Removed extra")
                or fix.startswith("Fixed spacing")
                or fix.startswith("Standardized lines")
            )
        ]

        self.fixes_applied.append(f"Reordered sections to match standard order: {', '.join(ordered_sections)}")
        return True, new_content

    def _validate_and_fix_package_fields(
        self, file_path: str, content: str, package_data: Dict, section_line: int, fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that fields in the [package] section appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            package_data: Parsed data for the [package] section
            section_line: Line number where the [package] section starts
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # Extract the package section and its fields
        try:
            # Find the [package] section and extract fields in order
            (
                package_section_start,
                package_section_end,
                field_lines,
                package_section_comments,
            ) = self._extract_package_fields(content)

            # Check if fields are in the correct order
            has_order_issue = self._check_package_field_order(file_path, field_lines, section_line)

            # Fix the order if needed
            if has_order_issue and fix:
                return self._reorder_package_fields(
                    content, field_lines, package_section_comments, package_section_start, package_section_end
                )

        except Exception as e:
            self.errors.append(
                ValidationError(file_path, "Error", f"Error validating package fields: {str(e)}", section_line)
            )

        return False, content

    def _check_package_field_order(
        self, file_path: str, field_lines: List[Tuple[str, Tuple[int, str]]], section_line: int
    ) -> bool:
        """
        Check if package fields are in the correct order.

        Args:
            file_path: Path to the file being validated
            field_lines: List of field names and their lines
            section_line: Line number where the [package] section starts

        Returns:
            True if order issues were found, False otherwise
        """
        has_order_issue = False
        field_names = [field[0] for field in field_lines]

        last_index = -1
        for field in field_names:
            if field in PACKAGE_FIELD_ORDER:
                current_index = PACKAGE_FIELD_ORDER.index(field)
                if current_index < last_index:
                    self.errors.append(
                        ValidationError(
                            file_path,
                            "Package Field Order",
                            f"Field '{field}' in [package] section appears out of order. Expected order: {', '.join(PACKAGE_FIELD_ORDER)}",
                            section_line,
                        )
                    )
                    has_order_issue = True
                last_index = current_index

        return has_order_issue

    def _reorder_package_fields(
        self,
        content: str,
        field_lines: List[Tuple[str, Tuple[int, str]]],
        package_section_comments: Dict[str, List[Tuple[int, str]]],
        package_section_start: int,
        package_section_end: int,
    ) -> Tuple[bool, str]:
        """
        Reorder fields in the package section.

        Args:
            content: Original content
            field_lines: List of field names and their lines
            package_section_comments: Comments for each field
            package_section_start: Start line of package section
            package_section_end: End line of package section

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        lines = content.split("\n")

        # Create a mapping of field names to their lines
        field_map = {field[0]: field[1] for field in field_lines}
        field_names = [field[0] for field in field_lines]

        # Get the ordered fields that exist in this file
        ordered_fields = [f for f in PACKAGE_FIELD_ORDER if f in field_map]
        # Get any fields that aren't in our expected order
        non_ordered_fields = [f for f in field_names if f not in PACKAGE_FIELD_ORDER]

        # Reconstruct the package section with fields in the correct order
        new_package_section_lines = []

        # Add the ordered fields with their comments
        for field in ordered_fields:
            # Add comments for this field
            if field in package_section_comments:
                for comment_index, comment_line in package_section_comments[field]:
                    new_package_section_lines.append(comment_line)

            # Add the field line
            new_package_section_lines.append(field_map[field][1])

        # Add any non-ordered fields at the end
        for field in non_ordered_fields:
            # Add comments for this field
            if field in package_section_comments:
                for comment_index, comment_line in package_section_comments[field]:
                    new_package_section_lines.append(comment_line)

            # Add the field line
            new_package_section_lines.append(field_map[field][1])

        # Rebuild the content
        new_content = (
            "\n".join(lines[: package_section_start + 1])
            + "\n"
            + "\n".join(new_package_section_lines)
            + "\n"
            + "\n".join(lines[package_section_end:])
        )

        self.fixes_applied.append(
            f"Reordered [package] section fields to match standard order: {', '.join(ordered_fields)}"
        )
        return True, new_content

    def _validate_deprecation_section(self, file_path: str, deprecation_data: Dict, section_line: int) -> None:
        """
        Validate the [deprecation] section.

        Args:
            file_path: Path to the TOML file
            deprecation_data: Parsed data for the [deprecation] section
            section_line: Line number where the [deprecation] section starts
        """
        # Check that the required field 'warning' exists
        if "warning" not in deprecation_data:
            self.errors.append(
                ValidationError(
                    file_path,
                    "Deprecation Field Missing",
                    f"Required field 'warning' missing in [deprecation] section",
                    section_line,
                )
            )

        # Check that the warning message is not empty
        elif not deprecation_data["warning"]:
            self.errors.append(
                ValidationError(
                    file_path, "Deprecation Warning Empty", f"Deprecation warning message is empty", section_line
                )
            )

    def _validate_and_fix_test_fields(
        self, file_path: str, content: str, toml_data: Dict, line_mapping: Dict[str, int], fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that fields in [[test]] sections appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            toml_data: Parsed TOML data
            line_mapping: Mapping of section names to line numbers
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        # If there's no test section, nothing to do
        if "test" not in toml_data or not isinstance(toml_data["test"], list) or not toml_data["test"]:
            return False, content

        # Extract the test sections - this will automatically filter out empty test sections
        test_section_lines, array_section_content, _, _ = self._extract_test_sections(content)  # Fix unpacking

        if not test_section_lines or not array_section_content:
            return False, content

        # Make sure we have the same number of sections in TOML data as we extracted
        # This can be different if there are empty test sections
        non_empty_test_sections = []
        for test_section in toml_data["test"]:
            if test_section:  # Skip empty sections
                non_empty_test_sections.append(test_section)

        # If there's a mismatch, we might have a problem
        if len(non_empty_test_sections) != len(array_section_content):
            # Try to match sections by content
            matched_test_sections = []

            for section_content in array_section_content:
                # Parse this section's content to identify it
                section_dict = {}
                for line in section_content[1:]:  # Skip [[test]] header
                    line_stripped = line.strip()
                    if "=" in line_stripped and not line_stripped.startswith("#"):
                        key = line_stripped.split("=", 1)[0].strip()
                        if key == "name" and not line_stripped.endswith("["):
                            # Found a name field - use it to match the section
                            try:
                                name_value = line_stripped.split("=", 1)[1].strip()
                                # Remove quotes if present
                                if name_value.startswith('"') and name_value.endswith('"'):
                                    name_value = name_value[1:-1]
                                section_dict["name"] = name_value
                            except:
                                pass

                # Try to find a matching section in non_empty_test_sections
                matched = False
                for test_section in non_empty_test_sections:
                    if (
                        "name" in section_dict
                        and "name" in test_section
                        and section_dict["name"] == test_section["name"]
                    ):
                        matched_test_sections.append(test_section)
                        matched = True
                        break

                if not matched:
                    # No match found, just take the first unused section
                    for test_section in non_empty_test_sections:
                        if test_section not in matched_test_sections:
                            matched_test_sections.append(test_section)
                            break

            # Use matched sections if we found enough
            if len(matched_test_sections) == len(array_section_content):
                non_empty_test_sections = matched_test_sections
            # Otherwise just use as many as we have
            elif len(non_empty_test_sections) > len(array_section_content):
                non_empty_test_sections = non_empty_test_sections[: len(array_section_content)]

        has_order_issue = False

        # Check each test section for field order issues
        for i, test_section in enumerate(non_empty_test_sections):
            if i < len(test_section_lines):
                section_start_line = test_section_lines[i]
                has_issue_in_section = self._check_test_field_order(file_path, test_section, section_start_line)
                has_order_issue = has_order_issue or has_issue_in_section

        # If there's an order issue and we should fix it
        if has_order_issue and fix:
            fixed_content = self._reorder_test_fields(
                content, non_empty_test_sections, test_section_lines, array_section_content
            )
            return True, fixed_content

        return False, content

    def _extract_test_sections(self, content: str) -> Tuple[List[int], List[List[str]]]:
        """
        Extract all [[test]] sections from the content.
        Also returns the start line of the first test section and end line of the last test section.

        Args:
            content: The raw TOML content

        Returns:
            Tuple of (section_line_numbers, section_contents, block_start_line, block_end_line)
            where block_start_line and block_end_line define the contiguous block containing all [[test]] sections.
            Returns (-1, -1) for block lines if no test sections are found.
        """
        lines = content.split("\n")
        section_line_numbers = []
        section_contents = []
        block_start_line = -1
        block_end_line = -1

        in_test_section = False
        current_section_lines = []
        current_section_start_line = -1

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check for start of test section
            if line_stripped == "[[test]]":
                # If this is the first test section encountered, mark the block start
                if block_start_line == -1:
                    block_start_line = i

                in_test_section = True

                # If we already have a test section started, add it to our list
                if current_section_lines:
                    # Only add non-empty sections
                    if any(l.strip() and not l.strip().startswith("#") for l in current_section_lines[1:]):
                        section_line_numbers.append(current_section_start_line)
                        section_contents.append(current_section_lines)

                # Start a new section
                current_section_lines = [line]
                current_section_start_line = i
            # Check for end of section (next section header)
            elif (
                in_test_section
                and (line_stripped.startswith("[") and not line_stripped.startswith("[["))
                or (line_stripped.startswith("[[") and not line_stripped.startswith("[[test]]"))
            ):
                in_test_section = False
                block_end_line = i  # Mark the end of the block

                # Add the last test section if it's non-empty
                if current_section_lines and any(
                    l.strip() and not l.strip().startswith("#") for l in current_section_lines[1:]
                ):
                    section_line_numbers.append(current_section_start_line)
                    section_contents.append(current_section_lines)

                current_section_lines = []  # Reset
                # Since we found the end, break the loop for test sections
                break
            # Add content lines to current section
            elif in_test_section:
                current_section_lines.append(line)

        # Add the last section if there is one and we didn't break early
        if in_test_section and current_section_lines:
            block_end_line = len(lines)  # Reaches end of file
            # Only add non-empty sections
            if any(l.strip() and not l.strip().startswith("#") for l in current_section_lines[1:]):
                section_line_numbers.append(current_section_start_line)
                section_contents.append(current_section_lines)

        return section_line_numbers, section_contents, block_start_line, block_end_line

    def _validate_test_section_order(self, file_path: str, content: str) -> Tuple[bool, bool]:
        """
        Validate that:
        1. There is only one unnamed test section
        2. Unnamed test sections appear before named test sections

        Args:
            file_path: Path to the file being validated
            content: The file content to check

        Returns:
            Tuple of (has_multiple_unnamed_sections, has_order_issue)
        """
        if self._verbose:
            print(f"DEBUG: Validating test section order in {file_path}")
        lines = content.split("\n")

        # Extract all test sections with their names and line numbers
        test_sections_info = []  # List of tuples: (start_line, has_name)
        in_test_section = False
        current_section_start = -1
        current_section_has_name = False

        # Find all test sections and whether they have a name field
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Start of a test section
            if line_stripped == "[[test]]":
                # If we were already in a section, save the previous one
                if in_test_section:
                    test_sections_info.append((current_section_start, current_section_has_name))

                # Start tracking the new section
                in_test_section = True
                current_section_start = i
                current_section_has_name = False
                # if self._verbose: # <<< Optional: Add verbose check here if needed
                #     print(f"DEBUG: Found test section at line {i}")
                continue

            # Process lines within a test section
            if in_test_section:
                # Check if the line defines a name
                if line_stripped.startswith("name") and "=" in line_stripped and not line_stripped.endswith("["):
                    # if self._verbose: # <<< Optional: Add verbose check here if needed
                    #     print(f"DEBUG: Found name at line {i}: '{line_stripped}'")
                    current_section_has_name = True
                # End of test section block (start of a new, non-test section)
                elif (line_stripped.startswith("[") and not line_stripped.startswith("[[")) or (
                    line_stripped.startswith("[[") and not line_stripped.startswith("[[test]]")
                ):
                    # if self._verbose: # <<< Optional: Add verbose check here if needed
                    #     print(f"DEBUG: End of section at line {i}")
                    # Save the last test section info
                    test_sections_info.append((current_section_start, current_section_has_name))
                    in_test_section = False  # Stop processing test sections
                    break

        # Add the last section if we reached the end of the file while in a test section
        if in_test_section:
            test_sections_info.append((current_section_start, current_section_has_name))

        # Now check for issues based on the collected info
        unnamed_sections = [section for section in test_sections_info if not section[1]]
        named_sections = [section for section in test_sections_info if section[1]]

        if self._verbose:
            print(f"DEBUG: test_sections_info = {test_sections_info}")
            print(f"DEBUG: unnamed_sections = {unnamed_sections}")
            print(f"DEBUG: named_sections = {named_sections}")

        has_multiple_unnamed_sections = len(unnamed_sections) > 1
        has_order_issue = False

        # Check if there are multiple unnamed sections
        if has_multiple_unnamed_sections:
            self.errors.append(
                ValidationError(
                    file_path,
                    "Test Section Structure",
                    f"Found {len(unnamed_sections)} unnamed [[test]] sections. Only one unnamed test section is allowed.",
                    unnamed_sections[1][0] + 1,  # Report error at the second unnamed section
                )
            )

        # Check if unnamed sections come before named sections
        if unnamed_sections and named_sections:
            # Find the line number of the last unnamed section
            max_unnamed_line = max(section[0] for section in unnamed_sections)
            # Find the line number of the first named section
            min_named_line = min(section[0] for section in named_sections)

            if self._verbose:
                print(f"DEBUG: max_unnamed_line={max_unnamed_line}, min_named_line={min_named_line}")

            if max_unnamed_line > min_named_line:
                has_order_issue = True
                # Find the first named section that appears before the last unnamed section
                offending_named_section = min(
                    (s for s in named_sections if s[0] < max_unnamed_line), key=lambda x: x[0]
                )
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Test Section Order",
                        f"Named [[test]] section at line {offending_named_section[0] + 1} appears before unnamed section at line {max_unnamed_line + 1}. Unnamed section must come first.",
                        offending_named_section[0] + 1,
                    )
                )

        if self._verbose:
            print(
                f"DEBUG: has_multiple_unnamed_sections={has_multiple_unnamed_sections}, has_order_issue={has_order_issue}"
            )

        return has_multiple_unnamed_sections, has_order_issue

    def _validate_and_fix_test_section_order(self, file_path: str, content: str, fix: bool = False) -> Tuple[bool, str]:
        """
        Validate and fix the order of test sections:
        1. Ensure only one unnamed test section (keeps the first one found)
        2. Ensure the unnamed test section appears before named test sections
        3. Sort named test sections alphabetically by their 'name' field.

        Args:
            file_path: Path to the file being validated
            content: Raw TOML content
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        has_multiple_unnamed_sections, has_order_issue = self._validate_test_section_order(file_path, content)

        # If there are no issues or we're not fixing, just return
        if (not has_multiple_unnamed_sections and not has_order_issue) or not fix:
            return False, content

        if self._verbose:
            print(f"DEBUG: Fixing issues: multi_unnamed={has_multiple_unnamed_sections}, order_issue={has_order_issue}")

        lines = content.split("\n")

        # Extract all test sections with content, name, and track block boundaries
        section_lines, section_contents, block_start, block_end = self._extract_test_sections(content)

        # If no test sections found, something is wrong (or file changed)
        if block_start == -1:
            return False, content

        unnamed_test_sections = []
        named_test_sections = []  # List of tuples: (section_content_list, name_value)

        for section_content in section_contents:
            has_name = False
            section_name = ""
            # Check for name field within the section content
            for line in section_content:
                line_stripped = line.strip()
                if line_stripped.startswith("name") and "=" in line_stripped and not line_stripped.endswith("["):
                    has_name = True
                    try:
                        name_value = line_stripped.split("=", 1)[1].strip()
                        # Remove quotes if present
                        if name_value.startswith('"') and name_value.endswith('"'):
                            name_value = name_value[1:-1]
                        section_name = name_value
                    except:
                        pass  # Ignore potential errors in extracting name
                    break  # Found name, no need to check further lines in this section

            if has_name:
                if self._verbose:
                    print(f"DEBUG: Found named section: {section_name}")
                named_test_sections.append((section_content, section_name))
            else:
                if self._verbose:
                    print(f"DEBUG: Found unnamed section")
                unnamed_test_sections.append(section_content)

        # Handle multiple unnamed test sections - keep only the first one found
        kept_unnamed_section = []
        if unnamed_test_sections:
            kept_unnamed_section = unnamed_test_sections[0]  # Keep the first one
            if len(unnamed_test_sections) > 1:
                self.fixes_applied.append(
                    f"Removed {len(unnamed_test_sections) - 1} duplicate unnamed test sections, keeping the first."
                )

        # Sort named test sections alphabetically by name
        named_test_sections.sort(key=lambda x: x[1])  # Sort by name (index 1)

        # Rebuild the block content
        reordered_block_lines = []

        # Add the single unnamed section first (if it exists)
        if kept_unnamed_section:
            reordered_block_lines.extend(kept_unnamed_section)

        # Add named sections
        for i, (section_content, _) in enumerate(named_test_sections):
            # Add a blank line before this named section if it's not the first section in the block
            # OR if it follows the unnamed section
            if kept_unnamed_section or i > 0:
                # Check if the last line added wasn't already blank
                if reordered_block_lines and reordered_block_lines[-1].strip():
                    reordered_block_lines.append("")
            reordered_block_lines.extend(section_content)

        # Combine the parts of the file
        # Content before the block + reordered block + content after the block
        fixed_content_lines = lines[:block_start] + reordered_block_lines + lines[block_end:]

        # Add messages about fixes
        if has_multiple_unnamed_sections:
            # Message already added when selecting the kept section
            pass
        if has_order_issue:
            self.fixes_applied.append("Reordered [[test]] sections (unnamed first, then named alphabetically)")
        elif named_test_sections:
            # Check if the order actually changed
            original_named_order = [
                name for _, name in named_test_sections
            ]  # Original extracted order might not be sorted
            # Extract names based on original section_contents order
            original_named_names = []
            for section_content in section_contents:
                section_name = None
                for line in section_content:
                    line_stripped = line.strip()
                    if line_stripped.startswith("name") and "=" in line_stripped and not line_stripped.endswith("["):
                        try:
                            name_value = line_stripped.split("=", 1)[1].strip().strip('"')
                            section_name = name_value
                        except:
                            pass
                        break
                if section_name is not None:
                    original_named_names.append(section_name)

            sorted_original_names = sorted(original_named_names)
            if original_named_names != sorted_original_names:
                self.fixes_applied.append("Sorted named [[test]] sections alphabetically")

        if self._verbose:
            print(f"DEBUG: Test position: {block_start}")  # Use block_start as test position indicator

        fixed_content = "\n".join(fixed_content_lines)

        # Run whitespace fixer again to ensure proper spacing around the modified block
        fixed_content = self._fix_whitespace(fixed_content)

        # Remove potential duplicate whitespace messages added by the second call
        ws_fixes = [
            "Reduced excessive blank lines between sections to exactly one",
            "Added required blank lines between sections",
            "Removed extra empty lines at start and/or end of file",
            "Standardized lines with only whitespace characters to empty lines",
            "Fixed spacing between sections (added missing blank lines and reduced excessive blank lines)",
        ]
        # Keep only the last instance of each whitespace fix message
        final_fixes = []
        seen_ws_fixes = set()
        for fix_msg in reversed(self.fixes_applied):
            if fix_msg in ws_fixes:
                if fix_msg not in seen_ws_fixes:
                    final_fixes.insert(0, fix_msg)
                    seen_ws_fixes.add(fix_msg)
            else:
                final_fixes.insert(0, fix_msg)
        self.fixes_applied = final_fixes

        if self._verbose:
            print(f"DEBUG: Original content length: {len(content)}, Fixed content length: {len(fixed_content)}")

        # Return True if any structural change was made
        was_fixed = (
            has_multiple_unnamed_sections
            or has_order_issue
            or (named_test_sections and original_named_names != sorted_original_names)
        )
        return was_fixed, fixed_content

    def _check_test_field_order(self, file_path: str, test_section: Dict, section_line: int) -> bool:
        """
        Check if fields in a [[test]] section are in the correct order.

        Args:
            file_path: Path to the file being validated
            test_section: The parsed test section data
            section_line: Line number where the test section starts

        Returns:
            True if order issues were found, False otherwise
        """
        has_order_issue = False
        field_order = []

        # Collect fields that exist in this test section
        for field in test_section:
            if field in TEST_FIELD_ORDER:
                field_order.append(field)

        # Check order by comparing pairs of adjacent fields
        last_index = -1
        for field in field_order:
            current_index = TEST_FIELD_ORDER.index(field)
            if current_index < last_index:
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Test Field Order",
                        f"Field '{field}' in [[test]] section appears out of order. Expected order: {', '.join(TEST_FIELD_ORDER)}",
                        section_line + 1,
                    )
                )
                has_order_issue = True
            last_index = current_index

        return has_order_issue

    def _reorder_test_fields(
        self, content: str, test_sections: List[Dict], section_lines: List[int], section_contents: List[List[str]]
    ) -> str:
        """
        Reorder fields in test sections to match the expected order.

        Args:
            content: Original content
            test_sections: List of test section dictionaries
            section_lines: Line numbers where test sections start
            section_contents: Contents of each test section

        Returns:
            Fixed content with reordered test sections
        """
        lines = content.split("\n")
        fixed_lines = lines.copy()

        # Track the line offset as we modify the file
        line_offset = 0

        for i, (test_section, section_content) in enumerate(zip(test_sections, section_contents)):
            if i >= len(section_lines):
                continue

            section_start = section_lines[i] + line_offset

            # Parse the original section to extract each field
            parsed_fields = {}

            # Keep track of non-field lines (comments, whitespace) to preserve them
            non_field_lines = []

            # Extract all fields and their original formatting
            in_array_field = False
            current_field = None
            field_lines = []

            j = 1  # Skip the [[test]] header
            while j < len(section_content):
                line = section_content[j]
                line_stripped = line.strip()

                # Handle comments and blank lines
                if not line_stripped or line_stripped.startswith("#"):
                    if in_array_field:
                        field_lines.append(line)
                    else:
                        non_field_lines.append((j, line))
                    j += 1
                    continue

                # Handle field assignment
                if "=" in line_stripped and not in_array_field:
                    field_name = line_stripped.split("=", 1)[0].strip()

                    # Simple non-array field
                    if not line_stripped.endswith("["):
                        parsed_fields[field_name] = {"lines": [line], "original_pos": j}
                        j += 1
                        continue

                    # Array field start
                    in_array_field = True
                    current_field = field_name
                    field_lines = [line]
                    j += 1
                    continue

                # End of array field
                if in_array_field and line_stripped == "]":
                    field_lines.append(line)
                    parsed_fields[current_field] = {"lines": field_lines, "original_pos": j - len(field_lines) + 1}
                    in_array_field = False
                    j += 1
                    continue

                # Content inside an array field
                if in_array_field:
                    field_lines.append(line)
                    j += 1
                    continue

                # Unknown line - just keep it
                non_field_lines.append((j, line))
                j += 1

            # Create a new ordered section
            new_section = ["[[test]]"]

            # Add comments that appear at the very beginning of the section
            for pos, line in non_field_lines:
                if pos == 1:  # Right after the [[test]] header
                    new_section.append(line)

            # Add fields in correct order
            for field_name in TEST_FIELD_ORDER:
                if field_name in parsed_fields:
                    # Add any non-field lines that appear right before this field
                    field_pos = parsed_fields[field_name]["original_pos"]
                    for pos, line in non_field_lines:
                        if pos == field_pos - 1:
                            new_section.append(line)

                    # Add the field itself
                    new_section.extend(parsed_fields[field_name]["lines"])

            # Add any fields not in TEST_FIELD_ORDER at the end
            for field_name, field_data in parsed_fields.items():
                if field_name not in TEST_FIELD_ORDER:
                    new_section.extend(field_data["lines"])

            # Replace the section in the file
            section_end = section_start + len(section_content)
            old_section_length = len(section_content)
            new_section_length = len(new_section)

            fixed_lines[section_start:section_end] = new_section

            # Update line offset for subsequent sections
            line_offset += new_section_length - old_section_length

        self.fixes_applied.append(
            f"Reordered [[test]] section fields to match standard order: {', '.join(TEST_FIELD_ORDER)}"
        )

        return "\n".join(fixed_lines)

    def _generate_diff(self, file_path: str, original_content: str, fixed_content: str) -> str:
        """
        Generate a unified diff between the original and fixed content.

        Args:
            file_path: Path to the file being validated
            original_content: Original file content
            fixed_content: Fixed file content

        Returns:
            Unified diff as a string
        """
        # Split content into lines
        original_lines = original_content.splitlines()
        fixed_lines = fixed_content.splitlines()

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                fixed_lines,
                fromfile=f"a/{os.path.basename(file_path)}",
                tofile=f"b/{os.path.basename(file_path)}",
                n=3,  # Context lines
                lineterm="",  # No trailing newlines
            )
        )

        # If terminal supports colors, add coloring
        if USE_COLORS:
            return self._colorize_diff(diff_lines)
        else:
            return "\n".join(diff_lines)

    def _colorize_diff(self, diff_lines: List[str]) -> str:
        """
        Add color formatting to diff lines.

        Args:
            diff_lines: List of diff lines

        Returns:
            Colored diff as a string
        """
        colored_diff = []
        for line in diff_lines:
            if line.startswith("+"):
                if line.startswith("+++"):  # File header
                    colored_diff.append(f"{Colors.BOLD}{Colors.BLUE}{line}{Colors.RESET}")
                else:
                    colored_diff.append(f"{Colors.GREEN}{line}{Colors.RESET}")
            elif line.startswith("-"):
                if line.startswith("---"):  # File header
                    colored_diff.append(f"{Colors.BOLD}{Colors.BLUE}{line}{Colors.RESET}")
                else:
                    colored_diff.append(f"{Colors.RED}{line}{Colors.RESET}")
            elif line.startswith("@@"):
                colored_diff.append(f"{Colors.BLUE}{line}{Colors.RESET}")
            else:
                colored_diff.append(line)
        return "\n".join(colored_diff)

    def _validate_required_write_target_kit(
        self, file_path: str, content: str, package_data: Dict, section_line: int, fix: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate that the package section contains the required writeTarget.kit = true field.
        If fix=True, adds the missing field if needed.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            package_data: Parsed data for the [package] section
            section_line: Line number where the [package] section starts
            fix: Whether to fix found issues

        Returns:
            Tuple of (was_fixed, fixed_content)
        """
        fixed = False
        fixed_content = content

        # Check for existing writeTarget.kit in the raw content
        # This handles cases where the field exists but might not be properly parsed
        lines = content.split("\n")
        in_package_section = False
        field_exists_in_content = False

        for line in lines:
            line_stripped = line.strip()

            # Find package section boundaries
            if line_stripped == "[package]":
                in_package_section = True
                continue
            elif in_package_section and line_stripped.startswith("[") and not line_stripped.startswith('["'):
                # End of package section
                break

            # Check for writeTarget.kit in the package section
            if in_package_section and "writeTarget.kit" in line_stripped:
                field_exists_in_content = True
                break

        # If the field exists in content but not in parsed data, there might be a TOML parse issue
        # We should not add a duplicate in this case
        if field_exists_in_content and "writeTarget.kit" not in package_data:
            self.errors.append(
                ValidationError(
                    file_path,
                    "TOML Parse Issue",
                    "Field 'writeTarget.kit' exists in file but was not properly parsed. Check for duplicate entries or syntax errors.",
                    section_line,
                )
            )
            return False, content

        # Check if writeTarget.kit exists and is set to true
        if not field_exists_in_content and "writeTarget.kit" not in package_data:
            self.errors.append(
                ValidationError(
                    file_path,
                    "Required Field Missing",
                    "Required field 'writeTarget.kit = true' is missing in [package] section",
                    section_line,
                )
            )

            # Fix: Add the missing field if fix=True
            if fix:
                # Find the [package] section in the content
                lines = content.split("\n")
                in_package_section = False
                package_section_end = 0
                package_section_start = 0

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # Find start of package section
                    if line_stripped == "[package]":
                        in_package_section = True
                        package_section_start = i
                        continue

                    # Find end of package section
                    if in_package_section and (line_stripped.startswith("[") and not line_stripped.startswith('["')):
                        package_section_end = i
                        break

                # If we didn't find the end, it's the last section
                if package_section_end == 0:
                    package_section_end = len(lines)

                # Get the package section content
                package_section_lines = lines[package_section_start + 1 : package_section_end]

                # Find proper position to insert writeTarget.kit
                # First try to find writeTarget.platform to place it before that
                insert_index = None

                # Iterate through package section lines to find the best place to insert
                for i, line in enumerate(package_section_lines):
                    line_stripped = line.strip()
                    if "writeTarget.platform" in line_stripped:
                        # Insert right before writeTarget.platform
                        insert_index = package_section_start + 1 + i
                        break
                    elif "feature" in line_stripped or "deprecation" in line_stripped:
                        # These typically come after writeTarget fields
                        insert_index = package_section_start + 1 + i
                        break

                # If we didn't find a specific place, add it at the end of the section
                # but before any empty lines that precede the next section
                if insert_index is None:
                    # Find the last non-empty line in the package section
                    last_content_line = package_section_start
                    for i, line in enumerate(package_section_lines):
                        if line.strip():
                            last_content_line = package_section_start + 1 + i

                    # Insert after the last content line
                    insert_index = last_content_line + 1

                # Add the writeTarget.kit = true field
                lines.insert(insert_index, "writeTarget.kit = true")

                # Clean up spacing:
                # 1. Remove any consecutive empty lines in the package section
                # 2. Ensure exactly one empty line before the next section

                # First recalculate the section end since we inserted a line
                package_section_end += 1

                # Clean up the spacing at the end of the package section
                i = insert_index + 1
                empty_line_count = 0

                # Only process if there are lines after our insert and before the next section
                if i < package_section_end:
                    # Count consecutive empty lines after our insertion
                    while i < package_section_end and not lines[i].strip():
                        empty_line_count += 1
                        i += 1

                    # If we're at the end of the file, remove all empty lines
                    if package_section_end >= len(lines):
                        if empty_line_count > 0:
                            lines = lines[: insert_index + 1] + lines[insert_index + 1 + empty_line_count :]
                    # If there's another section after this, ensure exactly one empty line
                    elif empty_line_count == 0:
                        # No empty line, add one
                        lines.insert(insert_index + 1, "")
                    elif empty_line_count > 1:
                        # Too many empty lines, remove extras
                        lines = lines[: insert_index + 2] + lines[insert_index + 1 + empty_line_count :]

                fixed_content = "\n".join(lines)
                fixed = True
                self.fixes_applied.append("Added required 'writeTarget.kit = true' to [package] section")

        elif field_exists_in_content and package_data.get("writeTarget.kit") is not True:
            self.errors.append(
                ValidationError(
                    file_path,
                    "Invalid Field Value",
                    f"Field 'writeTarget.kit' in [package] section must be set to true, found: {package_data['writeTarget.kit']}",
                    section_line,
                )
            )

            # Fix: Correct the field value if fix=True
            if fix:
                # Find and replace the incorrect value
                lines = content.split("\n")
                in_package_section = False

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # Find start of package section
                    if line_stripped == "[package]":
                        in_package_section = True
                        continue

                    # Find the writeTarget.kit line and fix it
                    if in_package_section and "writeTarget.kit" in line_stripped:
                        # Replace the entire line with the correct value
                        lines[i] = line.split("=")[0] + "= true"
                        break

                    # End of package section
                    if in_package_section and (line_stripped.startswith("[") and not line_stripped.startswith('["')):
                        break

                fixed_content = "\n".join(lines)
                fixed = True
                self.fixes_applied.append("Fixed 'writeTarget.kit' value to true in [package] section")

        return fixed, fixed_content


def find_extension_toml_files(root_dir: str, specific_dir: Optional[str] = None) -> List[str]:
    """
    Find all extension.toml files in the repository.

    Args:
        root_dir: Root directory of the repository
        specific_dir: If provided, only search in this specific directory

    Returns:
        List of paths to extension.toml files
    """
    extension_toml_files = []

    if specific_dir:
        search_dir = os.path.join(root_dir, specific_dir)
        if not os.path.exists(search_dir):
            print(f"Specified directory {specific_dir} does not exist.")
            return []
    else:
        search_dir = root_dir

    for root, dirs, files in os.walk(search_dir):
        if "extension.toml" in files:
            extension_toml_files.append(os.path.join(root, "extension.toml"))

    return extension_toml_files


def main():
    parser = argparse.ArgumentParser(description="Validate extension.toml files structure and order")
    parser.add_argument(
        "--root-dir",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
        help="Root directory of the repository (default: repository root)",
    )
    parser.add_argument("--dir", help="Specific directory to search in (relative to root dir)")
    parser.add_argument(
        "--file", help="Validate a specific extension.toml file (absolute path or relative to current dir)"
    )
    # Fix options
    fix_group = parser.add_argument_group("fix options")
    fix_group.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix all issues (spacing, section order, field order, dependencies order, and adds missing writeTarget.kit = true if --check-write-target is specified)",
    )
    fix_group.add_argument(
        "--fix-whitespace",
        action="store_true",
        help="Fix spacing: add missing blank lines between sections, reduce to exactly one blank line between sections, and remove extra empty lines at start/end of file",
    )
    fix_group.add_argument("--fix-section-order", action="store_true", help="Fix section order issues")
    fix_group.add_argument("--fix-package-order", action="store_true", help="Fix package section field order issues")
    fix_group.add_argument(
        "--fix-dependencies-order", action="store_true", help="Fix dependencies alphabetical order issues"
    )

    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--diagnostics", action="store_true", help="Show diagnostic information for whitespace issues")
    parser.add_argument(
        "--no-diff",
        action="store_true",
        help="Don't show diffs in dry-run mode, only report files that would be changed",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output in diffs")
    parser.add_argument(
        "--check-write-target",
        action="store_true",
        help="Check for and add the required writeTarget.kit = true field to the [package] section",
    )

    args = parser.parse_args()

    # Update color settings based on arguments
    global USE_COLORS
    if args.no_color:
        USE_COLORS = False

    # Set fix modes
    fix_whitespace = args.fix or args.fix_whitespace
    fix_section_order = args.fix or args.fix_section_order
    fix_package_order = args.fix or args.fix_package_order
    fix_dependencies_order = args.fix or args.fix_dependencies_order
    check_write_target = args.check_write_target

    # Settings comments are always checked by default
    check_settings_comments = True

    # Enable verbose output when running without arguments - Removed this default behavior
    # if len(sys.argv) == 1:
    #     args.verbose = True

    validator = ExtensionTomlValidator()
    return process_files(
        args,
        validator,
        fix_whitespace,
        fix_section_order,
        fix_package_order,
        fix_dependencies_order,
        check_settings_comments,
        check_write_target,
    )


def _print_file_diagnostics(file_path: str):
    """
    Print diagnostic information for a file, showing any whitespace or line-ending issues.

    Args:
        file_path: Path to the file to diagnose
    """
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        # Convert to string but keep line endings for analysis
        lines = content.splitlines(True)

        print(f"\nDiagnostic information for {file_path}:")
        print(f"Total bytes: {len(content)}")
        print(f"Total lines: {len(lines)}")

        # Line ending analysis
        cr_count = content.count(b"\r")
        lf_count = content.count(b"\n")
        crlf_count = content.count(b"\r\n")

        print(f"Line endings: CR: {cr_count}, LF: {lf_count}, CRLF: {crlf_count}")

        # Analyze each line
        print("\nLine analysis:")
        for i, line_bytes in enumerate(lines):
            try:
                line = line_bytes.decode("utf-8")
                leading_spaces = len(line) - len(line.lstrip(" "))
                trailing_spaces = len(line.rstrip("\r\n")) - len(line.rstrip(" \r\n"))
                tabs = line.count("\t")

                if i < 10 or line.strip() == "" or " \n" in line or "\t" in line or "\r" in line_bytes:
                    # Print details for first 10 lines, empty lines, or lines with special characters
                    line_repr = repr(line.rstrip("\r\n"))
                    bytes_repr = " ".join([f"{b:02x}" for b in line_bytes])
                    print(
                        f"Line {i+1}: length={len(line_bytes)}, lead_spaces={leading_spaces}, trail_spaces={trailing_spaces}, tabs={tabs}"
                    )
                    print(f"  Repr: {line_repr}")
                    print(f"  Bytes: {bytes_repr}")
            except Exception as e:
                print(f"Line {i+1}: Error decoding: {e}")

    except Exception as e:
        print(f"Error analyzing file: {str(e)}")


def process_files(
    args,
    validator,
    fix_whitespace,
    fix_section_order,
    fix_package_order,
    fix_dependencies_order,
    check_settings_comments,
    check_write_target,
):
    """
    Process files based on the provided arguments.

    Args:
        args: Command line arguments
        validator: Validator instance
        fix_whitespace: Whether to fix whitespace issues
        fix_section_order: Whether to fix section order issues
        fix_package_order: Whether to fix package field order issues
        fix_dependencies_order: Whether to fix dependencies alphabetical order issues
        check_settings_comments: Whether to check for comments above settings
        check_write_target: Whether to check for and add writeTarget.kit field

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    all_errors = []
    fix_count = 0
    files_with_fixes = []

    if args.file:
        # Show diagnostics if requested
        if args.diagnostics:
            _print_file_diagnostics(args.file)

        # Validate a specific file
        file_path = args.file
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return 1

        if args.verbose:
            print(f"Validating {file_path}...")

        errors = validator.validate_file(
            file_path,
            fix_whitespace=fix_whitespace,
            fix_section_order=fix_section_order,
            fix_package_order=fix_package_order,
            fix_dependencies_order=fix_dependencies_order,
            check_settings_comments=check_settings_comments,
            dry_run=args.dry_run,
            show_diff=args.dry_run and not args.no_diff,
            check_write_target=check_write_target,
            verbose=args.verbose,  # Pass verbose flag here
        )
        all_errors.extend(errors)
        if validator.fixes_applied:
            fix_count += 1
            files_with_fixes.append(file_path)
    else:
        # Find and validate all extension.toml files
        toml_files = find_extension_toml_files(args.root_dir, args.dir)

        if not toml_files:
            print(f"No extension.toml files found to validate.")
            return 1

        # Simplify the check here, just use args.verbose
        if args.verbose:
            print(f"Found {len(toml_files)} extension.toml files to validate.")

        for file_path in toml_files:
            # Show diagnostics if requested for problematic files
            if args.diagnostics and "isaacsim.examples.interactive" in file_path:
                _print_file_diagnostics(file_path)

            if args.verbose:
                print(f"Validating {file_path}...")

            # Only show diffs for the first few files in dry-run mode to avoid overwhelming output
            show_diff = args.dry_run and not args.no_diff and fix_count < 5
            errors = validator.validate_file(
                file_path,
                fix_whitespace=fix_whitespace,
                fix_section_order=fix_section_order,
                fix_package_order=fix_package_order,
                fix_dependencies_order=fix_dependencies_order,
                check_settings_comments=check_settings_comments,
                dry_run=args.dry_run,
                show_diff=show_diff,
                check_write_target=check_write_target,
                verbose=args.verbose,  # Pass verbose flag here
            )
            all_errors.extend(errors)
            if validator.fixes_applied:
                fix_count += 1
                files_with_fixes.append(file_path)

    # Print summary
    if all_errors:
        print(f"\nFound {len(all_errors)} validation errors in {len(set(e.file_path for e in all_errors))} files:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    elif fix_count > 0:
        if args.dry_run:
            print(f"\nWould fix issues in {fix_count} files (dry run):")
            for file_path in files_with_fixes:
                print(f"  - {file_path}")
        else:
            print(f"\nFixed issues in {fix_count} files:")
            for file_path in files_with_fixes:
                print(f"  - {file_path}")
    else:
        print("Validation successful. No errors found.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
