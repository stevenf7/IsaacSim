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

"""Check and optionally fix SPDX license headers.

This utility is the pre-merge home for license validation and supports:

- Repository scans via ``--root``.
- Targeted checks via ``--files`` (used by pre-merge validation).
- Optional auto-fixing via ``--fix``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Ensure this script's directory is on sys.path so repo_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import REPO_ROOT  # noqa: E402

FILE_EXTENSIONS: dict[str, str] = {
    ".py": "#",
    ".cpp": "//",
    ".cc": "//",
    ".cxx": "//",
    ".c": "//",
    ".h": "//",
    ".hpp": "//",
    ".hxx": "//",
    ".cu": "//",
    ".cuh": "//",
    ".yaml": "#",
    ".yml": "#",
    ".ipynb": "#",
    ".lua": "--",
    ".sh": "#",
    ".bat": "::",
}

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

EXCLUDED_FILES = {"__init__.py", "setup.py", "conftest.py"}

COPYRIGHT_RE = re.compile(
    r"SPDX-FileCopyrightText:\s*Copyright \(c\)\s*(\d{4}(?:-\d{4})?) NVIDIA CORPORATION & AFFILIATES\. All rights reserved\."
)
LICENSE_RE = re.compile(r"SPDX-License-Identifier:\s*Apache-2\.0")
PROPRIETARY_LICENSE_RE = re.compile(r"SPDX-License-Identifier:\s*LicenseRef-NvidiaProprietary")

_LEGACY_COPYRIGHT_RE = re.compile(r"Copyright \(c\)\s*\d{4}(?:[,-]\s*\d{4})?,?\s*NVIDIA CORPORATION")

TEMPLATE = [
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

PROPRIETARY_TEMPLATE = [
    "SPDX-FileCopyrightText: Copyright (c) {year} NVIDIA CORPORATION & AFFILIATES. All rights reserved.",
    "SPDX-License-Identifier: LicenseRef-NvidiaProprietary",
    "",
    "NVIDIA CORPORATION, its affiliates and licensors retain all intellectual",
    "property and proprietary rights in and to this material, related",
    "documentation and any modifications thereto. Any use, reproduction,",
    "disclosure or distribution of this material and related documentation",
    "without an express license agreement from NVIDIA CORPORATION or",
    "its affiliates is strictly prohibited.",
]

_INTERNAL_EXTENSIONS_PATH = REPO_ROOT / "source" / "internal_extensions"


def _is_internal_extension(file_path: Path) -> bool:
    try:
        file_path.resolve().relative_to(_INTERNAL_EXTENSIONS_PATH.resolve())
        return True
    except ValueError:
        return False


def _normalize_content(line: str, comment_symbol: str) -> str:
    stripped = line.strip()
    if stripped.startswith(comment_symbol):
        return stripped[len(comment_symbol) :].strip()
    return stripped


def _extract_copyright_year(line: str) -> str | None:
    m = COPYRIGHT_RE.search(line)
    if not m:
        return None
    return m.group(1)


def _current_year() -> str:
    return str(datetime.now().year)


def _compute_year_range(existing_year: str | None) -> str:
    current_year = _current_year()
    if not existing_year:
        return current_year

    if "-" in existing_year:
        start, _ = existing_year.split("-", 1)
        start = start.strip()
        return current_year if start == current_year else f"{start}-{current_year}"

    return current_year if existing_year == current_year else f"{existing_year}-{current_year}"


def should_skip_path(path: Path) -> bool:
    """Return whether a path should be excluded from license checks.

    Args:
        path: File path to evaluate.

    Returns:
        ``True`` if the file is excluded by directory or filename rules.
    """
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    if path.name in EXCLUDED_FILES:
        return True
    return False


def _read_lines(file_path: Path, line_limit: int | None = 80) -> list[str]:
    if file_path.suffix.lower() == ".ipynb":
        with open(file_path, encoding="utf-8") as f:
            notebook = json.load(f)
        cells = notebook.get("cells", [])
        if not cells:
            return []
        source = cells[0].get("source", [])
        if isinstance(source, str):
            lines = source.splitlines()
        else:
            lines = [line.rstrip("\n") for line in source]
        return lines[:line_limit] if line_limit is not None else lines

    with open(file_path, encoding="utf-8", errors="ignore") as f:
        lines = [line.rstrip("\n\r") for line in f.readlines()]
    return lines[:line_limit] if line_limit is not None else lines


def _multiple_header_count(lines: list[str], comment_symbol: str) -> int:
    count = 0
    for line in lines[:50]:
        content = _normalize_content(line, comment_symbol)
        if "SPDX-FileCopyrightText:" in content and "NVIDIA" in content:
            count += 1
    return count


def check_file_header(file_path: Path) -> tuple[bool, list[str]]:
    """Validate SPDX header lines for one source file.

    Args:
        file_path: Source file path to validate.

    Returns:
        A tuple ``(ok, issues)`` where ``ok`` indicates success and
        ``issues`` lists the detected header problems.
    """
    comment_symbol = FILE_EXTENSIONS[file_path.suffix.lower()]
    try:
        lines = _read_lines(file_path, line_limit=80)
    except Exception as exc:
        return False, [f"Could not read file: {exc}"]

    if not lines:
        return False, ["File is empty or has no content to check"]

    issues: list[str] = []
    copyright_line_count = 0
    license_line_count = 0
    is_internal = _is_internal_extension(file_path)

    for idx, line in enumerate(lines[:30], start=1):
        content = _normalize_content(line, comment_symbol)
        if "SPDX-FileCopyrightText:" in content:
            copyright_line_count += 1
            if not COPYRIGHT_RE.fullmatch(content):
                issues.append(f"Line {idx}: Invalid SPDX copyright format")
        if "SPDX-License-Identifier:" in content:
            license_line_count += 1
            license_valid = LICENSE_RE.fullmatch(content)
            if is_internal:
                license_valid = license_valid or PROPRIETARY_LICENSE_RE.fullmatch(content)
            if not license_valid:
                issues.append(f"Line {idx}: Invalid SPDX license identifier")

    if copyright_line_count == 0:
        issues.append("Missing SPDX-FileCopyrightText line")
    if license_line_count == 0:
        issues.append("Missing SPDX-License-Identifier line")
    if copyright_line_count > 1:
        issues.append("Multiple SPDX-FileCopyrightText lines detected")

    for idx, line in enumerate(lines[:60], start=1):
        content = _normalize_content(line, comment_symbol)
        if _LEGACY_COPYRIGHT_RE.search(content) and not COPYRIGHT_RE.search(content):
            issues.append(f"Line {idx}: Legacy proprietary NVIDIA copyright header found")
            break

    return len(issues) == 0, issues


def _generate_header(file_path: Path, year: str, *, proprietary: bool = False) -> list[str]:
    comment_symbol = FILE_EXTENSIONS[file_path.suffix.lower()]
    template = PROPRIETARY_TEMPLATE if proprietary else TEMPLATE
    out: list[str] = []
    for line in template:
        rendered = line.format(year=year)
        if rendered:
            out.append(f"{comment_symbol} {rendered}")
        else:
            out.append(comment_symbol)
    return out


_APACHE_HEADER_MARKERS = {
    "SPDX-License-Identifier:",
    "Licensed under the Apache License",
    "you may not use this file except in compliance",
    "You may obtain a copy of the License at",
    "http://www.apache.org/licenses/LICENSE-2.0",
    "Unless required by applicable law",
    'distributed on an "AS IS" BASIS',
    "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND",
    "See the License for the specific language governing",
    "limitations under the License",
}

_PROPRIETARY_SPDX_MARKERS = {
    "NVIDIA CORPORATION, its affiliates and licensors retain all intellectual",
    "property and proprietary rights in and to this material",
    "documentation and any modifications thereto",
    "disclosure or distribution of this material",
    "without an express license agreement from NVIDIA CORPORATION",
    "its affiliates is strictly prohibited",
}


def _is_header_line(content: str, stripped: str, comment_symbol: str) -> bool:
    if stripped == "" or stripped == comment_symbol:
        return True
    return any(marker in content for marker in _APACHE_HEADER_MARKERS) or any(
        marker in content for marker in _PROPRIETARY_SPDX_MARKERS
    )


def _strip_existing_header(lines: list[str], comment_symbol: str) -> list[str]:
    start = -1
    end = -1
    for i, line in enumerate(lines[:60]):
        content = _normalize_content(line, comment_symbol)
        if "SPDX-FileCopyrightText:" in content:
            start = i
            end = i + 1
            break

    if start == -1:
        return _strip_legacy_header(lines, comment_symbol)

    for j in range(start + 1, min(len(lines), start + 30)):
        content = _normalize_content(lines[j], comment_symbol)
        stripped = lines[j].strip()
        if _is_header_line(content, stripped, comment_symbol):
            end = j + 1
        else:
            break

    while end < len(lines) and lines[end].strip() == "":
        end += 1

    remaining = lines[:start] + lines[end:]
    return _strip_legacy_header(remaining, comment_symbol)


_LEGACY_HEADER_MARKERS = {
    "NVIDIA CORPORATION and its licensors retain all intellectual property",
    "and proprietary rights in and to this software",
    "Any use, reproduction, disclosure or",
    "distribution of this software and related documentation",
    "license agreement from NVIDIA CORPORATION is strictly prohibited",
}


def _strip_legacy_header(lines: list[str], comment_symbol: str) -> list[str]:
    """Remove old-style proprietary NVIDIA copyright blocks."""
    start = -1
    end = -1
    for i, line in enumerate(lines[:60]):
        content = _normalize_content(line, comment_symbol)
        if _LEGACY_COPYRIGHT_RE.search(content):
            start = i
            end = i + 1
            break

    if start == -1:
        return lines

    for j in range(start + 1, min(len(lines), start + 30)):
        content = _normalize_content(lines[j], comment_symbol)
        stripped = lines[j].strip()
        if stripped == "" or stripped == comment_symbol:
            end = j + 1
        elif any(marker in content for marker in _LEGACY_HEADER_MARKERS):
            end = j + 1
        else:
            break

    while end < len(lines) and lines[end].strip() == "":
        end += 1

    return lines[:start] + lines[end:]


def fix_file_header(file_path: Path) -> bool:
    """Attempt to insert or repair the SPDX header in a single file.

    Args:
        file_path: Source file path to repair.

    Returns:
        ``True`` if the file was successfully rewritten, otherwise ``False``.
    """
    comment_symbol = FILE_EXTENSIONS[file_path.suffix.lower()]
    try:
        lines = _read_lines(file_path, line_limit=None)
    except Exception:
        return False

    if not lines:
        return False

    if _multiple_header_count(lines, comment_symbol) > 1:
        return False

    existing_year: str | None = None
    for line in lines[:30]:
        existing_year = _extract_copyright_year(_normalize_content(line, comment_symbol))
        if existing_year:
            break
    year = _compute_year_range(existing_year)

    use_proprietary = False
    if _is_internal_extension(file_path):
        has_proprietary = any(
            PROPRIETARY_LICENSE_RE.search(_normalize_content(line, comment_symbol)) for line in lines[:30]
        )
        has_apache = any(LICENSE_RE.search(_normalize_content(line, comment_symbol)) for line in lines[:30])
        use_proprietary = has_proprietary or not has_apache

    license_header = _generate_header(file_path, year, proprietary=use_proprietary)

    if file_path.suffix.lower() == ".ipynb":
        try:
            with open(file_path, encoding="utf-8") as f:
                notebook = json.load(f)
            cells = notebook.setdefault("cells", [])
            if not cells:
                notebook["cells"] = [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "source": ["\n".join(license_header) + "\n"],
                        "outputs": [],
                        "execution_count": None,
                    }
                ]
            else:
                first = cells[0]
                source = first.get("source", [])
                if isinstance(source, str):
                    source_lines = source.splitlines()
                else:
                    source_lines = [line.rstrip("\n") for line in source]
                cleaned = _strip_existing_header(source_lines, comment_symbol)
                new_content = "\n".join(license_header + [""] + cleaned) + "\n"
                first["source"] = [new_content]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True
        except Exception:
            return False

    cleaned_lines = _strip_existing_header(lines, comment_symbol)
    insert_at = 1 if cleaned_lines and cleaned_lines[0].startswith("#!") else 0
    new_lines = cleaned_lines[:insert_at] + license_header + [""]
    new_lines.extend(cleaned_lines[insert_at:])
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for line in new_lines:
                f.write(line + "\n")
        return True
    except Exception:
        return False


def _discover_from_root(root_path: Path, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        if should_skip_path(file_path):
            continue
        if file_path.suffix.lower() in extensions:
            files.append(file_path)
    return sorted(files)


def _normalize_input_file(path_text: str, root_path: Path) -> Path:
    p = Path(path_text)
    if not p.is_absolute():
        p = (root_path / p).resolve()
    return p


def _collect_target_files(root_path: Path, args: argparse.Namespace) -> list[Path]:
    extensions = set(FILE_EXTENSIONS.keys())
    if args.extensions:
        extensions &= set(args.extensions)
        if not extensions:
            return []

    if args.files:
        selected: list[Path] = []
        for raw_path in args.files:
            file_path = _normalize_input_file(raw_path, root_path)
            if not file_path.exists() or not file_path.is_file():
                continue
            if file_path.suffix.lower() not in extensions:
                continue
            if should_skip_path(file_path):
                continue
            selected.append(file_path)
        return sorted(set(selected))

    return _discover_from_root(root_path, extensions)


def run_check(
    root_path: Path,
    files: list[Path],
    *,
    fix: bool = False,
    verbose: bool = False,
) -> int:
    """Run header validation (and optional fixing) for selected files.

    Args:
        root_path: Repository root used for relative display.
        files: Files to validate.
        fix: If ``True``, attempt automatic repair.
        verbose: If ``True``, print pass lines for clean files.

    Returns:
        int: ``0`` on success, ``1`` on failure.
    """
    if not files:
        print("No source files found to check")
        return 0

    print(f"Checking license headers under: {root_path}")
    print(f"Found {len(files)} source files to check")

    files_with_issues: list[tuple[Path, list[str]]] = []
    files_with_multiple: list[Path] = []
    files_fixed: list[Path] = []
    files_passed = 0

    for file_path in files:
        comment_symbol = FILE_EXTENSIONS[file_path.suffix.lower()]
        try:
            lines = _read_lines(file_path, line_limit=80)
        except Exception as exc:
            files_with_issues.append((file_path, [str(exc)]))
            continue

        if _multiple_header_count(lines, comment_symbol) > 1:
            files_with_multiple.append(file_path)
            print(f"ERROR: {file_path.relative_to(root_path)} has multiple license headers")
            continue

        ok, issues = check_file_header(file_path)
        if ok:
            files_passed += 1
            if verbose:
                print(f"PASS {file_path.relative_to(root_path)}")
            continue

        if fix:
            print(f"Fixing {file_path.relative_to(root_path)}")
            if fix_file_header(file_path):
                files_fixed.append(file_path)
                print("  OK")
                continue

        files_with_issues.append((file_path, issues))
        print(f"FAIL {file_path.relative_to(root_path)}")
        for issue in issues:
            print(f"  - {issue}")

    print("\nSummary:")
    print(f"  Files checked: {len(files)}")
    print(f"  Files passed: {files_passed}")
    if fix:
        print(f"  Files fixed: {len(files_fixed)}")
    print(f"  Files with issues: {len(files_with_issues)}")
    if files_with_multiple:
        print(f"  Files with multiple headers: {len(files_with_multiple)}")

    if files_with_multiple:
        print("\nFiles with multiple license headers were found. Fix these manually.")
        for file_path in files_with_multiple:
            print(f"  {file_path.relative_to(root_path)}")
        return 1

    if files_with_issues:
        if not fix:
            print("\nRun with --fix to attempt automatic repair.")
        return 1

    print("\nAll source files have valid license headers.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line parser for this tool.

    Returns:
        Configured ``ArgumentParser`` instance.
    """
    parser = argparse.ArgumentParser(description="Check SPDX license headers in source files")
    parser.add_argument("--root", type=str, default=str(REPO_ROOT), help="Root directory to search for source files")
    parser.add_argument("--fix", action="store_true", help="Attempt to add or repair headers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file pass output")
    parser.add_argument("--extensions", nargs="*", help="Specific file extensions to check (e.g., .py .cpp .h)")
    parser.add_argument(
        "--files",
        nargs="+",
        default=None,
        help="Explicit list of files to check (absolute or root-relative). Overrides recursive root scan.",
    )
    return parser


def main() -> int:
    """Parse arguments and execute the license header check workflow.

    Returns:
        int: ``0`` on success, ``1`` on failure.
    """
    parser = build_parser()
    args = parser.parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: root path '{root_path}' does not exist")
        return 1

    files = _collect_target_files(root_path, args)
    return run_check(root_path, files, fix=args.fix, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
