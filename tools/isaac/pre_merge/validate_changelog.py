# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

r"""Validate changelog format and version bump for Isaac Sim extensions.

Checks that each extension has:
  - A readable version in config/extension.toml
  - A matching top entry in docs/CHANGELOG.md
  - A version bump relative to the base branch (when --base-branch is given)
  - Correct changelog formatting (header, sections, dates, bullet points)

When --fix is passed, auto-fixable issues (spacing, capitalization, separator
characters) are corrected in-place.

Usage:
    # Validate specific extensions
    python tools/isaac/pre_merge/validate_changelog.py source/extensions/isaacsim.robot.poser

    # Validate with base branch comparison
    python tools/isaac/pre_merge/validate_changelog.py source/extensions/isaacsim.robot.poser \\
        --base-branch origin/main

    # Validate and auto-fix formatting
    python tools/isaac/pre_merge/validate_changelog.py source/extensions/isaacsim.robot.poser --fix
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure this script's directory is on sys.path so repo_helpers and term_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import REPO_ROOT, load_toml, read_toml_version
from term_helpers import log_fail, log_info, log_pass, log_warn

# ---------------------------------------------------------------------------
# Version comparison helpers
# ---------------------------------------------------------------------------

try:
    from packaging import version as _pkg_version

    def _parse_version(version_str: str):
        return _pkg_version.parse(version_str)

except ImportError:

    class _SimpleVersion:
        def __init__(self, version_str: str) -> None:
            self.version_str = version_str
            parts = version_str.split(".")
            self.major = int(parts[0]) if parts and parts[0].isdigit() else 0
            self.minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            self.patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            self.is_prerelease = len(parts) > 3 or (len(parts) > 2 and not parts[2].isdigit())

        def __lt__(self, other):
            if self.major != other.major:
                return self.major < other.major
            if self.minor != other.minor:
                return self.minor < other.minor
            if self.patch != other.patch:
                return self.patch < other.patch
            if self.is_prerelease and not other.is_prerelease:
                return True
            if not self.is_prerelease and other.is_prerelease:
                return False
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

    def _parse_version(version_str: str):
        return _SimpleVersion(version_str)


_CHANGELOG_VERSION_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]")

VALID_SECTIONS = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


# ---------------------------------------------------------------------------
# ChangelogValidator — migrated from update_changelogs.py
# ---------------------------------------------------------------------------


class ChangelogValidator:
    """Validate a single CHANGELOG.md file against Keep-a-Changelog rules.

    Args:
        file_path: Path to the CHANGELOG.md file.
        extension_toml_path: Optional path to extension.toml for version checks.
        require_unreleased: Whether the first version entry must be [Unreleased].
        verbose: Enable verbose output during fixes.
    """

    def __init__(
        self,
        file_path: str | Path,
        extension_toml_path: str | Path | None = None,
        require_unreleased: bool = False,
        verbose: bool = False,
    ) -> None:
        self.file_path = str(file_path)
        self.extension_toml_path = str(extension_toml_path) if extension_toml_path else None
        self.rel_changelog_path = os.path.basename(os.path.dirname(os.path.dirname(self.file_path)))
        self.lines: list[str] = []
        self.errors: list[str] = []
        self.require_unreleased = require_unreleased
        self.verbose = verbose

    # -- reading -------------------------------------------------------------

    def read_file(self) -> bool:
        """Read the changelog file into memory.

        Returns:
            True if the file was read successfully, False otherwise.
        """
        try:
            with open(self.file_path, encoding="utf-8") as f:
                self.lines = f.readlines()
            return True
        except Exception as e:
            self.errors.append(f"Error reading file {self.rel_changelog_path}: {e}")
            return False

    # -- validation ----------------------------------------------------------

    def validate(self) -> bool:
        """Run all validation checks.

        Returns:
            True when no errors found, False otherwise.
        """
        if not self.read_file():
            return False
        self.validate_header()
        self.validate_line_format()
        self.validate_versions_and_dates()
        self.validate_sections()
        self.validate_bullet_points()
        if self.extension_toml_path:
            self.validate_extension_version()
        return len(self.errors) == 0

    def validate_header(self) -> None:
        """Check that the file starts with '# Changelog'."""
        if not self.lines:
            self.errors.append(f"File {self.rel_changelog_path} is empty")
            return
        if not self.lines[0].strip().startswith("# Changelog"):
            self.errors.append(f"File {self.rel_changelog_path} should start with '# Changelog'")

    def extract_versions_and_dates(self) -> list[tuple[str, datetime.date | None, int]]:
        """Extract version strings, dates, and line numbers from changelog headers.

        Returns:
            List of (version_str, date_obj, line_num) tuples.
        """
        versions_and_dates: list[tuple[str, datetime.date | None, int]] = []
        version_pattern = re.compile(r"## \[([^\]]+)\](?:[ ]([^\w\s])[ ](\d{4}-\d{2}-\d{2}))?")
        malformed_date_pattern = re.compile(r"## \[([^\]]+)\][ ][-][ ](.+)")

        for line_num, line in enumerate(self.lines, 1):
            match = version_pattern.match(line.strip())
            if match:
                version_str = match.group(1)
                separator = match.group(2)
                date_str = match.group(3)

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
                    malformed_match = malformed_date_pattern.match(line.strip())
                    if malformed_match and malformed_match.group(1) == version_str:
                        malformed_date_text = malformed_match.group(2).strip()
                        if version_str.lower() != "unreleased" and malformed_date_text:
                            self.errors.append(
                                f"Line {line_num}: Invalid date format for version [{version_str}]: "
                                f"'{malformed_date_text}'. Use YYYY-MM-DD format with zero-padded "
                                f"months and days (e.g., 2023-12-01, not 2023-12-1)."
                            )

                versions_and_dates.append((version_str, date_obj, line_num))

        return versions_and_dates

    def validate_versions_and_dates(self) -> None:
        """Check version ordering, date presence, and date ordering."""
        versions_and_dates = self.extract_versions_and_dates()

        if not versions_and_dates:
            self.errors.append("No version entries found")
            return

        if self.require_unreleased and versions_and_dates[0][0].lower() != "unreleased":
            line_num = versions_and_dates[0][2]
            self.errors.append(f"Line {line_num}: First version entry should be [Unreleased]")

        actual_versions = [(v, d, ln) for v, d, ln in versions_and_dates if v.lower() != "unreleased"]

        for ver_str, date_obj, line_num in actual_versions:
            if date_obj is None:
                already_reported = any(f"Invalid date format for version [{ver_str}]" in err for err in self.errors)
                if not already_reported:
                    self.errors.append(
                        f"Line {line_num}: Version [{ver_str}] is missing a date. "
                        f"Released versions must have a date in format: ## [{ver_str}] - YYYY-MM-DD"
                    )

        for i in range(len(actual_versions) - 1):
            cur_str, cur_date, cur_ln = actual_versions[i]
            nxt_str, nxt_date, nxt_ln = actual_versions[i + 1]

            try:
                if _parse_version(cur_str) <= _parse_version(nxt_str):
                    self.errors.append(
                        f"Line {cur_ln}: Version {cur_str} should be greater than {nxt_str} "
                        f"(line {nxt_ln}) - versions should be in descending order"
                    )
            except Exception as e:
                self.errors.append(
                    f"Lines {cur_ln}/{nxt_ln}: Invalid version format: {cur_str} or {nxt_str}. Error: {e}"
                )

            if cur_date and nxt_date and cur_date < nxt_date:
                self.errors.append(
                    f"Line {cur_ln}: Date {cur_date} for version {cur_str} should not be before "
                    f"{nxt_date} for version {nxt_str} (line {nxt_ln})"
                )

    def validate_sections(self) -> None:
        """Check that section headers use valid Keep-a-Changelog names."""
        section_pattern = re.compile(r"^### (.+)$")
        for i, line in enumerate(self.lines):
            match = section_pattern.match(line.strip())
            if match:
                section_name = match.group(1)
                if section_name not in VALID_SECTIONS:
                    if section_name.lower() in [s.lower() for s in VALID_SECTIONS]:
                        self.errors.append(
                            f"Line {i+1}: Section '{section_name}' has incorrect capitalization. "
                            f"Should be one of: {', '.join(VALID_SECTIONS)}"
                        )
                    else:
                        self.errors.append(
                            f"Line {i+1}: Invalid section '{section_name}'. "
                            f"Should be one of: {', '.join(VALID_SECTIONS)}"
                        )

    def validate_line_format(self) -> None:
        """Check that lines start with allowed prefixes."""
        allowed_patterns = ("# Changelog", "## [", "### ", "-", "The format is based on")
        for line_num, line in enumerate(self.lines, 1):
            if not line.strip():
                continue
            stripped_line = line.lstrip()
            if stripped_line.startswith("-") and line[0] in (" ", "\t"):
                continue
            if not line.startswith(allowed_patterns):
                line_preview = line.rstrip()[:50] + "..." if len(line.rstrip()) > 50 else line.rstrip()
                self.errors.append(
                    f"Line {line_num}: Incorrect format. "
                    f"Lines should start with: '# Changelog', '## [', '### ', '-', or nested bullet points. "
                    f"Got: '{line_preview}'"
                )

    def validate_bullet_points(self) -> None:
        """Check that section content uses bullet points (- or *)."""
        in_version = False
        in_section = False
        version_pattern = re.compile(r"## \[([^\]]+)\]")
        section_pattern = re.compile(r"### (\w+)")

        for line_num, line in enumerate(self.lines, 1):
            line = line.strip()
            if not line:
                continue
            if version_pattern.match(line):
                in_version = True
                in_section = False
                continue
            if section_pattern.match(line):
                in_section = True
                continue
            if in_version and in_section:
                if line.startswith("#") or line.startswith("```"):
                    continue
                if not line.startswith("-") and not line.startswith("*"):
                    self.errors.append(f"Line {line_num} should start with a bullet point (- or *)")

    def validate_extension_version(self) -> None:
        """Check that the top changelog version matches extension.toml."""
        versions = self.extract_versions_and_dates()
        actual_versions = [(v, d, ln) for v, d, ln in versions if v.lower() != "unreleased"]

        if not actual_versions:
            self.errors.append("No actual version entries found")
            return

        latest_version_str, _, latest_line_num = actual_versions[0]

        if not self.extension_toml_path or not os.path.exists(self.extension_toml_path):
            self.errors.append(f"extension.toml not found at {self.extension_toml_path}")
            return

        try:
            extension_data = load_toml(Path(self.extension_toml_path))

            if "package" not in extension_data:
                self.errors.append(f"No [package] section found in extension.toml")
                return
            if "version" not in extension_data["package"]:
                self.errors.append(f"No version field found in [package] section of extension.toml")
                return

            toml_version = extension_data["package"]["version"]
            if toml_version != latest_version_str:
                self.errors.append(
                    f"Line {latest_line_num}: Version mismatch: {latest_version_str} in CHANGELOG.md "
                    f"doesn't match {toml_version} in extension.toml"
                )
        except Exception as e:
            self.errors.append(f"Error reading extension.toml: {e}")

    # -- fixing / formatting -------------------------------------------------

    def fix_version_format(self) -> None:
        """Fix incorrect version-line separators (e.g. ``=`` -> ``-``)."""
        version_pattern = re.compile(r"(## \[([^\]]+)\])[ ]([^\w\s])[ ](\d{4}-\d{2}-\d{2})")
        for i, line in enumerate(self.lines):
            match = version_pattern.match(line.strip())
            if match and match.group(3) != "-":
                version_header = match.group(1)
                date = match.group(4)
                corrected_line = f"{version_header} - {date}"
                if self.verbose:
                    print(f"  Fixed version format in line {i+1}: '{line.strip()}' -> '{corrected_line}'")
                self.lines[i] = corrected_line + "\n" if line.endswith("\n") else corrected_line

    def format_changelog(self) -> list[str]:
        """Return formatted lines with normalized spacing and capitalized bullet points.

        Returns:
            List of formatted changelog lines.
        """
        if not self.lines:
            return []

        formatted_lines: list[str] = []
        in_version_section = False
        in_subsection = False
        empty_line_count = 0
        last_line_was_version = False

        version_pattern = re.compile(r"## \[([^\]]+)\]")
        section_pattern = re.compile(r"### (\w+)")

        for line in self.lines:
            line = line.rstrip()

            if version_pattern.match(line):
                if in_version_section and formatted_lines and formatted_lines[-1] != "":
                    formatted_lines.append("")
                in_version_section = True
                in_subsection = False
                empty_line_count = 0
                last_line_was_version = True
                formatted_lines.append(line)
                continue

            if section_pattern.match(line) and in_version_section:
                if in_subsection and not last_line_was_version and formatted_lines[-1] != "":
                    formatted_lines.append("")
                in_subsection = True
                empty_line_count = 0
                last_line_was_version = False
                formatted_lines.append(line)
                continue

            if not line.strip():
                if last_line_was_version:
                    continue
                empty_line_count += 1
                if empty_line_count <= 1:
                    formatted_lines.append("")
                continue

            empty_line_count = 0
            last_line_was_version = False
            line = self._capitalize_bullet_point(line)
            formatted_lines.append(line)

        if formatted_lines and formatted_lines[-1] != "":
            formatted_lines.append("")

        return formatted_lines

    def format_and_save(self) -> bool:
        """Fix separators, format the file, and write it back.

        Returns:
            True if the file was written successfully, False otherwise.
        """
        self.fix_version_format()
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

    # -- bullet-point capitalization helpers ----------------------------------

    @staticmethod
    def _capitalize_bullet_point(line: str) -> str:
        """Capitalize the first letter of a bullet-point entry.

        Skips capitalization for code references, function names, variable
        names, and other technical terms that should stay lowercase.

        Args:
            line: A single changelog line, possibly starting with a bullet.

        Returns:
            The line with the first letter capitalized when applicable.
        """
        bullet_pattern = re.compile(r"^(\s*-\s+)(.*)$")
        match = bullet_pattern.match(line)
        if match:
            prefix = match.group(1)
            content = match.group(2)
            if content and ChangelogValidator._should_capitalize(content):
                return prefix + content[0].upper() + content[1:]
        return line

    @staticmethod
    def _should_capitalize(content: str) -> bool:
        if not content:
            return False
        first_char = content[0]
        if not first_char.islower():
            return False

        first_word_match = re.match(r"^([a-zA-Z0-9_.\[\]():=<>!-]+)", content)
        if first_word_match:
            first_word = first_word_match.group(1)
            if re.search(r"[_().\[\]:=<>!]", first_word):
                return False
            if "-" in first_word[1:]:
                return False
            if re.search(r"^[a-z]+[A-Z]", first_word):
                return False
        return True


# ---------------------------------------------------------------------------
# Version-bump helpers (original check_changelog_version logic)
# ---------------------------------------------------------------------------


def _read_changelog_version(ext_path: Path) -> str | None:
    changelog = ext_path / "docs" / "CHANGELOG.md"
    if not changelog.exists():
        return None
    for line in changelog.read_text().splitlines():
        m = _CHANGELOG_VERSION_RE.match(line.strip())
        if m:
            return m.group(1)
    return None


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def _get_base_branch_version(ext_path: Path, base_branch: str) -> str | None:
    rel = ext_path.relative_to(REPO_ROOT)
    toml_rel = rel / "config" / "extension.toml"
    proc = subprocess.run(
        ["git", "show", f"{base_branch}:{toml_rel.as_posix()}"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        return None
    in_package = False
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_package = stripped == "[package]"
            continue
        if in_package and stripped.startswith("version"):
            match = re.search(r'"([^"]+)"', stripped)
            if match:
                return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------


def check_changelog_and_version(extensions: list[Path], base_branch: str | None) -> int:
    """Validate changelog and version for each extension.

    Args:
        extensions: List of extension directory paths.
        base_branch: Optional base branch for version bump comparison.

    Returns:
        Number of validation errors encountered.
    """
    if not extensions:
        log_info("No extensions to check.")
        return 0

    errors = 0
    for ext in extensions:
        name = ext.name
        toml_version = read_toml_version(ext)
        changelog_version = _read_changelog_version(ext)

        if toml_version is None:
            log_fail(f"{name}: cannot read version from extension.toml")
            errors += 1
            continue

        if base_branch:
            base_version = _get_base_branch_version(ext, base_branch)
            if base_version and base_version == toml_version:
                log_fail(f"{name}: version {toml_version} not bumped vs {base_branch}")
                errors += 1
                continue
            if base_version and _version_tuple(toml_version) <= _version_tuple(base_version):
                log_fail(
                    f"{name}: version {toml_version} must be greater than " f"{base_branch} version {base_version}"
                )
                errors += 1
                continue

        if changelog_version is None:
            log_fail(f"{name}: no version entry found in docs/CHANGELOG.md")
            errors += 1
            continue

        if toml_version != changelog_version:
            log_fail(
                f"{name}: extension.toml version ({toml_version}) != " f"CHANGELOG.md top version ({changelog_version})"
            )
            errors += 1
            continue

        log_pass(f"{name}: version {toml_version} matches changelog.")

    return errors


def validate_changelog_format(extensions: list[Path], fix: bool = False) -> int:
    """Run ChangelogValidator on each extension.

    Args:
        extensions: List of extension directory paths.
        fix: Whether to auto-fix formatting issues in-place.

    Returns:
        Number of validation errors encountered.
    """
    if not extensions:
        log_info("No extensions to validate changelog format.")
        return 0

    errors = 0
    for ext in extensions:
        name = ext.name
        changelog_path = ext / "docs" / "CHANGELOG.md"
        toml_path = ext / "config" / "extension.toml"

        if not changelog_path.exists():
            continue

        validator = ChangelogValidator(
            file_path=str(changelog_path),
            extension_toml_path=str(toml_path) if toml_path.exists() else None,
            verbose=False,
        )
        is_valid = validator.validate()

        if not is_valid:
            for err in validator.errors:
                log_fail(f"{name}: {err}")
            errors += len(validator.errors)

        if fix:
            validator.format_and_save()
            if not is_valid:
                log_warn(f"{name}: auto-fixed formatting (re-run to verify)")
        elif is_valid:
            log_pass(f"{name}: changelog format OK.")

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse CLI arguments and run changelog validation.

    Returns:
        0 on success, 1 on validation failure or invalid input.
    """
    parser = argparse.ArgumentParser(
        description="Validate changelog format and version bump for Isaac Sim extensions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "extensions",
        nargs="+",
        type=Path,
        help="Extension directories to validate.",
    )
    parser.add_argument(
        "--base-branch",
        default=None,
        help="Base branch for version comparison (e.g. origin/main).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Auto-fix formatting issues (spacing, capitalization, separators).",
    )
    args = parser.parse_args()

    ext_dirs = [p.resolve() for p in args.extensions if p.is_dir()]
    if not ext_dirs:
        print("No valid extension directories provided.", flush=True)
        return 1

    errors = 0
    errors += check_changelog_and_version(ext_dirs, args.base_branch)
    errors += validate_changelog_format(ext_dirs, fix=args.fix)
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
