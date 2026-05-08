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

"""Validate and fix test args in extension.toml files.

Ensures that all ``[[test]]`` sections use the standard set of test arguments.
Each non-startup, non-doctest ``[[test]]`` section must have an ``args`` array
matching ``STANDARD_TEST_ARGS``, and startup sections must match ``STARTUP_TEST_ARGS``.
Extension-specific arguments (marked with ``### Extension specific args``) are
preserved.

Modes:
    - **Check** (default): report non-conforming files and exit non-zero.
    - **Fix** (``--fix``): rewrite args in place to match the standard.

Usage (standalone):
    # Validate all extensions
    python tools/isaac/pre_merge/validate_test_args.py

    # Validate specific extensions
    python tools/isaac/pre_merge/validate_test_args.py --extensions isaacsim.core.utils isaacsim.ros2.core

    # Validate a single file
    python tools/isaac/pre_merge/validate_test_args.py --file path/to/extension.toml

    # Auto-fix all extensions
    python tools/isaac/pre_merge/validate_test_args.py --fix

Usage (via pre_merge_validate.py):
    # Runs automatically as part of default validation
    python tools/isaac/pre_merge/pre_merge_validate.py

    # Run only test-args check
    python tools/isaac/pre_merge/pre_merge_validate.py --test-args

    # Auto-fix
    python tools/isaac/pre_merge/pre_merge_validate.py --test-args --fix
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TextIO

# Standard arguments for regular (non-startup) test sections.
STANDARD_TEST_ARGS = [
    "--enable",
    "omni.kit.loop-isaac",
    "--reset-user",
    "--vulkan",
    "--/app/asyncRendering=0",
    "--/app/asyncRenderingLowLatency=0",
    "--/app/fastShutdown=1",
    "--/app/file/ignoreUnsavedStage=1",
    "--/app/hydraEngine/waitIdle=0",
    "--/app/player/useFixedTimeStepping=false",
    "--/app/renderer/skipWhileMinimized=0",
    "--/app/renderer/sleepMsOnFocus=0",
    "--/app/renderer/sleepMsOutOfFocus=0",
    "--/app/runLoops/main/manualModeEnabled=true",
    "--/app/runLoops/main/rateLimitEnabled=false",
    "--/app/settings/fabricDefaultStageFrameHistoryCount=3",
    "--/app/settings/persistent=0",
    "--/app/useFabricSceneDelegate=true",
    "--/app/viewport/createCameraModelRep=0",
    "--/crashreporter/skipOldDumpUpload=1",
    "--/exts/omni.usd/locking/onClose=0",
    "--/omni/kit/plugin/syncUsdLoads=1",
    "--/omni/replicator/asyncRendering=0",
    "--/omnihydra/parallelHydraSprimSync=1",
    '--/persistent/app/stage/upAxis="Z"',
    "--/persistent/app/viewport/defaults/tickRate=120",
    "--/persistent/app/viewport/displayOptions=31951",
    "--/persistent/omni/replicator/captureOnPlay=1",
    "--/persistent/omnigraph/updateToUsd=0",
    "--/persistent/physics/visualizationDisplayJoints=0",
    "--/persistent/renderer/startupMessageDisplayed=1",
    "--/persistent/simulation/defaultMetersPerUnit=1.0",
    "--/persistent/simulation/minFrameRate=15",
    "--/renderer/multiGpu/autoEnable=0",
    "--/renderer/multiGpu/enabled=0",
    "--/rtx-transient/dlssg/enabled=0",
    "--/rtx-transient/resourcemanager/enableTextureStreaming=1",
    "--/rtx/descriptorSets=360000",
    "--/rtx/hydra/enableSemanticSchema=1",
    "--/rtx/hydra/materialSyncLoads=1",
    "--/rtx/hydra/supportMultiTickRate=true",
    "--/rtx/materialDb/syncLoads=1",
    "--/rtx/newDenoiser/enabled=1",
    "--/rtx/rendering/perSensorTickTlas=true",
    "--/rtx/reservedDescriptors=900000",
]

# Arguments for startup test sections.
STARTUP_TEST_ARGS = [
    "--/app/settings/fabricDefaultStageFrameHistoryCount=3",
]


# ---------------------------------------------------------------------------
# TOML helpers
# ---------------------------------------------------------------------------


def _format_args_section(args_list: list[str]) -> list[str]:
    """Format an args list into a properly indented TOML array with one arg per line.

    Args:
        args_list: List of argument strings to format.

    Returns:
        List of formatted lines representing a TOML array.
    """
    lines = ["args = ["]
    for arg in args_list:
        arg = arg.strip()
        if not arg:
            continue
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            lines.append(f"    {arg},")
        elif '"' in arg:
            lines.append(f"    '{arg}',")
        else:
            lines.append(f'    "{arg}",')
    lines.append("]")
    return lines


def _read_lines(file_path: str | Path) -> list[str]:
    """Read a file and return its contents as a list of lines with newlines preserved.

    Args:
        file_path: Path to the file.

    Returns:
        List of line strings including newline characters.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def _write_lines(file_path: str | Path, lines: list[str]) -> None:
    """Write a list of lines to a file.

    Args:
        file_path: Path to the file.
        lines: Lines to write.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _find_args_section_end(lines: list[str], start_idx: int) -> int | None:
    """Find the closing bracket of an ``args = [...]`` array.

    Args:
        lines: All lines of the file.
        start_idx: Index of the line containing ``args =``.

    Returns:
        Index of the line with the closing ``]``, or None if not found.
    """
    if lines[start_idx].strip().endswith("]"):
        return start_idx
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith("]") or line == "]":
            return i
    return None


def _parse_existing_args(lines: list[str], start_idx: int, end_idx: int) -> list[str]:
    """Extract the argument values from an existing args array in a TOML file.

    Args:
        lines: All lines of the file.
        start_idx: Index of the ``args = [`` line.
        end_idx: Index of the ``]`` closing line.

    Returns:
        List of argument strings (unquoted).
    """
    args = []
    for i in range(start_idx, end_idx + 1):
        line = lines[i].strip()
        # Skip the opening/closing lines and comments
        if line.startswith("args") or line == "]" or line.startswith("#"):
            continue
        # Strip trailing comma and whitespace
        line = line.rstrip(",").strip()
        if not line:
            continue
        # Remove surrounding quotes
        if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
            line = line[1:-1]
        if line:
            args.append(line)
    return args


# ---------------------------------------------------------------------------
# Section discovery
# ---------------------------------------------------------------------------


def _discover_test_sections(lines: list[str]) -> list[dict]:
    """Find all ``[[test]]`` sections and their args ranges.

    Args:
        lines: All lines of the file.

    Returns:
        List of dicts with keys: start_line, is_startup, is_doctest,
        args_start, args_end, extension_specific_start.
    """
    test_sections: list[dict] = []
    current: dict | None = None
    in_test = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == "[[test]]":
            in_test = True
            current = {
                "start_line": i,
                "is_startup": False,
                "is_doctest": False,
                "args_start": None,
                "args_end": None,
                "extension_specific_start": None,
            }
            test_sections.append(current)

        if in_test and current:
            if 'name = "startup"' in stripped or "name = 'startup'" in stripped:
                current["is_startup"] = True
            if 'name = "doctest"' in stripped or "name = 'doctest'" in stripped:
                current["is_doctest"] = True
            if stripped.startswith("args ="):
                current["args_start"] = i
                args_end = _find_args_section_end(lines, i)
                current["args_end"] = args_end
                if args_end is not None:
                    for j in range(i + 1, args_end):
                        if "### Extension specific args" in lines[j]:
                            current["extension_specific_start"] = j
                            break
            if i > current["start_line"] and (stripped.startswith("[[") or stripped.startswith("[package]")):
                in_test = False

    return test_sections


# ---------------------------------------------------------------------------
# Check / Fix logic
# ---------------------------------------------------------------------------


def validate_extension_toml(file_path: str | Path, fix: bool = False, verbose: bool = False) -> list[str]:
    """Validate (and optionally fix) test args in a single extension.toml.

    Args:
        file_path: Path to the extension.toml file.
        fix: If True, rewrite the file with standardized args.
        verbose: Print detailed progress.

    Returns:
        List of human-readable error strings (empty if conforming).
    """
    file_path = str(file_path)
    errors: list[str] = []

    try:
        original_lines = _read_lines(file_path)
    except OSError as e:
        return [f"Cannot read {file_path}: {e}"]

    sections = _discover_test_sections(original_lines)
    if not sections:
        return []  # no [[test]] sections at all — nothing to validate

    result_lines = original_lines.copy() if fix else None

    for section in sorted(sections, key=lambda s: s["start_line"], reverse=True):
        if section["is_doctest"]:
            continue

        if section["args_start"] is None or section["args_end"] is None:
            # Test sections without an args array are valid (e.g., startup tests
            # that rely on defaults). Skip silently.
            continue

        # Determine expected args
        expected_args = STARTUP_TEST_ARGS if section["is_startup"] else STANDARD_TEST_ARGS

        # Parse existing standard args (before extension-specific marker)
        ext_specific_start = section["extension_specific_start"]
        std_end = (ext_specific_start - 1) if ext_specific_start is not None else section["args_end"]
        existing_args = _parse_existing_args(original_lines, section["args_start"], std_end)

        if existing_args != expected_args:
            section_type = "startup" if section["is_startup"] else "regular"
            errors.append(f"line {section['start_line'] + 1}: {section_type} [[test]] args do not match standard")

            if fix and result_lines is not None:
                formatted = _format_args_section(expected_args)
                formatted_text = [line + "\n" for line in formatted[:-1]]

                if ext_specific_start is not None:
                    ext_lines = original_lines[ext_specific_start : section["args_end"] + 1]
                    result_lines[section["args_start"] : section["args_end"] + 1] = formatted_text + ext_lines
                else:
                    formatted_text.append(formatted[-1] + "\n")
                    result_lines[section["args_start"] : section["args_end"] + 1] = formatted_text

    if fix and result_lines is not None and errors:
        _write_lines(file_path, result_lines)
        if verbose:
            print(f"  Fixed: {file_path}")

    return errors


# ---------------------------------------------------------------------------
# Repo helpers (standalone mode)
# ---------------------------------------------------------------------------


def _find_repo_root() -> Path | None:
    """Walk up from cwd to find the repo root (contains source/extensions).

    Returns:
        Repo root path, or None.
    """
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / "source" / "extensions").is_dir():
            return current
        current = current.parent
    return None


def _find_extension_tomls(repo_root: Path, extension_names: list[str] | None = None) -> list[Path]:
    """Collect extension.toml files to validate.

    Args:
        repo_root: Repository root path.
        extension_names: If provided, only include these extensions.

    Returns:
        Sorted list of extension.toml paths.
    """
    toml_files: list[Path] = []
    search_dirs = [
        repo_root / "source" / "extensions",
        repo_root / "source" / "internal_extensions",
    ]

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for toml in search_dir.rglob("extension.toml"):
            if extension_names is not None:
                ext_dir = toml.parent.parent  # config/extension.toml -> ext_root
                if ext_dir.name not in extension_names:
                    continue
            toml_files.append(toml)

    return sorted(toml_files)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        Configured parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate and fix test args in extension.toml files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Validate all extension.toml files (default when no --file is given).",
    )
    group.add_argument("--file", type=Path, help="Validate a single extension.toml file.")
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=None,
        metavar="EXT",
        help="Validate only the named extensions.",
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix non-conforming args in place.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Standalone entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 if all clean, 1 if issues found/fixed).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.file:
        if not args.file.exists():
            print(f"Error: {args.file} not found.")
            return 1
        all_errors = validate_extension_toml(args.file, fix=args.fix, verbose=args.verbose)
        if all_errors:
            for err in all_errors:
                print(f"  {args.file}: {err}")
            if args.fix:
                print(f"Fixed {len(all_errors)} issue(s) in {args.file}.")
            return 1
        print(f"{args.file}: OK")
        return 0

    repo_root = _find_repo_root()
    if not repo_root:
        print("Error: could not find repository root (containing source/extensions).")
        return 1

    toml_files = _find_extension_tomls(repo_root, extension_names=args.extensions)
    if not toml_files:
        print("No extension.toml files found.")
        return 1

    total_errors = 0
    files_with_errors = 0

    for toml_path in toml_files:
        rel = toml_path.relative_to(repo_root)
        errors = validate_extension_toml(toml_path, fix=args.fix, verbose=args.verbose)
        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            for err in errors:
                print(f"  {rel}: {err}")
        elif args.verbose:
            print(f"  {rel}: OK")

    if total_errors:
        action = "fixed" if args.fix else "found"
        print(f"\n{total_errors} issue(s) {action} in {files_with_errors} file(s).")
        return 1

    print(f"All {len(toml_files)} extension.toml files have conforming test args.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
