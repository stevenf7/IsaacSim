#!/usr/bin/env python3
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

"""Remove generated ``## Other`` sections from python_api.md files."""

import argparse
import re
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Return the repository root based on this script location."""
    return Path(__file__).resolve().parents[2]


def is_other_heading(line: str) -> bool:
    """Return True when a line is exactly a generated Other section heading."""
    return line.strip() == "## Other"


def is_section_boundary(line: str) -> bool:
    """Return True when an Other section should stop before this line."""
    return re.match(r"^#\s+", line) is not None or re.match(r"^##(\s|$)", line) is not None


def remove_other_sections(text: str) -> str:
    """Remove every ``## Other`` section without consuming following API module headings."""
    lines = text.splitlines(keepends=True)
    output = []
    index = 0

    while index < len(lines):
        if is_other_heading(lines[index]):
            index += 1
            while index < len(lines) and not is_section_boundary(lines[index]):
                index += 1
            continue

        output.append(lines[index])
        index += 1

    cleaned = "".join(output)
    if cleaned:
        cleaned = re.sub(r"\n+\Z", "\n", cleaned)
    return cleaned


def iter_python_api_files(paths: list[Path]) -> list[Path]:
    """Expand explicit files and directories into python_api.md files."""
    files = []
    seen = set()

    for path in paths:
        if path.is_file() and path.name == "python_api.md":
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(path.rglob("python_api.md"))
        else:
            print(f"warning: skipping missing or unsupported path: {path}", file=sys.stderr)
            continue

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)

    return files


def cleanup_file(path: Path, *, check: bool, dry_run: bool) -> bool:
    """Clean a single file. Return True when it needed changes."""
    original = path.read_text(encoding="utf-8")
    cleaned = remove_other_sections(original)

    if cleaned == original:
        return False

    if not check and not dry_run:
        path.write_text(cleaned, encoding="utf-8")

    return True


def parse_args() -> argparse.Namespace:
    repo_root = get_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[repo_root / "source"],
        help="python_api.md files or directories to scan. Defaults to the repo source directory.",
    )
    parser.add_argument("--check", action="store_true", help="Exit nonzero if any file would be changed.")
    parser.add_argument("--dry-run", action="store_true", help="Print files that would change without writing them.")
    parser.add_argument("--quiet", action="store_true", help="Suppress changed-file output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = iter_python_api_files(args.paths)
    changed = []

    for path in files:
        if cleanup_file(path, check=args.check, dry_run=args.dry_run):
            changed.append(path)
            if not args.quiet:
                action = "would update" if args.check or args.dry_run else "updated"
                print(f"{action}: {path}")

    if args.check and changed:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
