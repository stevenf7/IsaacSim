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

"""Validate changelog and version bump for Isaac Sim extensions.

Checks that each extension has:
  - A readable version in config/extension.toml
  - A matching top entry in docs/CHANGELOG.md
  - A version bump relative to the base branch (when --base-branch is given)

Usage:
    # Validate specific extensions
    python tools/isaac/check_changelog_version.py source/extensions/isaacsim.robot.poser

    # Validate with base branch comparison
    python tools/isaac/check_changelog_version.py source/extensions/isaacsim.robot.poser \\
        --base-branch origin/main
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from repo_helpers import REPO_ROOT, read_toml_version
from term_helpers import log_fail, log_info, log_pass

_CHANGELOG_VERSION_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]")


# ---------------------------------------------------------------------------
# Version helpers
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
    """Validate changelog and version for each extension. Returns error count."""
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate changelog and version bump for Isaac Sim extensions.",
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
    args = parser.parse_args()

    ext_dirs = [p.resolve() for p in args.extensions if p.is_dir()]
    if not ext_dirs:
        print("No valid extension directories provided.", flush=True)
        return 1

    errors = check_changelog_and_version(ext_dirs, args.base_branch)
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
