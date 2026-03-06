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

"""Repository layout, extension discovery, and git helpers for Isaac Sim tools.

Provides constants and functions shared by the pre-commit orchestrator, the
changelog validator, the extension test runner, and similar tooling scripts.
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools" / "isaac" / "pre_merge"

EXTENSION_ROOTS = [
    REPO_ROOT / "source" / "extensions",
    REPO_ROOT / "source" / "internal_extensions",
    REPO_ROOT / "source" / "deprecated",
]

APPS_DIR = REPO_ROOT / "source" / "apps"
APP_SETUP_EXT = "isaacsim.app.setup"

_IS_WINDOWS = platform.system() == "Windows"
BUILD_PLATFORM = "windows-x86_64" if _IS_WINDOWS else "linux-x86_64"
BUILD_DIR = REPO_ROOT / "_build" / BUILD_PLATFORM / "release"
TEST_SCRIPT_EXT = ".bat" if _IS_WINDOWS else ".sh"


# ---------------------------------------------------------------------------
# Extension discovery
# ---------------------------------------------------------------------------


def extension_for_file(file_path: Path) -> Path | None:
    """Return the extension directory that contains the given file path, or None.

    Args:
        file_path: Path to the file to look up.

    Returns:
        Extension directory path if found, otherwise None.
    """
    for root in EXTENSION_ROOTS:
        try:
            rel = file_path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        ext_name = rel.parts[0] if rel.parts else None
        if not ext_name:
            continue
        ext_dir = root / ext_name
        if (ext_dir / "config" / "extension.toml").exists():
            return ext_dir
    return None


def affected_extensions(files: list[Path]) -> list[Path]:
    """Return unique, sorted list of extension directories touched by the given files.

    Args:
        files: List of file paths to check.

    Returns:
        Sorted list of extension directory paths.
    """
    seen: set[Path] = set()
    for f in files:
        ext = extension_for_file(f)
        if ext and ext.exists():
            seen.add(ext)
    return sorted(seen)


def all_extensions() -> list[Path]:
    """Return every extension directory across all extension roots.

    A directory is considered an extension only if it contains
    ``config/extension.toml``.

    Returns:
        Sorted list of extension directory paths.
    """
    exts: set[Path] = set()
    for root in EXTENSION_ROOTS:
        if root.exists():
            for child in root.iterdir():
                if child.is_dir() and (child / "config" / "extension.toml").exists():
                    exts.add(child)
    return sorted(exts)


def all_extension_names() -> list[str]:
    """Collect every extension directory name across all extension roots.

    Returns:
        List of extension directory names.
    """
    return [ext.name for ext in all_extensions()]


def has_apps_changes(files: list[Path]) -> bool:
    """Return True if any file in the given list lives under ``source/apps/``.

    Args:
        files: List of file paths to check.

    Returns:
        True if any file is under source/apps, otherwise False.
    """
    for f in files:
        try:
            f.resolve().relative_to(APPS_DIR.resolve())
            return True
        except ValueError:
            continue
    return False


# ---------------------------------------------------------------------------
# TOML helpers
# ---------------------------------------------------------------------------


def _regex_parse_toml(text: str) -> dict[str, dict]:
    """Minimal regex-based TOML parser for ``[section]`` / ``key = value`` files.

    Only handles the subset of TOML used by ``extension.toml`` (flat sections
    with simple string / number / boolean values).  Used as a last-resort
    fallback when no proper TOML library is available.

    Args:
        text: Raw TOML file contents.

    Returns:
        Parsed TOML data as nested dictionaries.
    """
    result: dict = {}
    current: dict = result
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            current = result
            for part in section_name.split("."):
                current = current.setdefault(part, {})
            continue
        if "=" in stripped:
            key, raw = stripped.split("=", 1)
            key = key.strip().strip('"')
            raw = raw.strip()
            if raw.startswith('"') and raw.endswith('"'):
                current[key] = raw[1:-1]
            elif raw.isdigit():
                current[key] = int(raw)
            elif raw.lower() == "true":
                current[key] = True
            elif raw.lower() == "false":
                current[key] = False
            else:
                current[key] = raw
    return result


def load_toml(path: Path) -> dict:
    """Load a TOML file using the best available library.

    Tries ``tomli`` (fast, pure-Python) -> ``tomlkit`` (preserves style) ->
    ``toml`` (popular) -> regex fallback.

    Args:
        path: Path to the TOML file.

    Returns:
        Parsed dict.

    """
    for loader_name in ("tomli", "tomlkit", "toml"):
        try:
            mod = __import__(loader_name)
            if loader_name == "tomli":
                with open(path, "rb") as fb:
                    return mod.load(fb)
            with open(path) as ft:
                return mod.load(ft)
        except ImportError:
            continue
        except Exception:
            continue
    return _regex_parse_toml(path.read_text())


# ---------------------------------------------------------------------------
# extension.toml helpers
# ---------------------------------------------------------------------------


def read_toml_version(ext_path: Path) -> str | None:
    """Read ``[package].version`` from an extension's ``config/extension.toml``.

    Args:
        ext_path: Path to the extension directory.

    Returns:
        Version string if found, otherwise None.
    """
    toml_path = ext_path / "config" / "extension.toml"
    if not toml_path.exists():
        return None
    data = load_toml(toml_path)
    return data.get("package", {}).get("version")


def parse_extension_deps(ext_path: Path) -> list[str]:
    """Extract dependency names from an extension's ``config/extension.toml``.

    Args:
        ext_path: Path to the extension directory.

    Returns:
        List of dependency extension names.
    """
    toml_path = ext_path / "config" / "extension.toml"
    if not toml_path.exists():
        return []
    data = load_toml(toml_path)
    return list(data.get("dependencies", {}).keys())


def build_reverse_deps() -> dict[str, set[str]]:
    """Build a reverse dependency map across all extension roots.

    Returns:
        Dict mapping each extension name to the set of extension names
        that declare it as a direct dependency.
    """
    reverse: dict[str, set[str]] = {}
    for root in EXTENSION_ROOTS:
        if not root.exists():
            continue
        for child in root.iterdir():
            if not child.is_dir():
                continue
            for dep in parse_extension_deps(child):
                reverse.setdefault(dep, set()).add(child.name)
    return reverse


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_diff_names(extra_args: list[str]) -> set[Path]:
    """Run ``git diff --name-only --diff-filter=ACMR`` and return resolved paths.

    Args:
        extra_args: Extra arguments to pass to git diff.

    Returns:
        Set of resolved file paths.
    """
    cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", *extra_args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    paths: set[Path] = set()
    if proc.returncode == 0 and proc.stdout.strip():
        for line in proc.stdout.strip().splitlines():
            paths.add(REPO_ROOT / line.strip())
    return paths


def _uncommitted_files() -> set[Path]:
    """Return staged and unstaged working-tree changes (excludes deleted files).

    Returns:
        Set of modified file paths.
    """
    return _git_diff_names([]) | _git_diff_names(["--staged"])


def _untracked_files() -> set[Path]:
    """Return new files that are not yet tracked by git.

    Returns:
        Set of untracked file paths.
    """
    cmd = ["git", "ls-files", "--others", "--exclude-standard"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    paths: set[Path] = set()
    if proc.returncode == 0 and proc.stdout.strip():
        for line in proc.stdout.strip().splitlines():
            if line.strip():
                paths.add(REPO_ROOT / line.strip())
    return paths


def get_uncommitted_files() -> set[Path]:
    """Return staged, unstaged, and untracked files in the working tree.

    This is useful for ``--diff-only`` modes that need the full set of
    locally-changed files (modified *and* newly created).

    Returns:
        Set of file paths.
    """
    return _uncommitted_files() | _untracked_files()


def _ref_exists(ref: str) -> bool:
    """Check whether a git ref (branch, tag, or commit) exists.

    Args:
        ref: Git ref to verify.

    Returns:
        True if the ref exists, otherwise False.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode == 0


def _list_remotes() -> list[str]:
    """List configured git remote names.

    Returns:
        List of remote names.
    """
    proc = subprocess.run(
        ["git", "remote"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        return []
    return [r.strip() for r in proc.stdout.strip().splitlines() if r.strip()]


def detect_base_branch() -> str | None:
    """Auto-detect the mainline integration branch this feature branch diverged from.

    Search order per remote: develop, main, master.
    Remote priority: ``main``, ``origin``, then any others alphabetically.

    Returns:
        Base branch ref if found, otherwise None.
    """
    remotes = _list_remotes()
    if not remotes:
        for name in ["develop", "main", "master"]:
            if _ref_exists(name):
                return name
        return None

    preferred = []
    for pref in ["main", "origin"]:
        if pref in remotes:
            preferred.append(pref)
    rest = sorted(r for r in remotes if r not in preferred)
    ordered_remotes = preferred + rest

    for remote in ordered_remotes:
        for branch in ["develop", "main", "master"]:
            candidate = f"{remote}/{branch}"
            if _ref_exists(candidate):
                return candidate

    return None


def get_branch_files(base_ref: str) -> set[Path]:
    """Return files that differ from base at ``HEAD`` since the merge-base.

    Uses a direct tree diff from ``merge-base(base_ref, HEAD)`` to ``HEAD``,
    so files that were touched and later reverted are not reported.

    Args:
        base_ref: Base branch or ref to compare against.

    Returns:
        Set of changed file paths.
    """
    merge_base_proc = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if merge_base_proc.returncode != 0:
        return set()
    merge_base = merge_base_proc.stdout.strip()

    proc = subprocess.run(
        [
            "git",
            "diff",
            "--diff-filter=ACMR",
            "--name-only",
            f"{merge_base}..HEAD",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    paths: set[Path] = set()
    if proc.returncode == 0 and proc.stdout.strip():
        for line in proc.stdout.strip().splitlines():
            if line.strip():
                paths.add(REPO_ROOT / line.strip())
    return paths


def get_all_modified_files(base_branch: str | None) -> tuple[list[Path], str | None]:
    """Return sorted file list and resolved base branch.

    Collects the union of branch-level changes (since the merge-base) and
    uncommitted working-tree changes.  If base_branch is None, attempts
    auto-detection via :func:`detect_base_branch`.

    Args:
        base_branch: Base branch to compare against, or None for auto-detection.

    Returns:
        Tuple of (sorted list of modified file paths, resolved base branch ref).
    """
    resolved_base = base_branch or detect_base_branch()

    paths: set[Path] = set()
    if resolved_base:
        paths |= get_branch_files(resolved_base)
    paths |= _uncommitted_files()

    return sorted(paths), resolved_base
