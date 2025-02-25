#!/usr/bin/env python3
import argparse
import datetime
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import tomli, but provide a fallback if it fails
try:
    import tomli
except ImportError:
    print("Warning: tomli not installed. Using built-in fallback for TOML parsing.")
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

    tomli = TomliWrapper()

# Try to import enchant, but provide a fallback if it fails
try:
    import enchant

    HAS_ENCHANT = True
except (ImportError, AttributeError):
    HAS_ENCHANT = False
    print("Warning: PyEnchant not properly installed. Spell checking will be limited.")

# Try to import packaging.version, but provide a fallback if it fails
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


class SimpleSpellChecker:
    """A simple fallback spell checker when enchant is not available."""

    def __init__(self):
        self.dictionary = set()
        # Try to load a simple word list if available
        try:
            with open("/usr/share/dict/words", "r") as f:
                self.dictionary = set(word.strip().lower() for word in f)
        except FileNotFoundError:
            print("Warning: No dictionary file found. Spell checking will be disabled.")

    def check(self, word):
        """Check if a word is correctly spelled."""
        return word.lower() in self.dictionary


class ChangelogValidator:
    def __init__(
        self,
        file_path: str,
        check_extension_version: bool = False,
        require_unreleased: bool = True,
        require_references: bool = True,
        check_spelling: bool = True,
        verbose: bool = False,
    ):
        self.file_path = file_path
        self.lines = []
        self.errors = []
        self.check_extension_version = check_extension_version
        self.require_unreleased = require_unreleased
        self.require_references = require_references
        self.check_spelling = check_spelling
        self.verbose = verbose

        # Initialize the spell checker only if spelling check is enabled
        self.spell_check_enabled = False
        if check_spelling:
            if HAS_ENCHANT:
                try:
                    self.dictionary = enchant.Dict("en_US")
                    self.spell_check_enabled = True
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Could not initialize enchant dictionary: {e}")
                    self.dictionary = SimpleSpellChecker()
                    self.spell_check_enabled = bool(self.dictionary.dictionary)
            else:
                self.dictionary = SimpleSpellChecker()
                self.spell_check_enabled = bool(self.dictionary.dictionary)

        # Add common technical terms to ignore during spell checking
        self.technical_terms = {
            "api",
            "apis",
            "config",
            "configs",
            "changelog",
            "deprecate",
            "deprecated",
            "deprecating",
            "deprecation",
            "github",
            "json",
            "yaml",
            "xml",
            "ui",
            "ux",
            "frontend",
            "backend",
            "refactor",
            "refactored",
            "refactoring",
            "bugfix",
            "bugfixes",
            "unreleased",
            "semver",
            "versioning",
            "toml",
            "npm",
            "cli",
            "sdk",
            "url",
            "urls",
            "http",
            "https",
            "css",
            "html",
            "js",
            "javascript",
            "typescript",
            "py",
            "python",
            "md",
            "markdown",
            "repo",
            "repos",
            "dev",
            "webpack",
            "runtime",
            "async",
            "sync",
            "param",
            "params",
            "middleware",
            "codebase",
            "readme",
            "eslint",
            "linter",
            "linting",
            "npm",
            "codeblock",
            "codeblocks",
            "changelog",
            "changelogs",
            "omni",
            "isaac",
            "nvidia",
            "sim",
        }

        # Standard sections in a Keep a Changelog file - with proper capitalization
        self.valid_sections = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

    def read_file(self) -> bool:
        """Read the changelog file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
            return True
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

    def validate(self) -> bool:
        """Run all validation checks."""
        if not self.read_file():
            return False

        self.validate_header()
        self.validate_versions_and_dates()
        self.validate_sections()
        self.validate_bullet_points()

        if self.check_spelling and self.spell_check_enabled:
            self.validate_spelling()

        if self.check_extension_version:
            self.validate_extension_version()

        return len(self.errors) == 0

    def validate_header(self) -> None:
        """Validate the changelog header."""
        if not self.lines:
            self.errors.append("File is empty")
            return

        if not self.lines[0].strip().startswith("# Changelog"):
            self.errors.append("File should start with '# Changelog'")

        # Only check for references if required
        if self.require_references:
            # Check for Keep a Changelog reference
            found_format_reference = False
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if "keepachangelog.com" in line.lower():
                    found_format_reference = True
                    break

            if not found_format_reference:
                self.errors.append("Missing reference to Keep a Changelog format")

            # Check for Semantic Versioning reference
            found_semver_reference = False
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if "semver" in line.lower() or "semantic versioning" in line.lower():
                    found_semver_reference = True
                    break

            if not found_semver_reference:
                self.errors.append("Missing reference to Semantic Versioning")

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
                        self.errors.append(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

                versions_and_dates.append((version_str, date_obj))

        return versions_and_dates

    def validate_versions_and_dates(self) -> None:
        """Validate that version numbers and dates are monotonically increasing."""
        versions_and_dates = self.extract_versions_and_dates()

        if not versions_and_dates:
            self.errors.append("No version entries found")
            return

        # Check if first entry is "Unreleased" (if required)
        if self.require_unreleased and versions_and_dates[0][0].lower() != "unreleased":
            self.errors.append("First version entry should be [Unreleased]")

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
                        f"(versions should be in descending order)"
                    )
            except Exception as e:
                self.errors.append(f"Invalid version format: {current_ver_str} or {next_ver_str}. Error: {e}")

            # Check date order if both dates exist
            # Allow same date (>=) instead of requiring strictly greater (>)
            if current_date and next_date and current_date < next_date:
                self.errors.append(
                    f"Date {current_date} for version {current_ver_str} should not be before "
                    f"{next_date} for version {next_ver_str}"
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
                    self.errors.append(f"Line {line_num} should start with a bullet point (- or *)")

    def validate_spelling(self) -> None:
        """Check for spelling mistakes in the changelog."""
        if not self.spell_check_enabled:
            return

        # Extract words from the changelog
        words = []
        for line in self.lines:
            # Skip headers and code blocks
            if line.strip().startswith("#") or line.strip().startswith("```"):
                continue

            # Extract words from the line
            line_words = re.findall(r"\b[a-zA-Z]+\b", line)
            words.extend(line_words)

        # Check spelling
        misspelled = []
        for word in words:
            # Skip short words, technical terms, and proper nouns (capitalized)
            if (
                len(word) <= 2
                or word.lower() in self.technical_terms
                or (word[0].isupper() and len(word) > 1 and word[1:].islower())
            ):
                continue

            if not self.dictionary.check(word):
                misspelled.append(word)

        # Report unique misspelled words
        unique_misspelled = set(misspelled)
        if unique_misspelled:
            self.errors.append(f"Possible spelling mistakes: {', '.join(unique_misspelled)}")

    def validate_extension_version(self) -> None:
        """Validate that the latest version in the changelog matches the version in extension.toml."""
        # Get the latest version from the changelog (excluding "Unreleased")
        versions = self.extract_versions_and_dates()
        actual_versions = [(v, d) for v, d in versions if v.lower() != "unreleased"]

        if not actual_versions:
            self.errors.append("No actual version entries found in changelog")
            return

        latest_version_str = actual_versions[0][0]

        # Find the extension.toml file
        # The changelog is in source/extensions/omni.isaac.foo/docs/CHANGELOG.md
        # The extension.toml is in source/extensions/omni.isaac.foo/config/extension.toml
        changelog_path = Path(self.file_path)

        # Go up from docs to the extension root directory
        extension_dir = changelog_path.parent.parent
        extension_toml_path = extension_dir / "config" / "extension.toml"

        if not extension_toml_path.exists():
            self.errors.append(f"extension.toml not found at {extension_toml_path}")
            return

        # Read the extension.toml file
        try:
            with open(extension_toml_path, "rb") as f:
                extension_data = tomli.load(f)

            # Check for version in the package section
            if "package" not in extension_data:
                self.errors.append(f"No [package] section found in {extension_toml_path}")
                return

            if "version" not in extension_data["package"]:
                self.errors.append(f"No version field found in [package] section of {extension_toml_path}")
                return

            toml_version = extension_data["package"]["version"]

            # Compare versions
            if toml_version != latest_version_str:
                self.errors.append(
                    f"Version mismatch: {latest_version_str} in changelog doesn't match "
                    f"{toml_version} in extension.toml"
                )

        except Exception as e:
            self.errors.append(f"Error reading extension.toml: {e}")

    def print_results(self) -> None:
        """Print validation results."""
        if not self.errors:
            print(f"✅ {self.file_path} is valid!")
        else:
            print(f"❌ {self.file_path} has {len(self.errors)} issues:")
            for error in self.errors:
                print(f"  - {error}")

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
            print(f"Error writing to file: {e}")
            return False


def validate_all_extensions(
    extensions_dir: str,
    check_extension_version: bool = True,
    require_unreleased: bool = True,
    require_references: bool = True,
    check_spelling: bool = True,
    verbose: bool = False,
) -> Dict[str, List[str]]:
    """Validate changelogs for all extensions in the given directory."""
    results = {}
    extensions_path = Path(extensions_dir)

    if not extensions_path.exists() or not extensions_path.is_dir():
        print(f"Error: Extensions directory '{extensions_dir}' does not exist or is not a directory")
        return {"error": [f"Invalid extensions directory: {extensions_dir}"]}

    # Find all extension directories
    for ext_dir in extensions_path.iterdir():
        if not ext_dir.is_dir():
            continue

        # Changelog is in the docs subfolder
        changelog_path = ext_dir / "docs" / "CHANGELOG.md"
        if not changelog_path.exists():
            results[ext_dir.name] = [f"CHANGELOG.md not found in {ext_dir}/docs"]
            continue

        # Validate the changelog
        validator = ChangelogValidator(
            str(changelog_path),
            check_extension_version=check_extension_version,
            require_unreleased=require_unreleased,
            require_references=require_references,
            check_spelling=check_spelling,
            verbose=verbose,
        )
        validator.validate()

        if validator.errors:
            results[ext_dir.name] = validator.errors
        else:
            results[ext_dir.name] = []

    return results


def format_all_extensions(extensions_dir: str, verbose: bool = False) -> Dict[str, bool]:
    """Format changelogs for all extensions in the given directory."""
    results = {}
    formatted_files = []
    skipped_files = []
    missing_files = []

    extensions_path = Path(extensions_dir)

    if not extensions_path.exists() or not extensions_path.is_dir():
        print(f"Error: Extensions directory '{extensions_dir}' does not exist or is not a directory")
        return {"error": False}

    # Find all extension directories
    for ext_dir in extensions_path.iterdir():
        if not ext_dir.is_dir():
            continue

        # Changelog is in the docs subfolder
        changelog_path = ext_dir / "docs" / "CHANGELOG.md"
        if not changelog_path.exists():
            results[ext_dir.name] = False
            missing_files.append(str(changelog_path))
            continue

        # Format the changelog
        validator = ChangelogValidator(str(changelog_path), verbose=verbose)

        # Read the file first to check if formatting is needed
        validator.read_file()
        formatted_lines = validator.format_changelog()

        # Check if the file content would change after formatting
        original_content = "".join(validator.lines)
        formatted_content = "\n".join(formatted_lines)

        if original_content.strip() != formatted_content.strip():
            # File needs formatting
            success = validator.format_and_save()
            results[ext_dir.name] = success

            if success:
                formatted_files.append(str(changelog_path))
            else:
                skipped_files.append(str(changelog_path))
        else:
            # File is already properly formatted
            results[ext_dir.name] = True
            skipped_files.append(str(changelog_path))

    # Print summary
    if formatted_files:
        print(f"\nFormatted {len(formatted_files)} files:")
        for file in formatted_files:
            print(f"  ✅ {file}")

    if verbose and skipped_files:
        print(f"\nSkipped {len(skipped_files)} files (already formatted or no changes needed):")
        for file in skipped_files:
            print(f"  ℹ️ {file}")

    if missing_files:
        print(f"\nMissing {len(missing_files)} changelog files:")
        for file in missing_files:
            print(f"  ❌ {file}")

    return results


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> callable:
    """Setup function for the repo tool."""
    # Get default values from config
    tool_config = config.get("repo_validate_changelogs", {})

    # Validation options
    parser.add_argument(
        "--check-version",
        action="store_true",
        default=tool_config.get("check_version", False),
        help="Check if changelog version matches extension.toml version",
    )
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
        "--check-spelling",
        action="store_true",
        default=tool_config.get("check_spelling", False),
        help="Check for spelling mistakes",
    )

    # Add an option to enable all checks
    parser.add_argument(
        "--check-all", action="store_true", default=tool_config.get("check_all", False), help="Enable all checks"
    )

    # Add a format option
    parser.add_argument(
        "--format",
        action="store_true",
        default=tool_config.get("format", False),
        help="Format the changelog files (fix spacing, etc.)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", default=tool_config.get("verbose", False), help="Enable verbose output"
    )

    # Add option to specify extensions directory
    parser.add_argument(
        "--extensions-dir",
        default=tool_config.get("extensions_dir", "source/extensions"),
        help="Path to extensions directory (relative to repo root)",
    )

    # Return the function to run when the tool is invoked
    return run_tool


def run_tool(args: Dict[str, Any], config: Dict[str, Any]) -> int:
    """Run the changelog validation tool."""
    # Get the extensions directory from args or config
    extensions_dir = os.path.join(config.get("root", "."), args.extensions_dir)

    # If format is specified, format the files
    if args.format:
        format_all_extensions(extensions_dir, verbose=args.verbose)

        # If no validation is requested, exit after formatting
        if not (
            args.check_all
            or args.check_version
            or args.check_unreleased
            or args.check_references
            or args.check_spelling
        ):
            return 0

        # If validation is also requested, add a separator
        print("\n" + "-" * 60 + "\n")
        print("Running validation checks...\n")

    # If --check-all is specified, enable all checks
    if args.check_all:
        check_version = True
        check_unreleased = True
        check_references = True
        check_spelling = True
    else:
        # Otherwise, use the individual flags
        check_version = args.check_version
        check_unreleased = args.check_unreleased
        check_references = args.check_references
        check_spelling = args.check_spelling

    # If no checks are specified and not formatting, show help
    if not (check_version or check_unreleased or check_references or check_spelling or args.format):
        print("\nNo actions specified. Use --format to format files or --check-* options to validate.")
        return 0

    # Only run validation if at least one check is enabled
    if check_version or check_unreleased or check_references or check_spelling:
        results = validate_all_extensions(
            extensions_dir,
            check_extension_version=check_version,
            require_unreleased=check_unreleased,
            require_references=check_references,
            check_spelling=check_spelling,
            verbose=args.verbose,
        )

        # Print results
        error_count = 0
        valid_count = 0

        for ext_name, errors in results.items():
            if errors:
                print(f"❌ Extension '{ext_name}' has {len(errors)} issues:")
                for error in errors:
                    print(f"  - {error}")
                error_count += len(errors)
            else:
                valid_count += 1
                if args.verbose:
                    print(f"✅ Extension '{ext_name}' is valid!")

        # Print summary
        print(f"\nValidation summary:")
        print(f"  ✅ {valid_count} extensions passed all checks")

        if error_count > 0:
            print(f"  ❌ Found {error_count} total issues across all extensions")
            return 1
        else:
            print(f"  🎉 All extension changelogs are valid!")
            return 0

    return 0
