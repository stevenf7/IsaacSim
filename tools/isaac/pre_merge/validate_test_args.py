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

"""Validate and fix ``[[test]]`` sections in extension.toml files.

Two independent checks are performed (select with ``--check``):

1. **args** — every non-startup, non-doctest ``[[test]]`` section must have an
   ``args`` array matching ``STANDARD_TEST_ARGS`` (startup sections must match
   ``STARTUP_TEST_ARGS``). Extension-specific arguments (marked with
   ``### Extension specific args``) are preserved.
2. **stdout** — every ``[[test]]`` section must contain the required
   ``stdoutFailPatterns.exclude`` entries listed in ``REQUIRED_STDOUT_FAIL_EXCLUDE``
   (e.g. ``'*The NumPy module was reloaded*'``), so benign warnings do not fail
   tests. Missing entries are prepended to an existing exclude array, or a new
   ``stdoutFailPatterns.exclude`` block is inserted in field order.

Modes:
    - **Check** (default): report non-conforming files and exit non-zero.
    - **Fix** (``--fix``): rewrite sections in place to satisfy the checks.

Usage (standalone):
    # Validate all extensions (both checks)
    python tools/isaac/pre_merge/validate_test_args.py

    # Run only the stdoutFailPatterns.exclude standardization
    python tools/isaac/pre_merge/validate_test_args.py --check stdout

    # Auto-fix only the stdoutFailPatterns.exclude entries across all extensions
    python tools/isaac/pre_merge/validate_test_args.py --check stdout --fix

    # Validate specific extensions
    python tools/isaac/pre_merge/validate_test_args.py --extensions isaacsim.core.utils isaacsim.ros2.core

    # Validate a single file
    python tools/isaac/pre_merge/validate_test_args.py --file path/to/extension.toml

    # Auto-fix all extensions (both checks)
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
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    tomllib = None  # type: ignore[assignment]

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

# stdoutFailPatterns.exclude entries that every [[test]] section must contain.
# These suppress benign warnings that would otherwise be flagged as test failures.
# Entries are written with single quotes, one per line, in the order listed here.
REQUIRED_STDOUT_FAIL_EXCLUDE = [
    "*The NumPy module was reloaded*",
]

# Marker comment separating the standard required excludes (above) from the
# test-suite-specific excludes already present in an extension's exclude array.
TEST_SUITE_SPECIFIC_MARKER = "### test-suite specific args"

# Standard indentation for entries inside a stdoutFailPatterns.exclude array.
_EXCLUDE_INDENT = "    "


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
# TOML parsing (read-only validation + value extraction via stdlib tomllib)
# ---------------------------------------------------------------------------


def _toml_parse(text: str) -> tuple[dict | None, str | None]:
    """Parse TOML text using stdlib ``tomllib`` (read-only).

    ``tomllib`` cannot serialize, so it is used only to (a) validate syntax and
    (b) read values; all edits are performed line-based to preserve formatting.

    Args:
        text: TOML document text.

    Returns:
        Tuple of (parsed_data, error_message). ``parsed_data`` is ``None`` when
        ``tomllib`` is unavailable (older interpreter) or parsing failed;
        ``error_message`` is ``None`` unless parsing raised a decode error.
    """
    if tomllib is None:
        return None, None
    try:
        return tomllib.loads(text), None
    except tomllib.TOMLDecodeError as exc:
        return None, str(exc)


def _unscoped_excludes(test_table: dict[str, Any]) -> list[str]:
    """Return a test table's unscoped ``stdoutFailPatterns.exclude`` entries.

    Args:
        test_table: A parsed ``[[test]]`` table.

    Returns:
        List of exclude pattern strings (empty if none declared).
    """
    sfp = test_table.get("stdoutFailPatterns")
    if isinstance(sfp, dict):
        exclude = sfp.get("exclude")
        if isinstance(exclude, list):
            return [e for e in exclude if isinstance(e, str)]
    return []


def _split_inline_array(line: str) -> tuple[str, list[str]]:
    """Split a single-line ``key = [ ... ]`` array into its prefix and entries.

    Args:
        line: A line containing an inline array (``[`` and closing ``]``).

    Returns:
        Tuple of (text up to and including ``[``, list of raw entry tokens with
        quoting preserved). Entries are empty for ``[]``.
    """
    open_pos = line.index("[")
    close_pos = line.rindex("]")
    head = line[: open_pos + 1]
    inner = line[open_pos + 1 : close_pos].strip()
    entries = [tok.strip() for tok in inner.split(",") if tok.strip()] if inner else []
    return head, entries


# ---------------------------------------------------------------------------
# Section discovery
# ---------------------------------------------------------------------------


def _discover_test_sections(lines: list[str]) -> list[dict]:
    """Find all ``[[test]]`` sections and the ranges of their relevant arrays.

    A section spans from its ``[[test]]`` header to the next top-level header
    (any line whose first non-whitespace character is ``[``) or end of file.

    Args:
        lines: All lines of the file.

    Returns:
        List of dicts with keys: start_line, end_line, is_startup, is_doctest,
        args_start, args_end, extension_specific_start, exclude_start,
        exclude_end, include_start.
    """
    starts = [i for i, line in enumerate(lines) if line.strip() == "[[test]]"]
    test_sections: list[dict] = []

    for start in starts:
        # Section ends at the next top-level header ('[' or '[[') or EOF.
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].lstrip().startswith("["):
                end = j
                break

        section: dict = {
            "start_line": start,
            "end_line": end,
            "is_startup": False,
            "is_doctest": False,
            "args_start": None,
            "args_end": None,
            "extension_specific_start": None,
            "exclude_start": None,
            "exclude_end": None,
            "include_start": None,
        }

        for i in range(start, end):
            stripped = lines[i].strip()

            if 'name = "startup"' in stripped or "name = 'startup'" in stripped:
                section["is_startup"] = True
            if 'name = "doctest"' in stripped or "name = 'doctest'" in stripped:
                section["is_doctest"] = True

            if stripped.startswith("args ="):
                section["args_start"] = i
                args_end = _find_args_section_end(lines, i)
                section["args_end"] = args_end
                if args_end is not None:
                    for j in range(i + 1, args_end):
                        if "### Extension specific args" in lines[j]:
                            section["extension_specific_start"] = j
                            break

            # Unscoped stdoutFailPatterns.exclude block (ignores filter-scoped or
            # pythonTests.exclude which begin with a quote or different key).
            if stripped.startswith("stdoutFailPatterns.exclude") and section["exclude_start"] is None:
                section["exclude_start"] = i
                section["exclude_end"] = _find_args_section_end(lines, i)

            if stripped.startswith("stdoutFailPatterns.include") and section["include_start"] is None:
                section["include_start"] = i

        test_sections.append(section)

    return test_sections


# ---------------------------------------------------------------------------
# Check / Fix logic
# ---------------------------------------------------------------------------

# Names of the individual checks this module can run.
ALL_CHECKS = ("args", "stdout")


def _validate_fix_args(lines: list[str], fix: bool) -> tuple[list[str], list[str]]:
    """Validate (and optionally fix) the ``args`` arrays of all test sections.

    Args:
        lines: Current file lines (with newlines).
        fix: Whether to apply fixes.

    Returns:
        Tuple of (errors, possibly-modified lines).
    """
    errors: list[str] = []
    sections = _discover_test_sections(lines)
    result_lines = lines.copy()

    for section in sorted(sections, key=lambda s: s["start_line"], reverse=True):
        if section["is_doctest"]:
            continue

        if section["args_start"] is None or section["args_end"] is None:
            # Test sections without an args array are valid (e.g., startup tests
            # that rely on defaults). Skip silently.
            continue

        expected_args = STARTUP_TEST_ARGS if section["is_startup"] else STANDARD_TEST_ARGS

        ext_specific_start = section["extension_specific_start"]
        std_end = (ext_specific_start - 1) if ext_specific_start is not None else section["args_end"]
        existing_args = _parse_existing_args(lines, section["args_start"], std_end)

        if existing_args != expected_args:
            section_type = "startup" if section["is_startup"] else "regular"
            errors.append(f"line {section['start_line'] + 1}: {section_type} [[test]] args do not match standard")

            if fix:
                formatted = _format_args_section(expected_args)
                formatted_text = [line + "\n" for line in formatted[:-1]]

                if ext_specific_start is not None:
                    ext_lines = lines[ext_specific_start : section["args_end"] + 1]
                    result_lines[section["args_start"] : section["args_end"] + 1] = formatted_text + ext_lines
                else:
                    formatted_text.append(formatted[-1] + "\n")
                    result_lines[section["args_start"] : section["args_end"] + 1] = formatted_text

    return errors, result_lines


def _build_exclude_block(missing: list[str], lead_blank: bool, trail_blank: bool) -> list[str]:
    """Build the lines for a new ``stdoutFailPatterns.exclude`` block.

    Args:
        missing: Pattern strings to include in the block.
        lead_blank: Whether to prepend a blank separator line.
        trail_blank: Whether to append a blank separator line.

    Returns:
        List of lines (with newlines) for the new block.
    """
    block: list[str] = []
    if lead_blank:
        block.append("\n")
    block.append("stdoutFailPatterns.exclude = [\n")
    for pat in missing:
        block.append(f"    '{pat}',\n")
    block.append("]\n")
    if trail_blank:
        block.append("\n")
    return block


def _section_missing(section: dict, test_table: dict | None, lines: list[str]) -> list[str]:
    """Compute required exclude patterns missing from a section.

    Uses the parsed unscoped ``stdoutFailPatterns.exclude`` list when available;
    otherwise falls back to a substring scan of the section's text.

    Args:
        section: Discovered section info.
        test_table: Corresponding parsed ``[[test]]`` table, or None.
        lines: All file lines.

    Returns:
        Required patterns missing from the section.
    """
    if test_table is not None:
        present = _unscoped_excludes(test_table)
        return [p for p in REQUIRED_STDOUT_FAIL_EXCLUDE if p not in present]
    section_text = "".join(lines[section["start_line"] : section["end_line"]])
    return [p for p in REQUIRED_STDOUT_FAIL_EXCLUDE if p not in section_text]


def _validate_fix_stdout_excludes(
    lines: list[str],
    fix: bool,
    test_tables: list[dict] | None = None,
) -> tuple[list[str], list[str]]:
    """Ensure every ``[[test]]`` section contains the required exclude patterns.

    For sections that already declare an unscoped ``stdoutFailPatterns.exclude``
    array, only the *missing* pattern(s) are inserted at the top of that array.
    For sections without one, a new block is inserted respecting field order
    (after ``args``/``dependencies`` and before any ``stdoutFailPatterns.include``).

    Args:
        lines: Current file lines (with newlines).
        fix: Whether to apply fixes.
        test_tables: Parsed ``[[test]]`` tables in file order, used for precise
            presence detection. When None or mismatched, a substring scan is used.

    Returns:
        Tuple of (errors, possibly-modified lines).
    """
    errors: list[str] = []
    sections = _discover_test_sections(lines)
    result_lines = lines.copy()

    # Map each section (in file order) to its parsed table when counts agree.
    sections_asc = sorted(sections, key=lambda s: s["start_line"])
    use_parsed = test_tables is not None and len(test_tables) == len(sections_asc)
    missing_by_start: dict[int, list[str]] = {}
    for idx, sec in enumerate(sections_asc):
        table = test_tables[idx] if use_parsed else None
        missing_by_start[sec["start_line"]] = _section_missing(sec, table, lines)

    # Process bottom-up so earlier line indices remain valid after insertions.
    for section in sorted(sections, key=lambda s: s["start_line"], reverse=True):
        missing = missing_by_start[section["start_line"]]
        if not missing:
            continue

        patterns = ", ".join(f"'{p}'" for p in missing)
        noun = "entry" if len(missing) == 1 else "entries"
        errors.append(
            f"line {section['start_line'] + 1}: [[test]] missing required stdoutFailPatterns.exclude {noun}: {patterns}"
        )

        if not fix:
            continue

        if section["exclude_start"] is not None:
            _fix_existing_exclude(result_lines, section, missing)
        elif section["include_start"] is not None:
            # Must appear before stdoutFailPatterns.include to satisfy field order.
            inc = section["include_start"]
            lead = inc > 0 and result_lines[inc - 1].strip() != ""
            block = _build_exclude_block(missing, lead_blank=lead, trail_blank=True)
            result_lines[inc:inc] = block
        else:
            # Append after the last real field line (skip trailing blanks/comments)
            # so the block lands at top level of the section, not inside an array.
            anchor = section["start_line"]
            for i in range(section["start_line"], section["end_line"]):
                stripped = result_lines[i].strip()
                if stripped and not stripped.startswith("#"):
                    anchor = i
            insert_at = anchor + 1
            # A trailing blank is needed only when the next line is a header/comment
            # (i.e. there is no existing blank separating us from what follows).
            need_trail = insert_at < len(result_lines) and result_lines[insert_at].strip() != ""
            block = _build_exclude_block(missing, lead_blank=True, trail_blank=need_trail)
            result_lines[insert_at:insert_at] = block

    # Normalize spacing of unscoped exclude blocks (runs after insertions so it
    # also tidies blocks we just modified).
    spacing_errors, result_lines = _normalize_exclude_spacing(result_lines, fix)
    errors.extend(spacing_errors)

    return errors, result_lines


def _normalize_exclude_spacing(lines: list[str], fix: bool) -> tuple[list[str], list[str]]:
    """Standardize whitespace around each unscoped ``stdoutFailPatterns.exclude`` block.

    Enforces exactly one blank line before the block (separating it from the
    preceding field) and no blank lines inside the array.

    Args:
        lines: Current file lines (with newlines).
        fix: Whether to apply fixes.

    Returns:
        Tuple of (errors, possibly-modified lines).
    """
    errors: list[str] = []
    result_lines = lines.copy()
    sections = _discover_test_sections(result_lines)

    # Bottom-up so edits do not invalidate earlier sections' indices.
    for section in sorted(sections, key=lambda s: s["start_line"], reverse=True):
        es = section["exclude_start"]
        ee = section["exclude_end"]
        if es is None or ee is None or ee == es:
            continue  # no block, or inline (handled during insertion)

        internal_blanks = [i for i in range(es + 1, ee) if result_lines[i].strip() == ""]

        # Find the insertion point for a leading blank, skipping a comment block
        # that documents the exclude array so the blank goes above it.
        ins = es
        while ins - 1 >= 0 and result_lines[ins - 1].lstrip().startswith("#"):
            ins -= 1
        prev = result_lines[ins - 1].strip() if ins - 1 >= 0 else ""
        missing_lead = prev != "" and prev != "[[test]]"

        if internal_blanks or missing_lead:
            issue = []
            if missing_lead:
                issue.append("missing blank line before block")
            if internal_blanks:
                issue.append("blank line(s) inside array")
            errors.append(f"line {es + 1}: stdoutFailPatterns.exclude has non-standard spacing ({', '.join(issue)})")
            if fix:
                for i in sorted(internal_blanks, reverse=True):
                    del result_lines[i]
                if missing_lead:
                    result_lines.insert(ins, "\n")

    return errors, result_lines


def _fix_existing_exclude(result_lines: list[str], section: dict, missing: list[str]) -> None:
    """Insert missing patterns into a section's existing unscoped exclude array.

    Handles both multi-line arrays (entries reindented to the standard indent,
    a separating marker added before pre-existing test-suite entries) and inline
    arrays (expanded to multi-line first to keep the result valid TOML). Mutates
    ``result_lines`` in place.

    Args:
        result_lines: File lines being edited.
        section: Discovered section info.
        missing: Required patterns to insert (already known to be absent).
    """
    open_idx = section["exclude_start"]
    close_idx = section["exclude_end"]
    inline = close_idx is None or close_idx == open_idx

    if inline:
        # Expand `key = [ ... ]` (or `[]`) into a multi-line block so we never
        # append entries after a closed array.
        head, existing = _split_inline_array(result_lines[open_idx])
        rebuilt = [f"{head}\n"]
        rebuilt += [f"{_EXCLUDE_INDENT}'{p}',\n" for p in missing]
        if existing:
            rebuilt.append(f"{_EXCLUDE_INDENT}{TEST_SUITE_SPECIFIC_MARKER}\n")
            rebuilt += [f"{_EXCLUDE_INDENT}{tok},\n" for tok in existing]
        rebuilt.append("]\n")
        result_lines[open_idx : open_idx + 1] = rebuilt
        return

    # Multi-line array: normalize entry indentation and detect an existing marker.
    has_marker = False
    for i in range(open_idx + 1, close_idx):
        stripped = result_lines[i].strip()
        if not stripped:
            continue
        if stripped == TEST_SUITE_SPECIFIC_MARKER:
            has_marker = True
        result_lines[i] = f"{_EXCLUDE_INDENT}{stripped}\n"

    existing_entries = any(result_lines[i].strip() for i in range(open_idx + 1, close_idx))
    new_entries = [f"{_EXCLUDE_INDENT}'{p}',\n" for p in missing]
    if existing_entries and not has_marker:
        new_entries.append(f"{_EXCLUDE_INDENT}{TEST_SUITE_SPECIFIC_MARKER}\n")
    result_lines[open_idx + 1 : open_idx + 1] = new_entries


def validate_extension_toml(
    file_path: str | Path,
    fix: bool = False,
    verbose: bool = False,
    checks: tuple[str, ...] | None = None,
) -> list[str]:
    """Validate (and optionally fix) test sections in a single extension.toml.

    Two independent checks are available (see :data:`ALL_CHECKS`):

    - ``"args"``: every non-startup/non-doctest ``[[test]]`` section must use
      ``STANDARD_TEST_ARGS`` (startup uses ``STARTUP_TEST_ARGS``).
    - ``"stdout"``: every ``[[test]]`` section must contain the
      :data:`REQUIRED_STDOUT_FAIL_EXCLUDE` ``stdoutFailPatterns.exclude`` entries.

    Args:
        file_path: Path to the extension.toml file.
        fix: If True, rewrite the file to satisfy the selected checks.
        verbose: Print detailed progress.
        checks: Which checks to run; defaults to all of :data:`ALL_CHECKS`.

    Returns:
        List of human-readable error strings (empty if conforming).
    """
    file_path = str(file_path)
    selected = tuple(checks) if checks else ALL_CHECKS
    errors: list[str] = []

    try:
        lines = _read_lines(file_path)
    except OSError as e:
        return [f"Cannot read {file_path}: {e}"]

    # Ensure the final line is newline-terminated so appends form real blank
    # lines instead of merging into an un-terminated last line.
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    # Validate syntax up front; refuse to edit a file we cannot parse.
    parsed, parse_err = _toml_parse("".join(lines))
    if parse_err is not None:
        return [f"invalid TOML, cannot validate/fix: {parse_err}"]

    if not _discover_test_sections(lines):
        return []  # no [[test]] sections at all — nothing to validate

    test_tables = parsed.get("test") if isinstance(parsed, dict) else None
    if not isinstance(test_tables, list):
        test_tables = None

    changed = False

    if "args" in selected:
        args_errors, lines = _validate_fix_args(lines, fix)
        errors.extend(args_errors)
        changed = changed or (fix and bool(args_errors))

    if "stdout" in selected:
        stdout_errors, lines = _validate_fix_stdout_excludes(lines, fix, test_tables)
        errors.extend(stdout_errors)
        changed = changed or (fix and bool(stdout_errors))

    if fix and changed:
        # Defense-in-depth: never write a file our edits would make unparseable.
        _, post_err = _toml_parse("".join(lines))
        if post_err is not None:
            return errors + [f"fix aborted: edit would produce invalid TOML ({post_err}); file left unchanged"]
        _write_lines(file_path, lines)
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
        repo_root / "source" / "deprecated",
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
    parser.add_argument("--fix", action="store_true", help="Auto-fix non-conforming sections in place.")
    parser.add_argument(
        "--check",
        choices=("all", *ALL_CHECKS),
        default="all",
        help="Which validation(s) to run: 'args' (standard test args), "
        "'stdout' (required stdoutFailPatterns.exclude entries), or 'all' (default).",
    )
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
    checks = ALL_CHECKS if args.check == "all" else (args.check,)

    if args.file:
        if not args.file.exists():
            print(f"Error: {args.file} not found.")
            return 1
        all_errors = validate_extension_toml(args.file, fix=args.fix, verbose=args.verbose, checks=checks)
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
        errors = validate_extension_toml(toml_path, fix=args.fix, verbose=args.verbose, checks=checks)
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

    label = {"all": "test sections", "args": "test args", "stdout": "stdout fail patterns"}[args.check]
    print(f"All {len(toml_files)} extension.toml files have conforming {label}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
