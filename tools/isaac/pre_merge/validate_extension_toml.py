# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

r"""Validate and fix extension.toml files to ensure they follow the specified structure and ordering rules.

This comprehensive validation script checks and can automatically fix multiple aspects of extension.toml files:

## Structure and Ordering Validation:
1. **Section Order**: Ensures sections appear in the correct order as defined in SECTION_ORDER
2. **Package Field Order**: Validates that fields in the [package] section follow the expected order
3. **Test Field Order**: Ensures fields in [[test]] sections are properly ordered
4. **Test Section Organization**: Validates that unnamed test sections appear before named ones,
   ensures only one unnamed test section exists, and sorts named test sections alphabetically

## Content Validation:
5. **Dependencies Sorting**: Verifies dependencies in [dependencies] and [[test]] sections are alphabetically sorted.
   Note: Whitespace is automatically re-fixed after dependency reordering to maintain proper section spacing.
6. **Settings Documentation**: Checks that each setting in [settings] sections has descriptive comments above it
7. **Required Fields**: Optionally validates presence of required fields like writeTarget.kit = true
8. **Deprecation Section**: Validates structure and content of [deprecation] sections
9. **Core Section Cleanup**: Removes redundant [core] sections that only contain default values (reloadable = true, order = 0)

## Formatting and Spacing:
10. **Section Spacing**: Ensures exactly one blank line between sections (not more, not less)
11. **File Boundaries**: Removes extra empty lines at start/end of file (allows 0 or 1 empty line at EOF, but not more)
12. **Whitespace Standardization**: Converts lines with only whitespace characters to empty lines
13. **Line Ending Normalization**: Standardizes line endings to Unix format (\n)

## Automatic Fixing Capabilities:
- **--fix**: Applies all available fixes automatically
- **--fix-whitespace**: Fixes spacing and formatting issues
- **--fix-section-order**: Reorders sections and test sections to match standards
- **--fix-package-order**: Reorders fields within [package] and [[test]] sections
- **--fix-dependencies-order**: Sorts dependencies alphabetically
- **--check-write-target**: Adds missing writeTarget.kit = true field when needed

## Advanced Features:
- **Dry Run Mode**: Preview changes without applying them (--dry-run)
- **Diff Display**: Shows unified diffs of proposed changes with color coding
- **Verbose Output**: Detailed logging for debugging and analysis
- **Diagnostics**: Special diagnostic mode for analyzing whitespace and encoding issues
- **Selective Processing**: Can validate specific files or directories
- **Error Reporting**: Comprehensive error messages with line numbers and context

## Platform Support:
- Handles platform-specific settings sections (e.g., settings."filter:platform=linux*")
- Preserves comments and maintains proper TOML structure
- Supports both regular sections [name] and array sections [[name]]

When run without arguments, validates all extension.toml files in the repository.
Supports both validation-only mode and automatic fixing with various granularity levels.
"""

import argparse
import difflib
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

import toml  # type: ignore[import-untyped]
from term_helpers import Colors


@dataclass
class ValidationConfig:
    """Configuration for validation and fixing behavior."""

    fix_whitespace: bool = False
    fix_section_order: bool = False
    fix_package_order: bool = False
    fix_dependencies_order: bool = False
    check_settings_comments: bool = True
    check_write_target: bool = False
    dry_run: bool = False
    show_diff: bool = False
    verbose: bool = False
    use_colors: bool = True

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ValidationConfig":
        """Create config from command-line arguments.

        Args:
            args: Parsed command-line arguments.

        Returns:
            A new ValidationConfig populated from the argument namespace.
        """
        fix_all = args.fix
        return cls(
            fix_whitespace=fix_all or args.fix_whitespace,
            fix_section_order=fix_all or args.fix_section_order,
            fix_package_order=fix_all or args.fix_package_order,
            fix_dependencies_order=fix_all or args.fix_dependencies_order,
            check_write_target=args.check_write_target,
            dry_run=args.dry_run,
            show_diff=args.dry_run and not args.no_diff,
            verbose=args.verbose,
            use_colors=sys.stdout.isatty() and not args.no_color,
        )


@dataclass
class FixResult:
    """Result of a fix operation."""

    was_fixed: bool
    fixed_content: str


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


@dataclass
class ValidationError:
    """Represents a validation error with context."""

    file_path: str
    error_type: str
    message: str
    line_number: Optional[int] = None

    def __str__(self) -> str:
        """Format error message with optional line number.

        Returns:
            Human-readable error string including file path and context.
        """
        location = f" at line {self.line_number}" if self.line_number is not None else ""
        return f"{self.file_path}{location}: {self.error_type}: {self.message}"


class ExtensionTomlValidator:
    """Validate extension.toml files.

    Args:
        config: Validation configuration. If None, uses default config.
    """

    def __init__(self, config: Optional[ValidationConfig] = None):

        self.errors: list[ValidationError] = []
        self.fixes_applied: list[str] = []
        self.config = config or ValidationConfig()

    def _create_line_mapping(self, content: str) -> dict[str, int]:
        """Create a mapping of section names to line numbers.

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

    def _is_section_header(self, line: str) -> tuple[bool, str, str]:
        """Check if a line is a section header and return its type and name.

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

    def _has_blank_line_before(self, lines: list[str], index: int) -> bool:
        """Check if there's a blank line before the given index.

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
        r"""Fix whitespace between sections by ensuring each section is preceded by exactly one blank line.

        If there are more than one consecutive blank lines, reduce them to exactly one.
        Don't add blank lines between comments and the section headers they describe.
        Also ensures at most one empty line at the end of the file (0 or 1 is acceptable).
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
        fixed_lines: list[str] = []
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

        # Remove excessive trailing empty lines (keep at most one)
        trailing_empty_count = 0
        while fixed_lines and not fixed_lines[-1].strip():
            trailing_empty_count += 1
            fixed_lines.pop()

        # If there was at least one trailing empty line, keep exactly one
        # (0 or 1 trailing empty lines is acceptable)
        if trailing_empty_count > 0:
            fixed_lines.append("")
            if trailing_empty_count > 1:
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
            self.fixes_applied.append("Removed excessive empty lines at start and/or end of file")

        # Add a message if we standardized whitespace-only lines
        if removed_whitespace_only_lines:
            self.fixes_applied.append("Standardized lines with only whitespace characters to empty lines")

        return "\n".join(fixed_lines)

    def _check_section_spacing(self, file_path: str, content: str) -> bool:
        """Check if sections are properly separated by blank lines.

        Ensures each section has exactly one blank line before it (not more or less),
        except when a section is preceded by a comment that describes it.
        Also checks for extra empty lines at the start or end of the file.
        The file may end with 0 or 1 empty line (both are acceptable), but not more.

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

        # Check for trailing empty lines (0 or 1 is acceptable, but not more)
        trailing_empty_lines = 0
        for line in reversed(lines):
            if not line.strip():
                trailing_empty_lines += 1
            else:
                break

        if trailing_empty_lines > 1:
            self.errors.append(
                ValidationError(
                    file_path,
                    "File Spacing",
                    f"Excessive empty lines ({trailing_empty_lines}) at the end of the file, should be at most 1",
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

    def _extract_sections(
        self, content: str
    ) -> tuple[list[str], dict[str, str], dict[str, list[str]], dict[str, list[list[str]]]]:
        """Extract sections from TOML content.

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
        array_sections: dict[str, list[list[str]]] = {}

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
    ) -> tuple[int | None, int | None, list[tuple[str, tuple[int, str]]], dict[str, list[tuple[int, str]]]]:
        """Extract fields from the [package] section.

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
                    field_comments: list[tuple[int, str]] = []
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

    def _parse_dependency_line(self, line: str) -> tuple[str, str, str]:
        """Parse a dependency line into its components: value, comma, and comment.

        Args:
            line: A dependency line like '"omni.kit.test", # comment' or '"omni.kit.test"'

        Returns:
            Tuple of (dependency_value, has_comma, comment)
            Example: ('"omni.kit.test"', ',', ' # comment') or ('"omni.kit.test"', '', '')
        """
        line_stripped = line.strip()

        # Find the end of the quoted dependency value
        if not line_stripped.startswith('"'):
            # Not a standard quoted dependency
            return line_stripped, "", ""

        # Find the closing quote
        closing_quote_idx = line_stripped.find('"', 1)
        if closing_quote_idx == -1:
            # Malformed, return as-is
            return line_stripped, "", ""

        # Extract the dependency value (including quotes)
        dep_value = line_stripped[: closing_quote_idx + 1]
        remainder = line_stripped[closing_quote_idx + 1 :]

        # Check for comma and comment in the remainder
        has_comma = ""
        comment = ""

        remainder_stripped = remainder.lstrip()
        if remainder_stripped.startswith(","):
            has_comma = ","
            remainder_stripped = remainder_stripped[1:].lstrip()

        if remainder_stripped.startswith("#"):
            comment = " " + remainder_stripped

        return dep_value, has_comma, comment

    def _format_dependency_line(self, dep_value: str, comment: str, is_last: bool = False) -> str:
        """Format a dependency line with proper comma placement.

        Args:
            dep_value: The dependency value (e.g., '"omni.kit.test"')
            comment: The comment (e.g., ' # some comment' or '')
            is_last: Whether this is the last item in the array (no trailing comma)

        Returns:
            Properly formatted dependency line
        """
        if is_last:
            # Last item should not have a trailing comma
            if comment:
                return f"{dep_value}{comment}"
            else:
                return dep_value
        else:
            # Non-last items should have comma after the value
            if comment:
                return f"{dep_value},{comment}"
            else:
                return f"{dep_value},"

    def _validate_toml_syntax(self, content: str, file_path: str) -> bool:
        """Validate that the content is valid TOML syntax.

        Args:
            content: TOML content to validate
            file_path: Path to file for error reporting

        Returns:
            True if valid, False if there are syntax errors
        """
        try:
            toml.loads(content)
            return True
        except Exception as e:
            self.errors.append(
                ValidationError(
                    file_path,
                    "TOML Syntax Error",
                    f"Invalid TOML syntax: {str(e)}",
                )
            )
            return False

    def _validate_settings_comments(self, file_path: str, content: str) -> bool:
        """Check if each setting in the [settings] section has at least one comment line above it.

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
                and line_stripped != current_settings_section
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
        self, file_path: str, content: str, toml_data: dict, line_mapping: dict[str, int], fix: bool = False
    ) -> FixResult:
        """Validate that dependencies in the [dependencies] section are alphabetically sorted and fix if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            toml_data: Parsed TOML data.
            line_mapping: Mapping of section names to line numbers.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        # If there's no dependencies section, nothing to do
        if "dependencies" not in toml_data or not toml_data["dependencies"]:
            return FixResult(was_fixed=False, fixed_content=content)

        # Extract the dependencies section
        dependencies = toml_data["dependencies"]

        # Check if dependencies are alphabetically sorted
        dependency_names = list(dependencies.keys())
        sorted_dependency_names = sorted(dependency_names)

        has_order_issue = dependency_names != sorted_dependency_names
        if has_order_issue:
            self.errors.append(
                ValidationError(
                    file_path=file_path,
                    error_type="Dependencies Order",
                    message="Dependencies in [dependencies] section should be alphabetically sorted",
                    line_number=line_mapping.get("dependencies", 0),
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

                # Validate TOML syntax after fixing
                if not self._validate_toml_syntax(fixed_content, file_path):
                    # If validation fails, return original content
                    self.fixes_applied.append("ERROR: Failed to fix dependencies - invalid TOML syntax after changes")
                    return FixResult(was_fixed=False, fixed_content=content)

                self.fixes_applied.append("Sorted dependencies alphabetically in [dependencies] section")
                return FixResult(was_fixed=True, fixed_content=fixed_content)

        return FixResult(was_fixed=False, fixed_content=content)

    def _validate_and_fix_test_dependencies_order(
        self, file_path: str, content: str, toml_data: dict, line_mapping: dict[str, int], fix: bool = False
    ) -> FixResult:
        """Validate that dependencies in the [[test]] section(s) are alphabetically sorted and fix if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            toml_data: Parsed TOML data.
            line_mapping: Mapping of section names to line numbers.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        # If there's no test section, nothing to do
        if "test" not in toml_data or not isinstance(toml_data["test"], list) or not toml_data["test"]:
            return FixResult(was_fixed=False, fixed_content=content)

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

                    # Parse dependency values with their comments
                    dependencies = []
                    for line in dep_lines[1 : deps_end - deps_start]:  # Skip start and end lines
                        line_stripped = line.strip()
                        if line_stripped and line_stripped != "]" and not line_stripped.startswith("#"):
                            # Parse the dependency line to separate value, comma, and comment
                            dep_value, _, comment = self._parse_dependency_line(line_stripped)
                            dependencies.append((dep_value, comment, line))

                    # Sort dependencies by their values
                    sorted_deps = sorted(dependencies, key=lambda x: x[0])

                    # Create new dependency block with proper comma placement
                    new_deps = [dep_lines[0]]  # Start line with "dependencies = ["
                    for i, (dep_value, comment, _) in enumerate(sorted_deps):
                        is_last = i == len(sorted_deps) - 1
                        formatted_line = self._format_dependency_line(dep_value, comment, is_last)
                        new_deps.append("    " + formatted_line)
                    new_deps.append(dep_lines[-1])  # End line with "]"

                    # Replace in section lines
                    section_lines[deps_start : deps_end + 1] = new_deps

                    # Replace in original lines
                    lines[section_start:section_end] = section_lines

            # Rebuild content
            fixed_content = "\n".join(lines)

            # Validate TOML syntax after fixing
            if not self._validate_toml_syntax(fixed_content, file_path):
                # If validation fails, return original content
                self.fixes_applied.append("ERROR: Failed to fix dependencies - invalid TOML syntax after changes")
                return FixResult(was_fixed=False, fixed_content=content)

            self.fixes_applied.append("Sorted dependencies alphabetically in [[test]] section(s)")
            return FixResult(was_fixed=True, fixed_content=fixed_content)

        return FixResult(was_fixed=False, fixed_content=content)

    def validate_file(self, file_path: str, config: Optional[ValidationConfig] = None) -> list[ValidationError]:
        """Validate a TOML file against the extension.toml style guide.

        Args:
            file_path: Path to the TOML file.
            config: Validation configuration. If None, uses the instance config.

        Returns:
            List of validation errors found.
        """
        # Use provided config or fall back to instance config
        config = config or self.config

        if config.verbose:
            print(f"DEBUG: Starting validation of {file_path}")
        if not os.path.exists(file_path):
            self.errors.append(ValidationError(file_path, "File Not Found", f"File {file_path} does not exist"))
            return self.errors

        try:
            with open(file_path) as f:
                content = f.read()
        except Exception as e:
            self.errors.append(ValidationError(file_path, "File Read Error", str(e)))
            return self.errors

        # Reset the errors list for this file
        self.errors = []
        self.fixes_applied = []

        # Validate TOML syntax first
        try:
            toml_data = toml.loads(content)
        except Exception as e:
            self.errors.append(ValidationError(file_path, "TOML Parse Error", str(e)))
            # Try to give more specific error for missing commas in arrays
            if "Expected" in str(e) or "Invalid" in str(e):
                # Check for common patterns of missing commas
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    # Check if this looks like a dependency without a trailing comma
                    if (
                        line_stripped.startswith('"')
                        and line_stripped.endswith('"')
                        and i + 1 < len(lines)
                        and lines[i + 1].strip().startswith('"')
                    ):
                        self.errors.append(
                            ValidationError(
                                file_path,
                                "Possible Missing Comma",
                                f"Line {i+1} may be missing a trailing comma: {line_stripped}",
                                i + 1,
                            )
                        )
            return self.errors

        # Create a mapping of section names to line numbers for error reporting
        line_mapping = self._create_line_mapping(content)

        # Track if any fixes were applied
        fixed = False
        fixed_content = content

        # Check for redundant [core] section and fix if requested
        if config.fix_section_order:  # Reuse fix_section_order flag for core section removal
            core_result = self._validate_and_fix_core_section(file_path, fixed_content, toml_data, line_mapping, True)
            if core_result.was_fixed:
                fixed = True
                fixed_content = core_result.fixed_content
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check for whitespace issues and fix if requested
        if config.fix_whitespace:
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
        if config.fix_section_order:
            sections_result = self._validate_and_fix_section_order(
                file_path, fixed_content, toml_data, line_mapping, True
            )
            if sections_result.was_fixed:
                fixed = True
                fixed_content = sections_result.fixed_content
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check [package] section
        if "package" in toml_data:
            # Check and fix [package] field order
            if config.fix_package_order:
                package_result = self._validate_and_fix_package_fields(
                    file_path, fixed_content, toml_data["package"], line_mapping.get("package", 0), True
                )
                if package_result.was_fixed:
                    fixed = True
                    fixed_content = package_result.fixed_content
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

            # Check for appropriate writeTarget.kit presence
            if config.check_write_target:
                write_target_result = self._validate_required_write_target_kit(
                    file_path, fixed_content, toml_data["package"], line_mapping.get("package", 0), True
                )
                if write_target_result.was_fixed:
                    fixed = True
                    fixed_content = write_target_result.fixed_content
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

        # Check spacing between sections
        self._check_section_spacing(file_path, fixed_content)

        # Check for redundant [core] section (validation only when not fixing)
        if not config.fix_section_order:
            self._validate_and_fix_core_section(file_path, fixed_content, toml_data, line_mapping, False)

        # Check that [package] is the first section if there's no [core] section
        self._validate_package_first_section(file_path, fixed_content, toml_data)

        # Check [settings] section comments
        if config.check_settings_comments and "settings" in toml_data:
            self._validate_settings_comments(file_path, fixed_content)

        # Check and fix test section field order
        if "test" in toml_data and config.fix_package_order:  # Reuse fix_package_order flag for test order fixes
            test_fields_result = self._validate_and_fix_test_fields(
                file_path, fixed_content, toml_data, line_mapping, True
            )

            if test_fields_result.was_fixed:
                fixed = True
                fixed_content = test_fields_result.fixed_content

        # Check and fix test section order
        has_multiple_unnamed, has_startup_order_issue = self._validate_test_section_order(file_path, fixed_content)

        if (has_multiple_unnamed or has_startup_order_issue) and config.fix_section_order:
            test_order_result = self._validate_and_fix_test_section_order(file_path, fixed_content, True)
            if test_order_result.was_fixed:
                fixed = True
                fixed_content = test_order_result.fixed_content
                # Reload TOML data and line mapping since content has changed
                try:
                    toml_data = toml.loads(fixed_content)
                    line_mapping = self._create_line_mapping(fixed_content)
                except Exception:
                    pass

        # Check and fix dependencies alphabetical order
        if config.fix_dependencies_order:
            deps_were_fixed = False

            # Fix dependencies section
            if "dependencies" in toml_data:
                deps_result = self._validate_and_fix_dependencies_order(
                    file_path, fixed_content, toml_data, line_mapping, True
                )
                if deps_result.was_fixed:
                    fixed = True
                    fixed_content = deps_result.fixed_content
                    deps_were_fixed = True
                    # Reload TOML data and line mapping since content has changed
                    try:
                        toml_data = toml.loads(fixed_content)
                        line_mapping = self._create_line_mapping(fixed_content)
                    except Exception:
                        pass

            # Fix test dependencies
            if "test" in toml_data:
                test_deps_result = self._validate_and_fix_test_dependencies_order(
                    file_path, fixed_content, toml_data, line_mapping, True
                )
                if test_deps_result.was_fixed:
                    fixed = True
                    fixed_content = test_deps_result.fixed_content
                    deps_were_fixed = True

            # Re-run whitespace fix after dependency reordering to ensure proper spacing
            if config.fix_whitespace and deps_were_fixed:
                fixed_whitespace = self._fix_whitespace(fixed_content)
                if fixed_whitespace != fixed_content:
                    fixed_content = fixed_whitespace
                    # No need to reload TOML data since whitespace changes don't affect parsing

        # If the file was fixed, apply changes
        if fixed and not config.dry_run:
            self._apply_fixes(file_path, fixed_content, toml_data)
        elif fixed and config.dry_run:
            self._report_fixes(file_path, content, fixed_content, config.show_diff)

        return self.errors

    def _apply_fixes(self, file_path: str, fixed_content: str, original_toml_data: dict) -> None:
        """Apply fixes to the file and verify the result.

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
        """Report fixes that would be applied in dry-run mode.

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
        self, file_path: str, content: str, toml_data: dict, line_mapping: dict[str, int], fix: bool = False
    ) -> FixResult:
        """Validate that sections appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            toml_data: Parsed TOML data.
            line_mapping: Mapping of section names to line numbers.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        # Extract sections from the content to preserve order
        sections, section_types, regular_sections, array_sections = self._extract_sections(content)

        # Check for order issues
        has_order_issue = self._check_section_order(file_path, sections, line_mapping)

        # If there's an order issue, reorder the sections
        if has_order_issue and fix:
            result = self._reorder_sections(content, regular_sections, array_sections)
            if result.was_fixed:
                # Validate TOML syntax after fixing
                if not self._validate_toml_syntax(result.fixed_content, file_path):
                    # If validation fails, return original content
                    self.fixes_applied.append("ERROR: Failed to reorder sections - invalid TOML syntax after changes")
                    return FixResult(was_fixed=False, fixed_content=content)
            return result

        return FixResult(was_fixed=False, fixed_content=content)

    def _check_section_order(self, file_path: str, sections: list[str], line_mapping: dict[str, int]) -> bool:
        """Check if sections are in the correct order.

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
        self, content: str, regular_sections: dict[str, list[str]], array_sections: dict[str, list[list[str]]]
    ) -> FixResult:
        """Reorder sections according to the expected order.

        Args:
            content: Original content.
            regular_sections: Regular sections extracted from content.
            array_sections: Array sections extracted from content.

        Returns:
            FixResult indicating whether content was fixed and the new content.
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
        return FixResult(was_fixed=True, fixed_content=new_content)

    def _validate_and_fix_package_fields(
        self, file_path: str, content: str, package_data: dict, section_line: int, fix: bool = False
    ) -> FixResult:
        """Validate that fields in the [package] section appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            package_data: Parsed data for the [package] section.
            section_line: Line number where the [package] section starts.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
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
                assert package_section_start is not None
                assert package_section_end is not None
                result = self._reorder_package_fields(
                    content, field_lines, package_section_comments, package_section_start, package_section_end
                )
                if result.was_fixed:
                    # Validate TOML syntax after fixing
                    if not self._validate_toml_syntax(result.fixed_content, file_path):
                        # If validation fails, return original content
                        self.fixes_applied.append(
                            "ERROR: Failed to reorder package fields - invalid TOML syntax after changes"
                        )
                        return FixResult(was_fixed=False, fixed_content=content)
                return result

        except Exception as e:
            self.errors.append(
                ValidationError(
                    file_path=file_path,
                    error_type="Error",
                    message=f"Error validating package fields: {str(e)}",
                    line_number=section_line,
                )
            )

        return FixResult(was_fixed=False, fixed_content=content)

    def _check_package_field_order(
        self, file_path: str, field_lines: list[tuple[str, tuple[int, str]]], section_line: int
    ) -> bool:
        """Check if package fields are in the correct order.

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
        field_lines: list[tuple[str, tuple[int, str]]],
        package_section_comments: dict[str, list[tuple[int, str]]],
        package_section_start: int,
        package_section_end: int,
    ) -> FixResult:
        """Reorder fields in the package section.

        Args:
            content: Original content.
            field_lines: List of field names and their lines.
            package_section_comments: Comments for each field.
            package_section_start: Start line of package section.
            package_section_end: End line of package section.

        Returns:
            FixResult indicating whether content was fixed and the new content.
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
        return FixResult(was_fixed=True, fixed_content=new_content)

    def _validate_deprecation_section(self, file_path: str, deprecation_data: dict, section_line: int) -> None:
        """Validate the [deprecation] section.

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
        self, file_path: str, content: str, toml_data: dict, line_mapping: dict[str, int], fix: bool = False
    ) -> FixResult:
        """Validate that fields in [[test]] sections appear in the correct order and fix if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            toml_data: Parsed TOML data.
            line_mapping: Mapping of section names to line numbers.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        # If there's no test section, nothing to do
        if "test" not in toml_data or not isinstance(toml_data["test"], list) or not toml_data["test"]:
            return FixResult(was_fixed=False, fixed_content=content)

        # Extract the test sections - this will automatically filter out empty test sections
        test_section_lines, array_section_content, _, _ = self._extract_test_sections(content)  # Fix unpacking

        if not test_section_lines or not array_section_content:
            return FixResult(was_fixed=False, fixed_content=content)

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
                            except Exception:
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
            # Validate TOML syntax after fixing
            if not self._validate_toml_syntax(fixed_content, file_path):
                # If validation fails, return original content
                self.fixes_applied.append("ERROR: Failed to reorder test fields - invalid TOML syntax after changes")
                return FixResult(was_fixed=False, fixed_content=content)
            return FixResult(was_fixed=True, fixed_content=fixed_content)

        return FixResult(was_fixed=False, fixed_content=content)

    def _extract_test_sections(self, content: str) -> tuple[list[int], list[list[str]], int, int]:
        """Extract all [[test]] sections from the content.

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
        current_section_lines: list[str] = []
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
            elif in_test_section and (
                (line_stripped.startswith("[") and not line_stripped.startswith("[["))
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

    def _validate_test_section_order(self, file_path: str, content: str) -> tuple[bool, bool]:
        """Validate test section naming and ordering constraints.

        1. There is only one unnamed test section
        2. The "startup" test section appears first among all test sections

        Args:
            file_path: Path to the file being validated
            content: The file content to check

        Returns:
            Tuple of (has_multiple_unnamed_sections, has_startup_order_issue)
        """
        if self.config.verbose:
            print(f"DEBUG: Validating test section order in {file_path}")
        lines = content.split("\n")

        # Extract all test sections with their names and line numbers
        test_sections_info = []  # List of tuples: (start_line, has_name, name_value)
        in_test_section = False
        current_section_start = -1
        current_section_has_name = False
        current_section_name = ""

        # Find all test sections and whether they have a name field
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Start of a test section
            if line_stripped == "[[test]]":
                # If we were already in a section, save the previous one
                if in_test_section:
                    test_sections_info.append((current_section_start, current_section_has_name, current_section_name))

                # Start tracking the new section
                in_test_section = True
                current_section_start = i
                current_section_has_name = False
                current_section_name = ""
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
                    # Extract the name value
                    try:
                        name_value = line_stripped.split("=", 1)[1].strip()
                        if name_value.startswith('"') and name_value.endswith('"'):
                            name_value = name_value[1:-1]
                        current_section_name = name_value
                    except Exception:
                        pass
                # End of test section block (start of a new, non-test section)
                elif (line_stripped.startswith("[") and not line_stripped.startswith("[[")) or (
                    line_stripped.startswith("[[") and not line_stripped.startswith("[[test]]")
                ):
                    # if self._verbose: # <<< Optional: Add verbose check here if needed
                    #     print(f"DEBUG: End of section at line {i}")
                    # Save the last test section info
                    test_sections_info.append((current_section_start, current_section_has_name, current_section_name))
                    in_test_section = False  # Stop processing test sections
                    break

        # Add the last section if we reached the end of the file while in a test section
        if in_test_section:
            test_sections_info.append((current_section_start, current_section_has_name, current_section_name))

        # Now check for issues based on the collected info
        unnamed_sections = [section for section in test_sections_info if not section[1]]
        startup_sections = [section for section in test_sections_info if section[2] == "startup"]
        non_startup_sections = [section for section in test_sections_info if section[2] != "startup"]

        if self.config.verbose:
            print(f"DEBUG: test_sections_info = {test_sections_info}")
            print(f"DEBUG: unnamed_sections = {unnamed_sections}")
            print(f"DEBUG: startup_sections = {startup_sections}")
            print(f"DEBUG: non_startup_sections = {non_startup_sections}")

        has_multiple_unnamed_sections = len(unnamed_sections) > 1
        has_startup_order_issue = False

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

        # Check if "startup" test section comes first among ALL test sections
        if startup_sections and non_startup_sections:
            # Find the line number of the first startup section
            min_startup_line = min(section[0] for section in startup_sections)
            # Find the line number of the first non-startup section (named or unnamed)
            min_non_startup_line = min(section[0] for section in non_startup_sections)

            if self.config.verbose:
                print(f"DEBUG: min_startup_line={min_startup_line}, min_non_startup_line={min_non_startup_line}")

            if min_startup_line > min_non_startup_line:
                has_startup_order_issue = True
                # Find the first non-startup section that appears before startup
                offending_section = min(
                    (s for s in non_startup_sections if s[0] < min_startup_line), key=lambda x: x[0]
                )
                section_desc = f"'{offending_section[2]}'" if offending_section[2] else "unnamed"
                self.errors.append(
                    ValidationError(
                        file_path,
                        "Test Section Order",
                        f"[[test]] section {section_desc} at line {offending_section[0] + 1} appears before 'startup' section at line {min_startup_line + 1}. The 'startup' test section must come first among all test sections.",
                        offending_section[0] + 1,
                    )
                )

        if self.config.verbose:
            print(
                f"DEBUG: has_multiple_unnamed_sections={has_multiple_unnamed_sections}, has_startup_order_issue={has_startup_order_issue}"
            )

        return has_multiple_unnamed_sections, has_startup_order_issue

    def _validate_and_fix_test_section_order(self, file_path: str, content: str, fix: bool = False) -> FixResult:
        """Validate and fix the order of test sections.

        1. Ensure only one unnamed test section (keeps the first one found)
        2. Ensure the "startup" test section appears first among all test sections
        3. Sort remaining test sections alphabetically by their 'name' field (unnamed sections last).

        Args:
            file_path: Path to the file being validated.
            content: Raw TOML content.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        has_multiple_unnamed_sections, has_startup_order_issue = self._validate_test_section_order(file_path, content)

        # If there are no issues or we're not fixing, just return
        if (not has_multiple_unnamed_sections and not has_startup_order_issue) or not fix:
            return FixResult(was_fixed=False, fixed_content=content)

        if self.config.verbose:
            print(
                f"DEBUG: Fixing issues: multi_unnamed={has_multiple_unnamed_sections}, startup_order_issue={has_startup_order_issue}"
            )

        lines = content.split("\n")

        # Extract all test sections with content, name, and track block boundaries
        section_lines, section_contents, block_start, block_end = self._extract_test_sections(content)

        # If no test sections found, something is wrong (or file changed)
        if block_start == -1:
            return FixResult(was_fixed=False, fixed_content=content)

        unnamed_test_sections = []
        named_test_sections = []  # List of tuples: (section_content_list, name_value)

        for section_content in section_contents:
            has_name = False
            section_name: str | None = ""
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
                    except Exception:
                        pass  # Ignore potential errors in extracting name
                    break  # Found name, no need to check further lines in this section

            if has_name:
                if self.config.verbose:
                    print(f"DEBUG: Found named section: {section_name}")
                named_test_sections.append((section_content, section_name))
            else:
                if self.config.verbose:
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

        # Sort named test sections: "startup" first, then alphabetically by name
        # Using a tuple key: (0, name) for "startup", (1, name) for others
        named_test_sections.sort(key=lambda x: (0 if x[1] == "startup" else 1, x[1]))

        # Rebuild the block content
        # Order: "startup" first, then other named sections alphabetically, then unnamed section(s)
        reordered_block_lines: list[str] = []

        # Add named sections first (startup will be first due to sorting)
        for i, (section_content, _) in enumerate(named_test_sections):
            # Add a blank line before this section if it's not the first section in the block
            if i > 0:
                # Check if the last line added wasn't already blank
                if reordered_block_lines and reordered_block_lines[-1].strip():
                    reordered_block_lines.append("")
            reordered_block_lines.extend(section_content)

        # Add the single unnamed section after named sections (if it exists)
        if kept_unnamed_section:
            # Add a blank line before the unnamed section if there are named sections
            if reordered_block_lines and reordered_block_lines[-1].strip():
                reordered_block_lines.append("")
            reordered_block_lines.extend(kept_unnamed_section)

        # Combine the parts of the file
        # Content before the block + reordered block + content after the block
        fixed_content_lines = lines[:block_start] + reordered_block_lines + lines[block_end:]

        # Extract original names from section_contents to check if order changed
        original_named_names = []
        for section_content in section_contents:
            section_name = None
            for line in section_content:
                line_stripped = line.strip()
                if line_stripped.startswith("name") and "=" in line_stripped and not line_stripped.endswith("["):
                    try:
                        name_value = line_stripped.split("=", 1)[1].strip().strip('"')
                        section_name = name_value
                    except Exception:
                        pass
                    break
            if section_name is not None:
                original_named_names.append(section_name)

        # Sort with "startup" first, then alphabetically
        sorted_original_names = sorted(original_named_names, key=lambda x: (0 if x == "startup" else 1, x))

        # Add messages about fixes
        if has_multiple_unnamed_sections:
            # Message already added when selecting the kept section
            pass
        if has_startup_order_issue:
            self.fixes_applied.append(
                "Reordered [[test]] sections ('startup' first, then other named alphabetically, then unnamed)"
            )
        elif named_test_sections and original_named_names != sorted_original_names:
            self.fixes_applied.append("Sorted named [[test]] sections ('startup' first, then alphabetically)")

        if self.config.verbose:
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
        final_fixes: list[str] = []
        seen_ws_fixes = set()
        for fix_msg in reversed(self.fixes_applied):
            if fix_msg in ws_fixes:
                if fix_msg not in seen_ws_fixes:
                    final_fixes.insert(0, fix_msg)
                    seen_ws_fixes.add(fix_msg)
            else:
                final_fixes.insert(0, fix_msg)
        self.fixes_applied = final_fixes

        if self.config.verbose:
            print(f"DEBUG: Original content length: {len(content)}, Fixed content length: {len(fixed_content)}")

        # Return True if any structural change was made
        was_fixed = bool(
            has_multiple_unnamed_sections
            or has_startup_order_issue
            or (named_test_sections and original_named_names != sorted_original_names)
        )

        # Validate TOML syntax if content was modified
        if was_fixed:
            if not self._validate_toml_syntax(fixed_content, file_path):
                # If validation fails, return original content
                self.fixes_applied.append("ERROR: Failed to reorder test sections - invalid TOML syntax after changes")
                return FixResult(was_fixed=False, fixed_content=content)

        return FixResult(was_fixed=was_fixed, fixed_content=fixed_content)

    def _check_test_field_order(self, file_path: str, test_section: dict, section_line: int) -> bool:
        """Check if fields in a [[test]] section are in the correct order.

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
        self, content: str, test_sections: list[dict], section_lines: list[int], section_contents: list[list[str]]
    ) -> str:
        """Reorder fields in test sections to match the expected order.

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
            parsed_fields: dict[str, dict[str, Any]] = {}

            # Keep track of non-field lines (comments, whitespace) to preserve them
            non_field_lines = []

            # Extract all fields and their original formatting
            in_array_field = False
            current_field: str | None = None
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
                    assert current_field is not None
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
        """Generate a unified diff between the original and fixed content.

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
        if self.config.use_colors:
            return self._colorize_diff(diff_lines)
        else:
            return "\n".join(diff_lines)

    def _colorize_diff(self, diff_lines: list[str]) -> str:
        """Add color formatting to diff lines.

        Args:
            diff_lines: List of diff lines.

        Returns:
            Colored diff as a string.
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
        self, file_path: str, content: str, package_data: dict, section_line: int, fix: bool = False
    ) -> FixResult:
        """Validate that the package section contains the required writeTarget.kit = true field.

        If fix=True, adds the missing field if needed.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            package_data: Parsed data for the [package] section.
            section_line: Line number where the [package] section starts.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
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
            return FixResult(was_fixed=False, fixed_content=content)

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
                self.fixes_applied.append("Fixed 'writeTarget.kit' value to true in [package] section")
                return FixResult(was_fixed=True, fixed_content=fixed_content)

        return FixResult(was_fixed=False, fixed_content=fixed_content)

    def _validate_and_fix_core_section(
        self, file_path: str, content: str, toml_data: dict, line_mapping: dict[str, int], fix: bool = False
    ) -> FixResult:
        """Validate the [core] section and remove it if it only contains default values.

        If the [core] section only contains reloadable = true and order = 0 (or just one of these),
        it should be removed as these are default values.

        Args:
            file_path: Path to the TOML file.
            content: Raw TOML content.
            toml_data: Parsed TOML data.
            line_mapping: Mapping of section names to line numbers.
            fix: Whether to fix found issues.

        Returns:
            FixResult indicating whether content was fixed and the new content.
        """
        # If there's no core section, nothing to do
        if "core" not in toml_data:
            return FixResult(was_fixed=False, fixed_content=content)

        core_data = toml_data["core"]

        # Check if the core section only contains default values
        has_only_defaults = True
        non_default_fields = []

        for key, value in core_data.items():
            if key == "reloadable" and value is True:
                continue  # This is a default value
            elif key == "order" and value == 0:
                continue  # This is a default value
            else:
                # This is a non-default field
                has_only_defaults = False
                non_default_fields.append(f"{key} = {value}")

        # If the section only contains default values, it should be removed
        if has_only_defaults and core_data:  # Make sure it's not empty
            self.errors.append(
                ValidationError(
                    file_path,
                    "Redundant Core Section",
                    f"[core] section contains only default values (reloadable = true, order = 0) and should be removed",
                    line_mapping.get("core", 0),
                )
            )

            if fix:
                # Remove the [core] section from the content
                lines = content.split("\n")
                core_section_start = None
                core_section_end = None

                # Find the [core] section boundaries
                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    if line_stripped == "[core]":
                        core_section_start = i
                        continue
                    elif core_section_start is not None and (
                        (line_stripped.startswith("[") and not line_stripped.startswith("[["))
                        or line_stripped.startswith("[[")
                    ):
                        core_section_end = i
                        break

                # If we didn't find the end, it goes to the end of file
                if core_section_end is None:
                    core_section_end = len(lines)

                if core_section_start is not None:
                    # Remove the core section and any trailing empty lines
                    # Also remove any leading empty lines that would be left behind
                    section_start = core_section_start
                    section_end = core_section_end

                    # Check if there are empty lines before the core section that should also be removed
                    while section_start > 0 and not lines[section_start - 1].strip():
                        section_start -= 1

                    # Remove the section
                    fixed_content = "\n".join(lines[:section_start] + lines[section_end:])

                    # Clean up any excessive whitespace that might result
                    fixed_content = self._fix_whitespace(fixed_content)

                    self.fixes_applied.append("Removed redundant [core] section with default values")
                    return FixResult(was_fixed=True, fixed_content=fixed_content)

        return FixResult(was_fixed=False, fixed_content=content)

    def _validate_package_first_section(self, file_path: str, content: str, toml_data: dict) -> None:
        """Validate that [package] is the first section if there's no [core] section.

        Args:
            file_path: Path to the TOML file
            content: Raw TOML content
            toml_data: Parsed TOML data
        """
        # If there's a [core] section, this check doesn't apply
        if "core" in toml_data:
            return

        # If there's no [package] section, this check doesn't apply
        if "package" not in toml_data:
            return

        lines = content.split("\n")
        first_section_found = None
        first_section_line = None

        # Find the first section in the file
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Check if this is a section header
            is_header, section_name, section_type = self._is_section_header(line)
            if is_header:
                first_section_found = section_name
                first_section_line = i + 1
                break

        # If the first section is not [package], report an error
        if first_section_found and first_section_found != "package":
            self.errors.append(
                ValidationError(
                    file_path,
                    "Package Section Order",
                    f"[package] section must be the first section when there is no [core] section. Found [{first_section_found}] first at line {first_section_line}",
                    first_section_line,
                )
            )


def find_extension_toml_files(root_dir: str, specific_dir: Optional[str] = None) -> list[str]:
    """Find all extension.toml files in the repository.

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
    """Parse arguments, validate extension.toml files, and report results.

    Returns:
        0 on success, 1 if validation errors were found.
    """
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

    # Create validation configuration from arguments
    config = ValidationConfig.from_args(args)

    # Create validator with config
    validator = ExtensionTomlValidator(config)

    return process_files(args, validator, config)


def _print_file_diagnostics(file_path: str):
    """Print diagnostic information for a file, showing any whitespace or line-ending issues.

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

                if i < 10 or line.strip() == "" or " \n" in line or "\t" in line or b"\r" in line_bytes:
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


def process_files(args: argparse.Namespace, validator: ExtensionTomlValidator, config: ValidationConfig) -> int:
    """Process files based on the provided arguments.

    Args:
        args: Command line arguments.
        validator: Validator instance.
        config: Validation configuration.

    Returns:
        Exit code (0 for success, 1 for errors).
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

        if config.verbose:
            print(f"Validating {file_path}...")

        errors = validator.validate_file(file_path, config)
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

        # Simplify the check here, just use config.verbose
        if config.verbose:
            print(f"Found {len(toml_files)} extension.toml files to validate.")

        for file_path in toml_files:
            # Show diagnostics if requested for problematic files
            if args.diagnostics and "isaacsim.examples.interactive" in file_path:
                _print_file_diagnostics(file_path)

            if config.verbose:
                print(f"Validating {file_path}...")

            # Only show diffs for the first few files in dry-run mode to avoid overwhelming output
            # Update config for this specific file
            file_config = ValidationConfig(
                fix_whitespace=config.fix_whitespace,
                fix_section_order=config.fix_section_order,
                fix_package_order=config.fix_package_order,
                fix_dependencies_order=config.fix_dependencies_order,
                check_settings_comments=config.check_settings_comments,
                check_write_target=config.check_write_target,
                dry_run=config.dry_run,
                show_diff=config.dry_run and not args.no_diff and fix_count < 5,
                verbose=config.verbose,
                use_colors=config.use_colors,
            )
            errors = validator.validate_file(file_path, file_config)
            all_errors.extend(errors)
            if validator.fixes_applied:
                fix_count += 1
                files_with_fixes.append(file_path)

    # Print summary
    if all_errors:
        print(f"\nFound {len(all_errors)} validation errors in {len({e.file_path for e in all_errors})} files:")
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
