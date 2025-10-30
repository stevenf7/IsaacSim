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

"""Script to check that all source files have the required SPDX license headers."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# File extensions and their corresponding comment symbols
FILE_EXTENSIONS = {
    # Python files
    ".py": "#",
    # C++ files
    ".cpp": "//",
    ".cc": "//",
    ".cxx": "//",
    ".c": "//",
    ".h": "//",
    ".hpp": "//",
    ".hxx": "//",
    # CUDA files
    ".cu": "//",
    ".cuh": "//",
    # YAML files
    ".yaml": "#",
    ".yml": "#",
    # Jupyter notebooks (special handling)
    ".ipynb": "#",
    # Other common source files
    ".lua": "--",
    ".sh": "#",
    ".bat": "::",
}

# Required header lines (without comment symbols)
REQUIRED_LINES = [
    "SPDX-FileCopyrightText: Copyright (c) {year} NVIDIA CORPORATION & AFFILIATES. All rights reserved.",
    "SPDX-License-Identifier: Apache-2.0",
]

# Full license header template (without comment symbols)
FULL_LICENSE_TEMPLATE = [
    "SPDX-FileCopyrightText: Copyright (c) {year} NVIDIA CORPORATION & AFFILIATES. All rights reserved.",
    "SPDX-License-Identifier: Apache-2.0",
    "",
    'Licensed under the Apache License, Version 2.0 (the "License");',
    "you may not use this file except in compliance with the License.",
    "You may obtain a copy of the License at",
    "",
    "http://www.apache.org/licenses/LICENSE-2.0",
    "",
    "Unless required by applicable law or agreed to in writing, software",
    'distributed under the License is distributed on an "AS IS" BASIS,',
    "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
    "See the License for the specific language governing permissions and",
    "limitations under the License.",
]

# Directories to exclude from checking
EXCLUDED_DIRS = {
    "_build",
    "_compiler",
    "_repo",
    "__pycache__",
    ".git",
    ".vscode",
    ".cursor",
    "node_modules",
    "build",
    "dist",
    "target",
    "deps",
    "PACKAGE-LICENSES",
    "extscache",
    "extsDeprecated",
    "extsUser",
}

# Files to exclude from checking
EXCLUDED_FILES = {
    "__init__.py",  # Often empty or minimal
    "setup.py",
    "conftest.py",
}


def should_skip_path(path: Path) -> bool:
    """Check if a path should be skipped based on exclusion rules.

    Args:
        path: Path to check against exclusion rules.

    Returns:
        True if the path should be skipped, False otherwise.
    """
    # Skip if any parent directory is in excluded dirs
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True

    # Skip if filename is in excluded files
    if path.name in EXCLUDED_FILES:
        return True

    return False


def get_comment_symbol(file_path: Path) -> str:
    """Get the appropriate comment symbol for a file based on its extension.

    Args:
        file_path: Path to the file.

    Returns:
        The comment symbol string for the file type (defaults to '#' for unknown types).
    """
    suffix = file_path.suffix.lower()
    return FILE_EXTENSIONS.get(suffix, "#")  # Default to # if unknown


def extract_year_from_copyright(line: str) -> str:
    """Extract the year or year range from a copyright line.

    Args:
        line: Copyright line to extract year from.

    Returns:
        Year or year range string (e.g., '2024' or '2024-2025'), or 'YYYY' if not found.
    """
    # Look for patterns like "2024", "2024-2025", "2020-2025"
    year_pattern = r"Copyright \(c\) (\d{4}(?:-\d{4})?)"
    match = re.search(year_pattern, line)
    return match.group(1) if match else "YYYY"


def get_current_year() -> str:
    """Get the current year as a string.

    Returns:
        Current year as a four-digit string.
    """
    return str(datetime.now().year)


def is_jupyter_notebook(file_path: Path) -> bool:
    """Check if a file is a Jupyter notebook.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if the file is a Jupyter notebook (.ipynb), False otherwise.
    """
    return file_path.suffix.lower() == ".ipynb"


def read_notebook(file_path: Path) -> Dict[str, Any]:
    """Read and parse a Jupyter notebook file.

    Args:
        file_path: Path to the notebook file.

    Returns:
        Dictionary containing the parsed notebook structure.

    Raises:
        Exception: If the notebook cannot be read or parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Could not read notebook: {e}") from e


def write_notebook(file_path: Path, notebook: Dict[str, Any]) -> bool:
    """Write a Jupyter notebook to file.

    Args:
        file_path: Path where the notebook should be written.
        notebook: Dictionary containing the notebook structure.

    Returns:
        True if the notebook was successfully written, False otherwise.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Add trailing newline
        return True
    except Exception as e:
        print(f"  Error writing notebook: {e}")
        return False


def get_notebook_header_lines(notebook: Dict[str, Any]) -> List[str]:
    """Extract the first few lines from a Jupyter notebook for header checking.

    Args:
        notebook: Dictionary containing the notebook structure.

    Returns:
        List of up to 20 lines from the first cell, or empty list if no suitable cell exists.
    """
    if "cells" not in notebook or not notebook["cells"]:
        return []

    first_cell = notebook["cells"][0]
    if first_cell.get("cell_type") not in ("code", "markdown"):
        return []

    source = first_cell.get("source", [])
    if isinstance(source, str):
        lines = source.split("\n")
    else:
        lines = [line.rstrip("\n") for line in source]

    return lines[:20]  # Return first 20 lines for header checking


def add_notebook_header(notebook: Dict[str, Any], header_lines: List[str]) -> Dict[str, Any]:
    """Add license header to a Jupyter notebook.

    Args:
        notebook: Dictionary containing the notebook structure.
        header_lines: List of license header lines to add.

    Returns:
        Updated notebook dictionary with the header cell added.
    """
    # Create header cell content
    header_content = "\n".join(header_lines) + "\n"

    # Create new header cell
    header_cell = {
        "cell_type": "code",
        "metadata": {},
        "source": [header_content],
        "outputs": [],
        "execution_count": None,
    }

    # Insert at the beginning
    if "cells" not in notebook:
        notebook["cells"] = []

    notebook["cells"].insert(0, header_cell)
    return notebook


def generate_license_header(file_path: Path, year: str = None) -> List[str]:
    """Generate the full license header for a file.

    Args:
        file_path: Path to the file for which to generate the header.
        year: Year or year range to use in the copyright line. Defaults to current year.

    Returns:
        List of formatted license header lines with appropriate comment symbols.
    """
    if year is None:
        year = get_current_year()

    comment_symbol = get_comment_symbol(file_path)
    header_lines = []

    for line in FULL_LICENSE_TEMPLATE:
        formatted_line = line.format(year=year)
        if formatted_line.strip():
            header_lines.append(f"{comment_symbol} {formatted_line}")
        else:
            header_lines.append(comment_symbol)

    return header_lines


def has_shebang(lines: List[str]) -> bool:
    """Check if the first line is a shebang.

    Args:
        lines: List of file lines to check.

    Returns:
        True if the first line starts with '#!', False otherwise.
    """
    return len(lines) > 0 and lines[0].startswith("#!")


def _extract_comment_content(line: str, comment_symbols: set) -> str:
    """Extract content from a line by removing comment symbols.

    Args:
        line: Line to extract content from.
        comment_symbols: Set of possible comment symbols.

    Returns:
        Line content with comment symbols removed.
    """
    stripped = line.strip()
    for cs in comment_symbols:
        if stripped.startswith(cs):
            return stripped[len(cs) :].strip()
    return stripped


def _is_license_line(content: str) -> bool:
    """Check if a line contains license-related content.

    Args:
        content: Stripped line content to check.

    Returns:
        True if the line appears to be part of a license header.
    """
    license_keywords = [
        "SPDX-License-Identifier:",
        "Licensed under the Apache License",
        "http://www.apache.org/licenses/LICENSE-2.0",
        "limitations under the License",
        "WITHOUT WARRANTIES OR CONDITIONS",
        "distributed under the License",
        "See the License for the specific language governing permissions",
        "You may obtain a copy of the License at",
    ]
    return any(keyword in content for keyword in license_keywords)


def find_all_license_headers(lines: List[str]) -> List[Tuple[int, int]]:
    """Find all license headers in a file.

    Args:
        lines: List of lines from the file to search.

    Returns:
        List of tuples (start_index, end_index) for each license header found.
        The end_index is exclusive.
    """
    license_headers = []

    # Skip shebang if present
    search_start = 1 if has_shebang(lines) else 0

    # All possible comment symbols to check for
    all_comment_symbols = set(FILE_EXTENSIONS.values())
    all_comment_symbols.add("REM")  # Also check for REM without @

    i = search_start
    while i < min(len(lines), 50):  # Check first 50 lines
        content = _extract_comment_content(lines[i], all_comment_symbols)

        # Check if this line starts a license header
        if "SPDX-FileCopyrightText:" in content or ("Copyright (c)" in content and "NVIDIA" in content):
            # Found start of a license header, find its end
            start_index = i
            end_index = i + 1

            # Continue until we find the end of this license header
            for j in range(i + 1, min(len(lines), i + 20)):  # Look ahead up to 20 lines
                next_line = lines[j].strip()
                next_content = _extract_comment_content(next_line, all_comment_symbols)
                is_comment_line = any(next_line.startswith(cs) for cs in all_comment_symbols)

                # Check if this line is still part of the license
                if is_comment_line or not next_line or _is_license_line(next_content):
                    end_index = j + 1
                else:
                    # Found the end of the license header
                    break

            # Include any trailing empty lines
            while end_index < len(lines) and not lines[end_index].strip():
                end_index += 1

            license_headers.append((start_index, end_index))
            i = end_index  # Continue searching after this license header
        else:
            i += 1

    return license_headers


def has_multiple_license_headers(file_path: Path) -> Tuple[bool, List[Tuple[int, int]]]:
    """Check if a file has multiple license headers.

    Args:
        file_path: Path to the file to check.

    Returns:
        Tuple of (has_multiple_headers, list_of_header_ranges).
    """
    try:
        if is_jupyter_notebook(file_path):
            # Handle Jupyter notebooks
            notebook = read_notebook(file_path)
            lines = get_notebook_header_lines(notebook)
        else:
            # Handle regular text files
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.rstrip() for line in f.readlines()[:50]]  # Check first 50 lines
    except Exception:
        return False, []

    if not lines:
        return False, []

    license_headers = find_all_license_headers(lines)
    return len(license_headers) > 1, license_headers


def find_existing_license_header(lines: List[str], comment_symbol: str) -> Tuple[int, int]:
    """Find the start and end indices of the first existing license header.

    Args:
        lines: List of file lines to search.
        comment_symbol: Comment symbol for the file type (unused, kept for compatibility).

    Returns:
        Tuple of (start_index, end_index) where end_index is exclusive.
        Returns (-1, -1) if no license header is found.
    """
    license_headers = find_all_license_headers(lines)
    if license_headers:
        return license_headers[0]  # Return the first license header found
    return (-1, -1)


def remove_existing_license_header(lines: List[str], comment_symbol: str) -> List[str]:
    """Remove existing license header from the file lines.

    Args:
        lines: List of file lines.
        comment_symbol: Comment symbol for the file type (unused, kept for compatibility).

    Returns:
        List of lines with the license header removed.
    """
    start_index, end_index = find_existing_license_header(lines, comment_symbol)

    if start_index == -1:
        return lines  # No license header found

    # Remove the license header lines
    return lines[:start_index] + lines[end_index:]


def check_file_header(file_path: Path) -> Tuple[bool, List[str]]:
    """Check if a file has the required SPDX license header.

    Args:
        file_path: Path to the file to check.

    Returns:
        Tuple of (has_valid_header, list_of_issues).
    """
    try:
        if is_jupyter_notebook(file_path):
            # Handle Jupyter notebooks
            notebook = read_notebook(file_path)
            lines = get_notebook_header_lines(notebook)
        else:
            # Handle regular text files
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.rstrip() for line in f.readlines()[:20]]  # Check first 20 lines
    except Exception as e:
        return False, [f"Could not read file: {e}"]

    if not lines:
        return False, ["File is empty or has no content to check"]

    comment_symbol = get_comment_symbol(file_path)
    issues = []

    # Look for SPDX-FileCopyrightText line
    copyright_found = False
    license_found = False
    copyright_year = "YYYY"

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Remove comment symbol and whitespace
        if stripped.startswith(comment_symbol):
            content = stripped[len(comment_symbol) :].strip()
        else:
            content = stripped

        # Check for copyright line
        if "SPDX-FileCopyrightText:" in content and "NVIDIA CORPORATION" in content:
            copyright_found = True
            copyright_year = extract_year_from_copyright(content)

            # Validate the format
            expected_copyright = REQUIRED_LINES[0].format(year=copyright_year)
            if content != expected_copyright:
                issues.append(
                    f"Line {i + 1}: Copyright format incorrect. " f"Expected: '{expected_copyright}', Got: '{content}'"
                )

        # Check for license line
        elif "SPDX-License-Identifier:" in content:
            license_found = True
            if content != REQUIRED_LINES[1]:
                issues.append(
                    f"Line {i + 1}: License identifier incorrect. " f"Expected: '{REQUIRED_LINES[1]}', Got: '{content}'"
                )

    if not copyright_found:
        issues.append("Missing SPDX-FileCopyrightText line")

    if not license_found:
        issues.append("Missing SPDX-License-Identifier line")

    return len(issues) == 0, issues


def _fix_notebook_header(file_path: Path, license_header: List[str]) -> bool:
    """Fix license header in a Jupyter notebook.

    Args:
        file_path: Path to the notebook file.
        license_header: List of license header lines to add.

    Returns:
        True if the notebook was successfully fixed, False otherwise.
    """
    try:
        notebook = read_notebook(file_path)

        # Check if the first cell already has license header
        if "cells" in notebook and notebook["cells"]:
            first_cell_lines = get_notebook_header_lines(notebook)
            comment_symbol = get_comment_symbol(file_path)

            # Check if first cell has existing license header
            start_index, end_index = find_existing_license_header(first_cell_lines, comment_symbol)
            if start_index != -1:
                # Replace the existing header in the first cell
                first_cell = notebook["cells"][0]
                if isinstance(first_cell.get("source", []), str):
                    cell_lines = first_cell["source"].split("\n")
                else:
                    cell_lines = [line.rstrip("\n") for line in first_cell["source"]]

                # Remove existing header and add new one
                cleaned_lines = remove_existing_license_header(cell_lines, comment_symbol)
                new_content = "\n".join(license_header + [""] + cleaned_lines)
                first_cell["source"] = [new_content + "\n"]
                return write_notebook(file_path, notebook)

        # Add header to notebook (no existing header found)
        notebook = add_notebook_header(notebook, license_header)
        return write_notebook(file_path, notebook)

    except Exception as e:
        print(f"  Error processing notebook: {e}")
        return False


def _fix_text_file_header(file_path: Path, license_header: List[str]) -> bool:
    """Fix license header in a regular text file.

    Args:
        file_path: Path to the text file.
        license_header: List of license header lines to add.

    Returns:
        True if the file was successfully fixed, False otherwise.
    """
    try:
        # Read the entire file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            original_lines = [line.rstrip("\n\r") for line in f.readlines()]
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False

    comment_symbol = get_comment_symbol(file_path)

    # Check for existing license header and remove it
    cleaned_lines = remove_existing_license_header(original_lines, comment_symbol)

    # Determine where to insert the header
    insert_index = 0

    # If the file starts with a shebang, insert after it
    if cleaned_lines and cleaned_lines[0].startswith("#!"):
        insert_index = 1

    # Create the new file content
    new_lines = []

    # Add lines before the license header (e.g., shebang)
    new_lines.extend(cleaned_lines[:insert_index])

    # Add the license header
    new_lines.extend(license_header)

    # Add an empty line after the license header if the next line isn't empty
    if insert_index < len(cleaned_lines) and cleaned_lines[insert_index].strip():
        new_lines.append("")

    # Add the rest of the original file
    new_lines.extend(cleaned_lines[insert_index:])

    # Write the updated file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for line in new_lines:
                f.write(line + "\n")
        return True
    except Exception as e:
        print(f"  Error writing file: {e}")
        return False


def fix_file_header(file_path: Path) -> bool:
    """Add or replace the required license header in a file.

    Args:
        file_path: Path to the file to fix.

    Returns:
        True if the file was successfully fixed, False otherwise.
    """
    # Check if file already has proper headers
    has_valid_header, issues = check_file_header(file_path)
    if has_valid_header:
        return True  # Nothing to fix

    # Check for multiple license headers - don't fix these automatically
    has_multiple, header_ranges = has_multiple_license_headers(file_path)
    if has_multiple:
        return False  # Don't attempt to fix files with multiple headers

    # Generate the license header
    license_header = generate_license_header(file_path)

    if is_jupyter_notebook(file_path):
        return _fix_notebook_header(file_path, license_header)
    else:
        return _fix_text_file_header(file_path, license_header)


def find_source_files(root_path: Path, extensions: Dict[str, str]) -> List[Path]:
    """Find all source files that should be checked.

    Args:
        root_path: Root directory to search for source files.
        extensions: Dictionary mapping file extensions to comment symbols.

    Returns:
        Sorted list of paths to source files that should be checked.
    """
    source_files = []

    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue

        if should_skip_path(file_path):
            continue

        if file_path.suffix.lower() in extensions:
            source_files.append(file_path)

    return sorted(source_files)


def main():
    """Main function to check license headers in source files.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(description="Check SPDX license headers in source files")
    parser.add_argument(
        "--root", type=str, default=".", help="Root directory to search for source files (default: current directory)"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to add missing headers or replace incorrect headers in files"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output including files that pass")
    parser.add_argument("--extensions", nargs="*", help="Specific file extensions to check (e.g., .py .cpp .h)")

    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: Root path '{root_path}' does not exist")
        return 1

    print(f"Checking license headers in source files under: {root_path}")

    # Filter extensions if specified
    extensions_to_check = FILE_EXTENSIONS
    if args.extensions:
        filtered_extensions = {ext: FILE_EXTENSIONS[ext] for ext in args.extensions if ext in FILE_EXTENSIONS}
        if not filtered_extensions:
            print(f"Error: None of the specified extensions {args.extensions} are supported")
            print(f"Supported extensions: {list(FILE_EXTENSIONS.keys())}")
            return 1
        extensions_to_check = filtered_extensions

    source_files = find_source_files(root_path, extensions_to_check)

    if not source_files:
        print("No source files found to check")
        return 0

    print(f"Found {len(source_files)} source files to check")

    files_with_issues = []
    files_passed = []
    files_fixed = []
    files_with_multiple_headers = []

    for file_path in source_files:
        # First check if file has multiple license headers
        has_multiple, header_ranges = has_multiple_license_headers(file_path)

        if has_multiple:
            files_with_multiple_headers.append(file_path)
            print(f"❌ ERROR: {file_path.relative_to(root_path)} has multiple license headers (lines {header_ranges})")
            continue

        has_valid_header, issues = check_file_header(file_path)

        if has_valid_header:
            files_passed.append(file_path)
            if args.verbose:
                print(f"✓ {file_path.relative_to(root_path)}")
        else:
            if args.fix:
                print(f"🔧 Fixing {file_path.relative_to(root_path)}")
                if fix_file_header(file_path):
                    files_fixed.append(file_path)
                    print(f"  ✓ Successfully added/updated license header")
                else:
                    files_with_issues.append((file_path, issues))
                    print(f"  ✗ Failed to add/update license header")
            else:
                files_with_issues.append((file_path, issues))
                print(f"✗ {file_path.relative_to(root_path)}")
                for issue in issues:
                    print(f"  - {issue}")

    print(f"\nSummary:")
    print(f"  Files checked: {len(source_files)}")
    print(f"  Files passed: {len(files_passed)}")
    if args.fix:
        print(f"  Files fixed: {len(files_fixed)}")
    print(f"  Files with issues: {len(files_with_issues)}")
    if files_with_multiple_headers:
        print(f"  Files with multiple headers: {len(files_with_multiple_headers)}")

    if files_with_multiple_headers:
        print(f"\nERROR: Files with multiple license headers found:")
        for file_path in files_with_multiple_headers:
            print(f"  {file_path.relative_to(root_path)}")
        print(f"Please manually fix these files by removing duplicate headers.")
        return 1

    if files_with_issues:
        if not args.fix:
            print(f"\nFiles with missing or incorrect license headers:")
            for file_path, _ in files_with_issues:
                print(f"  {file_path.relative_to(root_path)}")
            print(f"\nRun with --fix to automatically add missing headers or replace incorrect ones")

        return 1
    else:
        if args.fix and files_fixed:
            print(f"\n✓ Successfully fixed {len(files_fixed)} files!")
        else:
            print("\n✓ All source files have valid license headers!")
        return 0


if __name__ == "__main__":
    exit(main())
