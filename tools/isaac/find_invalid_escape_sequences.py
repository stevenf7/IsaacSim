#!/usr/bin/env python3
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
Script to find Python files with invalid escape sequences that trigger SyntaxWarnings.

This tool scans Python files in the codebase and identifies those that contain invalid
escape sequences (e.g., '\\d' in regular strings instead of r'\\d' or '\\\\d'). These
warnings are emitted by Python's AST parser when analyzing code.

Usage Examples:
    # Scan default directories
    python tools/isaac/find_invalid_escape_sequences.py

    # Scan specific directories
    python tools/isaac/find_invalid_escape_sequences.py --search-dirs source exts

    # Show detailed line-by-line analysis
    python tools/isaac/find_invalid_escape_sequences.py --verbose

    # Save results to JSON
    python tools/isaac/find_invalid_escape_sequences.py --output-json results.json

    # Only show files with warnings (no detailed output)
    python tools/isaac/find_invalid_escape_sequences.py --files-only

    # Exclude certain paths
    python tools/isaac/find_invalid_escape_sequences.py --exclude "tests/*" "test_*.py"

Features:
    - Scans Python files and captures SyntaxWarnings from ast.parse()
    - Reports files with issues and the specific line numbers with warnings
    - Shows the problematic escape sequences and suggested fixes
    - Supports JSON output for automated processing
    - Can follow symlinks for build directories
    - Supports file exclusion patterns
"""

import argparse
import ast
import os
import sys
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class InvalidEscapeSequenceFinder:
    """Finds Python files with invalid escape sequences that trigger SyntaxWarnings.

    This class scans Python files and uses ast.parse() to identify files that contain
    invalid escape sequences, capturing the warnings and providing detailed reports.
    """

    def __init__(self, root_dir: str, verbose: bool = False, exclusion_patterns: List[str] = None):
        """Initialize the InvalidEscapeSequenceFinder.

        Args:
            root_dir: Root directory of the repository to scan.
            verbose: Enable verbose debug output.
            exclusion_patterns: List of file patterns to exclude from scanning.
        """
        self.root_dir = Path(root_dir)
        self.verbose = verbose
        self.exclusion_patterns = exclusion_patterns or []
        self.files_with_warnings = {}  # file_path -> list of warnings

    def log(self, message: str):
        """Print message if verbose mode is enabled.

        Args:
            message: Debug message to print.
        """
        if self.verbose:
            print(f"DEBUG: {message}")

    def should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on exclusion patterns.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file should be excluded, False otherwise.
        """
        import fnmatch

        try:
            relative_path = file_path.relative_to(self.root_dir)
        except ValueError:
            relative_path = file_path

        path_str = str(relative_path).replace(os.sep, "/")

        for pattern in self.exclusion_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True

        return False

    def find_python_files(self, search_dirs: List[str]) -> List[Path]:
        """Find all Python files in the specified directories.

        Args:
            search_dirs: List of directory paths relative to root_dir to search in.

        Returns:
            List of Path objects for all Python files found.
        """
        python_files = []

        for search_dir in search_dirs:
            search_path = self.root_dir / search_dir
            if not search_path.exists():
                self.log(f"Search directory not found: {search_path}")
                continue

            self.log(f"Searching for Python files in {search_path}")

            for root, dirs, files in os.walk(str(search_path), followlinks=True):
                for file in files:
                    if file.endswith(".py"):
                        py_file = Path(root) / file
                        if not self.should_exclude(py_file):
                            python_files.append(py_file)

        self.log(f"Found {len(python_files)} Python files to analyze")
        return python_files

    def check_file_for_warnings(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check a single Python file for invalid escape sequence warnings.

        Args:
            file_path: Path to the Python file to check.

        Returns:
            List of tuples (line_number, warning_message, line_content) for each warning found.
        """
        warnings_found = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Capture warnings from ast.parse
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", SyntaxWarning)
                try:
                    ast.parse(content, filename=str(file_path))
                except SyntaxError:
                    # File has syntax errors, skip it
                    self.log(f"Syntax error in {file_path}, skipping")
                    return warnings_found

                # Process captured warnings
                for warning in w:
                    if issubclass(warning.category, SyntaxWarning):
                        msg = str(warning.message)
                        line_no = warning.lineno if hasattr(warning, "lineno") else 0

                        # Get the line content if available
                        line_content = ""
                        if line_no > 0 and line_no <= len(lines):
                            line_content = lines[line_no - 1].strip()

                        warnings_found.append((line_no, msg, line_content))

        except Exception as e:
            self.log(f"Error reading {file_path}: {e}")

        return warnings_found

    def analyze_files(self, search_dirs: List[str]) -> Dict[str, List[Tuple[int, str, str]]]:
        """Analyze all Python files in the specified directories for invalid escape sequences.

        Args:
            search_dirs: List of directory paths to search for Python files.

        Returns:
            Dictionary mapping file paths to lists of warnings found in each file.
        """
        python_files = self.find_python_files(search_dirs)
        files_with_warnings = {}

        print(f"Analyzing {len(python_files)} Python files...")

        for i, py_file in enumerate(python_files):
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(python_files)} files analyzed...")

            warnings = self.check_file_for_warnings(py_file)
            if warnings:
                try:
                    relative_path = py_file.relative_to(self.root_dir)
                except ValueError:
                    relative_path = py_file
                files_with_warnings[str(relative_path)] = warnings

        return files_with_warnings

    def print_results(self, files_with_warnings: Dict[str, List[Tuple[int, str, str]]], files_only: bool = False):
        """Print the analysis results to console.

        Args:
            files_with_warnings: Dictionary mapping file paths to their warnings.
            files_only: If True, only print file names without detailed warnings.
        """
        if not files_with_warnings:
            print("\n✓ No files with invalid escape sequence warnings found!")
            return

        total_warnings = sum(len(warnings) for warnings in files_with_warnings.values())

        print(f"\n=== Invalid Escape Sequence Report ===")
        print(f"Files with warnings: {len(files_with_warnings)}")
        print(f"Total warnings: {total_warnings}")
        print()

        if files_only:
            print("Files with invalid escape sequences:")
            for file_path in sorted(files_with_warnings.keys()):
                warning_count = len(files_with_warnings[file_path])
                print(f"  {file_path} ({warning_count} warnings)")
        else:
            # Group by warning type
            warning_types = defaultdict(list)
            for file_path, warnings in files_with_warnings.items():
                for line_no, msg, line_content in warnings:
                    warning_types[msg].append((file_path, line_no, line_content))

            print("Files with invalid escape sequences:\n")
            for file_path in sorted(files_with_warnings.keys()):
                warnings = files_with_warnings[file_path]
                print(f"📄 {file_path} ({len(warnings)} warnings)")

                for line_no, msg, line_content in warnings:
                    print(f"   Line {line_no}: {msg}")
                    if line_content and self.verbose:
                        print(f"      {line_content}")
                print()

            # Show summary by warning type
            print("\n=== Summary by Warning Type ===")
            for msg, occurrences in sorted(warning_types.items(), key=lambda x: -len(x[1])):
                print(f"\n{msg}")
                print(f"  Found in {len(occurrences)} locations")
                if self.verbose:
                    for file_path, line_no, line_content in occurrences[:5]:
                        print(f"    {file_path}:{line_no}")
                    if len(occurrences) > 5:
                        print(f"    ... and {len(occurrences) - 5} more")

    def save_results_json(self, files_with_warnings: Dict[str, List[Tuple[int, str, str]]], output_file: str):
        """Save results to a JSON file.

        Args:
            files_with_warnings: Dictionary mapping file paths to their warnings.
            output_file: Path to the output JSON file.
        """
        import json

        # Convert tuples to dictionaries for JSON serialization
        json_data = {}
        for file_path, warnings in files_with_warnings.items():
            json_data[file_path] = [
                {
                    "line_number": line_no,
                    "message": msg,
                    "line_content": line_content,
                }
                for line_no, msg, line_content in warnings
            ]

        summary = {
            "total_files_with_warnings": len(files_with_warnings),
            "total_warnings": sum(len(warnings) for warnings in files_with_warnings.values()),
        }

        output_data = {
            "summary": summary,
            "files": json_data,
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to {output_file}")


def main():
    """Main entry point for the invalid escape sequence finder.

    Parses command-line arguments, initializes the finder, runs the analysis,
    and displays or saves the results.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(
        description="Find Python files with invalid escape sequences that trigger SyntaxWarnings"
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory of the repository (default: current directory)",
    )
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=["_build/linux-x86_64/release", "source", "exts"],
        help="Directories to search for Python files (default: _build/linux-x86_64/release source exts)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with line content",
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="Only show file names without detailed warnings",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Write results to a JSON file",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="File patterns to exclude (e.g., --exclude 'tests/*' 'test_*.py')",
    )

    args = parser.parse_args()

    # Validate root directory
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: Root directory does not exist: {root_path}")
        return 1

    print(f"Scanning for invalid escape sequences in: {root_path}")
    print(f"Search directories: {', '.join(args.search_dirs)}")
    if args.exclude:
        print(f"Excluding patterns: {', '.join(args.exclude)}")
    print()

    finder = InvalidEscapeSequenceFinder(
        str(root_path),
        verbose=args.verbose,
        exclusion_patterns=args.exclude,
    )

    files_with_warnings = finder.analyze_files(args.search_dirs)
    finder.print_results(files_with_warnings, files_only=args.files_only)

    if args.output_json:
        finder.save_results_json(files_with_warnings, args.output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
