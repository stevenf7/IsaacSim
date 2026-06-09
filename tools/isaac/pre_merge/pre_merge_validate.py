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

"""Pre-merge validation orchestrator for Isaac Sim repository.

Determines modified files and affected extensions, then delegates each check
to a standalone script:

  1. Python linting (ruff)          -> run_python_linting.py
  2. Code formatting verification   -> repo.sh format --verify
  3. Changelog and version bump     -> validate_changelog.py
  4. extension.toml validation      -> validate_extension_toml.py
  5. Test args validation            -> validate_test_args.py
  6. Settings docs validation       -> validate_settings.py
  7. Extension structure validation  -> validate_extension_structure.py
  8. License header validation       -> validate_license_headers.py
  9. Python package definitions      -> repo.sh validate_python_packages
 10. C++ linting (clang-tidy)        -> clang_tidy.py  (--clang-tidy flag, requires build)
 11. Extension test discovery & run  -> run_extension_tests.py
 12. API docs check (checkapi)       -> run_checkapi.py (--checkapi flag, requires build)

Determines the full set of changed files by comparing against the merge-base
of the current branch with its upstream (auto-detected, or set via --base-branch).
Uncommitted working-tree changes are always included on top.
When source/apps/ files are modified, isaacsim.app.setup tests are also included.

Usage:
    # Run all validation checks (no tests)
    python tools/isaac/pre_merge/pre_merge_validate.py

    # Run specific checks
    python tools/isaac/pre_merge/pre_merge_validate.py --lint --format

    # Run validation + extension tests
    python tools/isaac/pre_merge/pre_merge_validate.py --test

    # Run only tests for modified extensions
    python tools/isaac/pre_merge/pre_merge_validate.py --test-only

    # Run checks on a single extension
    python tools/isaac/pre_merge/pre_merge_validate.py -e isaacsim.ros2.core

    # Run checks on multiple extensions
    python tools/isaac/pre_merge/pre_merge_validate.py --extensions isaacsim.ros2.core isaacsim.ros2.nodes

    # Run tests for specific extensions
    python tools/isaac/pre_merge/pre_merge_validate.py --test -e isaacsim.ros2.core

    # Auto-fix what can be fixed (ruff, extension.toml, settings docs)
    python tools/isaac/pre_merge/pre_merge_validate.py --fix

    # Fast format check for pre-commit hooks (uncommitted files only)
    python tools/isaac/pre_merge/pre_merge_validate.py --modified

    # Re-run only the extensions that failed in a previous test run
    python tools/isaac/pre_merge/pre_merge_validate.py --retest isaacsim.robot.poser isaacsim.robot.schema

    # Save all output to a log file (ANSI-stripped)
    python tools/isaac/pre_merge/pre_merge_validate.py --log validation.log

    # Compare changelog/version against a specific base branch
    python tools/isaac/pre_merge/pre_merge_validate.py --base-branch main

    # Lint the full standalone_examples tree
    python tools/isaac/pre_merge/pre_merge_validate.py --standalone

    # All extensions plus the full standalone_examples tree
    python tools/isaac/pre_merge/pre_merge_validate.py --all
"""

from __future__ import annotations

import argparse
import contextlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

# Ensure this script's directory is on sys.path so repo_helpers and term_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import (  # noqa: E402
    _IS_WINDOWS,
    EXTENSION_ROOTS,
    REPO_ROOT,
    STANDALONE_EXAMPLES_DIR,
    TOOLS_DIR,
    affected_extensions,
    all_extensions,
    get_all_modified_files,
    has_apps_changes,
    resolve_extensions_by_name,
    standalone_examples_files,
)
from term_helpers import (  # noqa: E402
    Colors,
    colorize,
    header,
    log_fail,
    log_info,
    log_pass,
    log_warn,
)

# ---------------------------------------------------------------------------
# Output tee — duplicate stdout to a log file when --log is active
# ---------------------------------------------------------------------------

_log_fh: TextIO | None = None
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class _TeeStream:
    """Wrap a stream to duplicate writes to a log file with ANSI stripping.

    Args:
        stream: The stream to wrap.
        log_file: The log file to duplicate writes to (ANSI codes stripped).
    """

    def __init__(self, stream: TextIO, log_file: TextIO) -> None:
        self._stream = stream
        self._log_file = log_file

    def write(self, text: str) -> int:
        self._stream.write(text)
        self._log_file.write(_ANSI_RE.sub("", text))
        return len(text)

    def flush(self) -> None:
        self._stream.flush()
        self._log_file.flush()

    def isatty(self) -> bool:
        return self._stream.isatty()

    @property
    def encoding(self) -> str:
        return self._stream.encoding


def _run_teed(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Run a command, teeing its stdout to the log file when active.

    When ``_log_fh`` is ``None`` this is equivalent to ``subprocess.run()``.
    When logging is active the subprocess stdout is captured via a pipe and
    relayed line-by-line through ``sys.stdout`` (which is a ``_TeeStream``).

    Args:
        cmd: Command and arguments to run.
        **kwargs: Additional arguments passed to subprocess.run.

    Returns:
        Completed process result.
    """
    if _log_fh is None:
        return subprocess.run(cmd, **kwargs)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        **kwargs,
    )
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.stdout.close()
    proc.wait()
    return subprocess.CompletedProcess(cmd, proc.returncode)


# ---------------------------------------------------------------------------
# Check 1: Python linting — delegates to run_python_linting.py
# ---------------------------------------------------------------------------


def check_python_lint(extensions: list[Path], fix: bool = False) -> int:
    """Run ruff via ``run_python_linting.py`` on affected extensions.

    Args:
        extensions: List of extension paths to lint.
        fix: Whether to auto-fix issues.

    Returns:
        Exit code (0 if clean, 1 if issues).
    """
    if not extensions:
        log_info("No modified extensions to lint.")
        return 0

    script = TOOLS_DIR / "run_python_linting.py"
    if not script.exists():
        log_warn("run_python_linting.py not found; skipping lint check.")
        return 0

    ext_names = [ext.name for ext in extensions]
    cmd = [sys.executable, str(script), "--ruff", "--extensions"] + ext_names
    if fix:
        cmd.append("--fix")

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        log_fail("Python linting reported issues.")
        return 1

    log_pass("Python linting clean.")
    return 0


def check_python_lint_paths(paths: list[Path], label: str, fix: bool = False) -> int:
    """Run ruff via ``run_python_linting.py --path`` on arbitrary directories/files.

    Used for source trees (such as ``source/standalone_examples``) that are not
    registered extensions but still contain Python that should be linted.

    Args:
        paths: Directories and/or files to lint.
        label: Human-readable name for this section (used in status messages).
        fix: Whether to auto-fix issues.

    Returns:
        Exit code (0 if clean, 1 if issues).
    """
    existing = [p for p in paths if p.exists()]
    if not existing:
        log_info(f"No {label} files to lint.")
        return 0

    script = TOOLS_DIR / "run_python_linting.py"
    if not script.exists():
        log_warn("run_python_linting.py not found; skipping lint check.")
        return 0

    cmd = [sys.executable, str(script), "--ruff", "--path"] + [str(p) for p in existing]
    if fix:
        cmd.append("--fix")

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        log_fail(f"Python linting reported issues in {label}.")
        return 1

    log_pass(f"Python linting clean ({label}).")
    return 0


# ---------------------------------------------------------------------------
# Check 2: Code formatting (repo.sh format --verify)
# ---------------------------------------------------------------------------


def start_format_check(
    modified_only: bool = False,
    files: list[Path] | None = None,
    fix: bool = False,
) -> subprocess.Popen | None:
    """Launch ``repo.sh format`` in the background.

    When *fix* is ``False`` (default), ``--verify`` is passed so the command
    only reports issues.  When *fix* is ``True``, ``--verify`` is omitted and
    ``--force`` is added so the formatter rewrites files in place.

    When *modified_only* is ``True``, passes ``-m`` so only uncommitted files
    are checked.  Otherwise, if *files* is provided, each path is made
    relative to the repo root and passed as a positional ``select_files``
    argument so the formatter only inspects the listed files.

    Args:
        modified_only: If True, only check uncommitted files.
        files: Optional list of files to check; ignored if modified_only is True.
        fix: Whether to auto-fix formatting issues.

    Returns:
        Popen handle for the format process, or None if repo.sh is not found.
    """
    if _IS_WINDOWS:
        repo_script = REPO_ROOT / "repo.bat"
        if not repo_script.exists():
            return None
        cmd = ["cmd.exe", "/c", str(repo_script), "format"]
    else:
        repo_script = REPO_ROOT / "repo.sh"
        if not repo_script.exists():
            return None
        cmd = ["bash", str(repo_script), "format"]
    if fix:
        cmd.append("--force")
    else:
        cmd.append("--verify")
    if modified_only:
        cmd.append("-m")
    elif files:
        for f in files:
            try:
                cmd.append(str(f.relative_to(REPO_ROOT)))
            except ValueError:
                cmd.append(str(f))
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=REPO_ROOT,
    )


def collect_format_result(proc: subprocess.Popen | None, fix: bool = False) -> int:
    """Wait for the background format check and report the result.

    Args:
        proc: Format check process handle from start_format_check.
        fix: Whether fix was attempted (affects error message).

    Returns:
        Exit code (0 if OK, 1 if issues).
    """
    if proc is None:
        log_warn("repo script not found; skipping format check.")
        return 0

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        output_lines = (stdout or "").strip().splitlines() + (stderr or "").strip().splitlines()
        for line in output_lines[-20:]:
            print(f"    {line}", flush=True)
        if fix:
            log_fail("Code formatting auto-fix failed.")
        else:
            log_fail("Code formatting issues detected. Run: ./repo.sh format (or repo.bat format on Windows)")
        return 1

    if fix:
        log_pass("Code formatting auto-fixed.")
    else:
        log_pass("Code formatting OK.")
    return 0


# ---------------------------------------------------------------------------
# Check 3: Changelog & version bump — delegates to validate_changelog.py
# ---------------------------------------------------------------------------


def check_changelog(extensions: list[Path], base_branch: str | None, fix: bool = False) -> int:
    """Validate changelog and version bump via ``validate_changelog.py``.

    Args:
        extensions: List of extension paths to check.
        base_branch: Base branch to diff against for version comparison.
        fix: Whether to auto-fix issues.

    Returns:
        Exit code (0 if OK, 1 if issues).
    """
    if not extensions:
        log_info("No modified extensions to check for changelog/version.")
        return 0

    script = TOOLS_DIR / "validate_changelog.py"
    if not script.exists():
        log_warn("validate_changelog.py not found; skipping.")
        return 0

    cmd = [sys.executable, str(script)] + [str(ext) for ext in extensions]
    if base_branch:
        cmd.extend(["--base-branch", base_branch])
    if fix:
        cmd.append("--fix")

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    return 1 if proc.returncode != 0 else 0


# ---------------------------------------------------------------------------
# Check 4: extension.toml validation — delegates to validate_extension_toml.py
# ---------------------------------------------------------------------------


def check_extension_toml(extensions: list[Path], fix: bool = False) -> int:
    """Validate extension.toml for each modified extension.

    Args:
        extensions: List of extension paths to validate.
        fix: Whether to auto-fix issues.

    Returns:
        Number of extensions with validation errors.
    """
    if not extensions:
        log_info("No modified extensions to validate extension.toml.")
        return 0

    script = TOOLS_DIR / "validate_extension_toml.py"
    if not script.exists():
        log_warn("validate_extension_toml.py not found; skipping.")
        return 0

    errors = 0
    for ext in extensions:
        toml_file = ext / "config" / "extension.toml"
        if not toml_file.exists():
            log_fail(f"{ext.name}: missing config/extension.toml")
            errors += 1
            continue

        cmd = [sys.executable, str(script), "--file", str(toml_file)]
        if fix:
            cmd.append("--fix")

        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            output = (proc.stdout or "").strip()
            if output:
                for line in output.splitlines()[-10:]:
                    print(f"    {line}", flush=True)
            log_fail(f"{ext.name}: extension.toml validation failed.")
            errors += 1
        else:
            log_pass(f"{ext.name}: extension.toml OK.")

    return errors


# ---------------------------------------------------------------------------
# Check 5: Test args validation — delegates to validate_test_args.py
# ---------------------------------------------------------------------------


def check_test_args(extensions: list[Path], fix: bool = False) -> int:
    """Validate test args in extension.toml for each modified extension.

    Args:
        extensions: List of extension paths to validate.
        fix: Whether to auto-fix non-conforming args.

    Returns:
        Number of extensions with validation errors.
    """
    if not extensions:
        log_info("No modified extensions to validate test args.")
        return 0

    from validate_test_args import validate_extension_toml as validate_test_args_toml

    errors = 0
    for ext in extensions:
        toml_file = ext / "config" / "extension.toml"
        if not toml_file.exists():
            continue  # Already reported by check_extension_toml

        issues = validate_test_args_toml(toml_file, fix=fix)
        if issues:
            for issue in issues:
                print(f"    {issue}", flush=True)
            if fix:
                log_pass(f"{ext.name}: test args fixed.")
            else:
                log_fail(f"{ext.name}: test args do not match standard.")
                errors += 1
        else:
            log_pass(f"{ext.name}: test args OK.")

    return errors


# ---------------------------------------------------------------------------
# Check 6: Settings docs validation — delegates to validate_settings.py
# ---------------------------------------------------------------------------


def check_settings(extensions: list[Path], fix: bool = False) -> int:
    """Validate settings docs for each modified extension.

    Args:
        extensions: List of extension paths to validate.
        fix: Whether to auto-fix `docs/SETTINGS.md`.

    Returns:
        Number of extensions with validation errors.
    """
    if not extensions:
        log_info("No modified extensions to validate settings docs.")
        return 0

    script = TOOLS_DIR / "validate_settings.py"
    if not script.exists():
        log_warn("validate_settings.py not found; skipping.")
        return 0

    errors = 0
    for ext in extensions:
        cmd = [sys.executable, str(script), str(ext)]
        if fix:
            cmd.append("--fix")

        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            output_lines = (proc.stdout or "").strip().splitlines()
            if proc.stderr:
                output_lines.extend((proc.stderr or "").strip().splitlines())
            for line in output_lines[-10:]:
                print(f"    {line}", flush=True)
            log_fail(f"{ext.name}: settings docs validation failed.")
            errors += 1
        else:
            log_pass(f"{ext.name}: settings docs OK.")

    return errors


# ---------------------------------------------------------------------------
# Check 6: Extension structure — delegates to validate_extension_structure.py
# ---------------------------------------------------------------------------


def _normalize_structure_output(output: str, ext_root: str) -> set[str]:
    """Replace the extension root path with a placeholder for diffing.

    Args:
        output: Raw validation output.
        ext_root: Extension root path to replace with placeholder.

    Returns:
        Set of normalized error lines.
    """
    normalized: set[str] = set()
    for line in output.splitlines():
        stripped = line.strip()
        if stripped:
            normalized.add(stripped.replace(ext_root, "<ext>"))
    return normalized


def _get_base_structure_errors(ext_path: Path, base_ref: str, script: Path) -> set[str]:
    """Run structure validation on the base-branch version of an extension.

    Args:
        ext_path: Path to the extension.
        base_ref: Base branch ref (e.g. origin/main).
        script: Path to validate_extension_structure.py.

    Returns:
        Set of normalized error strings from base version.
    """
    import shutil
    import tempfile

    rel = ext_path.relative_to(REPO_ROOT)
    merge_base_proc = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if merge_base_proc.returncode != 0:
        return set()
    merge_base = merge_base_proc.stdout.strip()

    tmpdir = None
    try:
        tmpdir = Path(tempfile.mkdtemp(prefix="pre_commit_struct_"))
        proc = subprocess.run(
            ["git", "archive", merge_base, "--", rel.as_posix()],
            capture_output=True,
            cwd=REPO_ROOT,
        )
        if proc.returncode != 0 or not proc.stdout:
            return set()
        subprocess.run(
            ["tar", "xf", "-"],
            input=proc.stdout,
            cwd=tmpdir,
            capture_output=True,
        )
        base_ext = tmpdir / rel
        if not base_ext.exists():
            return set()

        result = subprocess.run(
            [sys.executable, str(script), str(base_ext)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if result.returncode == 0:
            return set()
        return _normalize_structure_output(result.stdout or "", str(base_ext))
    except Exception:
        return set()
    finally:
        if tmpdir and tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)


def check_extension_structure(extensions: list[Path], base_ref: str | None = None) -> int:
    """Validate extension directory structure, reporting only new failures.

    Args:
        extensions: List of extension paths to validate.
        base_ref: Base branch ref for diffing; if None, all failures are reported.

    Returns:
        Number of extensions with new structure errors.
    """
    if not extensions:
        log_info("No modified extensions to check structure.")
        return 0

    script = TOOLS_DIR / "validate_extension_structure.py"
    if not script.exists():
        log_warn("validate_extension_structure.py not found; skipping.")
        return 0

    errors = 0
    for ext in extensions:
        cmd = [sys.executable, str(script), str(ext)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            current_normalized = _normalize_structure_output(proc.stdout or "", str(ext))

            if base_ref:
                base_normalized = _get_base_structure_errors(ext, base_ref, script)
                new_issues = current_normalized - base_normalized
            else:
                new_issues = current_normalized

            if new_issues:
                for line in sorted(new_issues):
                    print(f"    {line.replace('<ext>', str(ext))}", flush=True)
                log_fail(f"{ext.name}: extension structure validation failed (new issues).")
                errors += 1
            else:
                log_pass(f"{ext.name}: extension structure OK (pre-existing issues only).")
        else:
            log_pass(f"{ext.name}: extension structure OK.")

    return errors


# ---------------------------------------------------------------------------
# Check 7: License headers — delegates to validate_license_headers.py
# ---------------------------------------------------------------------------


def validate_license_headers(modified_files: list[Path], fix: bool = False, all_files: bool = False) -> int:
    """Validate SPDX headers on changed source files.

    Args:
        modified_files: Full list of changed files discovered by pre-merge logic.
        fix: Whether to auto-fix issues when possible.
        all_files: If True, validate all supported files under the repo root.

    Returns:
        Exit code (0 if OK, 1 if issues).
    """
    script = TOOLS_DIR / "validate_license_headers.py"
    if not script.exists():
        log_warn("validate_license_headers.py not found; skipping license header check.")
        return 0

    if all_files:
        failures = 0
        for root in EXTENSION_ROOTS:
            if not root.exists():
                continue
            log_info(f"Checking license headers under {root.relative_to(REPO_ROOT)}")
            cmd = [sys.executable, str(script), "--root", str(root)]
            if fix:
                cmd.append("--fix")
            proc = _run_teed(cmd, cwd=REPO_ROOT)
            if proc.returncode != 0:
                failures += 1
        if failures > 0:
            log_fail("License header validation reported issues.")
            return 1
        log_pass("License header validation clean.")
        return 0

    cmd = [sys.executable, str(script), "--root", str(REPO_ROOT)]
    if not all_files:
        supported_exts = {
            ".py",
            ".cpp",
            ".cc",
            ".cxx",
            ".c",
            ".h",
            ".hpp",
            ".hxx",
            ".cu",
            ".cuh",
            ".yaml",
            ".yml",
            ".ipynb",
            ".lua",
            ".sh",
            ".bat",
        }
        existing_files = [f for f in modified_files if f.exists() and f.suffix.lower() in supported_exts]
        if not existing_files:
            log_info("No modified source files requiring license checks.")
            return 0
        cmd.extend(["--files", *[str(f) for f in existing_files]])

    if fix:
        cmd.append("--fix")

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        log_fail("License header validation reported issues.")
        return 1

    log_pass("License header validation clean.")
    return 0


# ---------------------------------------------------------------------------
# Check 8: Python package definitions — delegates to repo.sh validate_python_packages
# ---------------------------------------------------------------------------


def check_python_packages() -> int:
    """Validate Python package definitions via ``repo.sh validate_python_packages``.

    Returns:
        Exit code (0 if OK, 1 if issues).
    """
    if _IS_WINDOWS:
        repo_script = REPO_ROOT / "repo.bat"
        if not repo_script.exists():
            log_warn("repo.bat not found; skipping python packages check.")
            return 0
        cmd = ["cmd.exe", "/c", str(repo_script), "validate_python_packages"]
    else:
        repo_script = REPO_ROOT / "repo.sh"
        if not repo_script.exists():
            log_warn("repo.sh not found; skipping python packages check.")
            return 0
        cmd = ["bash", str(repo_script), "validate_python_packages"]

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        log_fail("Python package definitions check failed.")
        return 1
    log_pass("Python package definitions OK.")
    return 0


# ---------------------------------------------------------------------------
# Check 9: C++ linting (clang-tidy) — delegates to clang_tidy.py
# ---------------------------------------------------------------------------


def check_clang_tidy(extensions: list[Path], fix: bool = False) -> int:
    """Run clang-tidy on C++ files in the given extensions.

    Args:
        extensions: List of extension paths to analyze.
        fix: Whether to apply auto-fixes.

    Returns:
        Number of extensions with clang-tidy issues.
    """
    if not extensions:
        log_info("No modified extensions to check with clang-tidy.")
        return 0

    from run_clang_tidy import check_extensions

    errors = check_extensions(extensions, REPO_ROOT, fix=fix)
    if errors > 0:
        log_fail(f"clang-tidy reported issues in {errors} extension(s).")
    else:
        log_pass("clang-tidy clean.")
    return errors


# ---------------------------------------------------------------------------
# Check 10: API docs check (checkapi) — delegates to run_checkapi.py
# ---------------------------------------------------------------------------


def check_checkapi(extensions: list[Path], fix: bool = False) -> int:
    """Run checkapi on modified extensions to verify python_api.md is up-to-date.

    Args:
        extensions: List of extension paths to check.
        fix: Whether to auto-update python_api.md files.

    Returns:
        Exit code (0 if OK, 1 if issues).
    """
    if not extensions:
        log_info("No modified extensions to check API docs.")
        return 0

    script = TOOLS_DIR / "run_checkapi.py"
    if not script.exists():
        log_warn("run_checkapi.py not found; skipping checkapi.")
        return 0

    ext_names = [ext.name for ext in extensions]
    cmd = [sys.executable, str(script), "--check"] + ext_names
    if not fix:
        # In non-fix mode we still generate to detect drift, but report it
        pass

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        log_fail("API docs check (checkapi) reported issues.")
        return 1

    log_pass("API docs check (checkapi) clean.")
    return 0


# ---------------------------------------------------------------------------
# Check 11: Extension tests — delegates to run_extension_tests.py
# ---------------------------------------------------------------------------


def check_tests(
    extensions: list[Path],
    modified_files: list[Path],
    test_filter: str | None = None,
    timeout: int = 600,
    include_downstream: bool = True,
    only_extensions: list[str] | None = None,
) -> int:
    """Discover and run extension tests via ``run_extension_tests.py``.

    Args:
        extensions: List of extension paths to test.
        modified_files: List of modified files (used for apps-changed detection).
        test_filter: Optional filter expression for test selection.
        timeout: Per-extension test timeout in seconds.
        include_downstream: Whether to include downstream dependent extensions.
        only_extensions: If set, run tests only for these extension names.

    Returns:
        Exit code (0 if all pass, 1 if any fail).
    """
    script = TOOLS_DIR / "run_extension_tests.py"
    if not script.exists():
        log_warn("run_extension_tests.py not found; skipping tests.")
        return 0

    if not extensions:
        log_info("No extensions to test.")
        return 0

    cmd = [sys.executable, str(script)] + [str(ext) for ext in extensions]
    if test_filter:
        cmd.extend(["--filter", test_filter])
    cmd.extend(["--timeout", str(timeout)])
    if not include_downstream:
        cmd.append("--no-downstream")
    if only_extensions:
        cmd.extend(["--only"] + only_extensions)
    if has_apps_changes(modified_files):
        cmd.append("--apps-changed")

    proc = _run_teed(cmd, cwd=REPO_ROOT)
    return 1 if proc.returncode != 0 else 0


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for pre-merge validation.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Pre-commit validation for Isaac Sim: lint, format, changelog, toml, settings docs, structure, license, and clang-tidy checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    checks = parser.add_argument_group("check selection (default: all validation, no tests)")
    checks.add_argument("--lint", action="store_true", help="Run Python linting (ruff)")
    checks.add_argument("--format", action="store_true", help="Run code format verification")
    checks.add_argument("--changelog", action="store_true", help="Check changelog and version bump")
    checks.add_argument("--toml", action="store_true", help="Validate extension.toml files")
    checks.add_argument("--test-args", action="store_true", help="Validate test args in extension.toml")
    checks.add_argument("--settings", action="store_true", help="Validate settings docs against extension.toml")
    checks.add_argument("--structure", action="store_true", help="Validate extension directory structure")
    checks.add_argument("--license", action="store_true", help="Validate SPDX license headers on changed files")
    checks.add_argument("--packages", action="store_true", help="Validate Python package definitions")
    checks.add_argument(
        "--clang-tidy",
        action="store_true",
        help="Run clang-tidy on C++ files in modified extensions (requires a build).",
    )
    checks.add_argument(
        "--checkapi",
        action="store_true",
        help="Run checkapi to verify python_api.md is up-to-date for modified extensions (requires a build).",
    )
    checks.add_argument(
        "--test",
        action="store_true",
        help="Run extension tests for modified extensions (requires a build). "
        "Also runs isaacsim.app.setup tests when source/apps/ files changed.",
    )
    checks.add_argument(
        "--test-only",
        action="store_true",
        help="Run ONLY extension tests, skip all other validation checks.",
    )

    test_opts = parser.add_argument_group("test options")
    test_opts.add_argument(
        "--test-filter",
        default=None,
        help="Filter expression passed to test scripts via -f (supports wildcards).",
    )
    test_opts.add_argument(
        "--test-timeout",
        type=int,
        default=600,
        help="Per-extension test timeout in seconds (default: 600).",
    )
    test_opts.add_argument(
        "--retest",
        nargs="+",
        default=None,
        metavar="EXT",
        help="Re-run tests for only the listed extension names. "
        "Implies --test. Extensions are still auto-discovered from "
        "modified files, but execution is restricted to those named here "
        "(applied as a whitelist after discovery and downstream expansion).",
    )

    parser.add_argument(
        "--extensions",
        "-e",
        nargs="+",
        default=None,
        metavar="EXT",
        help="Run checks on the specified extension(s) instead of auto-detecting "
        "from modified files. Accepts one or more extension names "
        "(e.g. isaacsim.ros2.core isaacsim.ros2.nodes).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_extensions",
        help="Run checks on every extension in the repo, not just those with "
        "modified files. Ignores the branch diff for extension discovery. "
        "Also lints the full source/standalone_examples tree.",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Lint the full source/standalone_examples tree. Without this flag, "
        "only standalone_examples files present in the branch diff are linted "
        "unless --all is used.",
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Run format verification only on uncommitted files (repo.sh -m). "
        "Other checks still use the full branch diff.",
    )
    parser.add_argument(
        "--skip-format",
        action="store_true",
        help="Skip the code format check (useful when format is already verified).",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip extension tests even when --test is specified.",
    )
    parser.add_argument(
        "--no-downstream",
        action="store_true",
        help="Do not include downstream dependent extensions when running tests.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible (ruff, code formatting, extension.toml, settings docs)",
    )
    parser.add_argument(
        "--base-branch",
        default=None,
        help="Base branch to diff against (e.g. main, origin/main). "
        "Auto-detected from upstream tracking branch if not provided. "
        "All committed changes since the merge-base plus uncommitted "
        "working-tree changes are included.",
    )
    parser.add_argument(
        "--log",
        default=None,
        type=Path,
        dest="log_path",
        help="Save all output (ANSI-stripped) to the specified log file.",
    )
    parser.add_argument(
        "--keep-going",
        "-k",
        action="store_true",
        help="Run all checks even if earlier ones fail; exit 0 regardless.",
    )
    return parser


def main() -> int:
    """Parse arguments, set up logging if requested, and run the validation pipeline.

    Returns:
        Exit code (0 on success, 1 on failure; 0 always if --keep-going).
    """
    global _log_fh

    parser = build_parser()
    args = parser.parse_args()

    original_stdout = sys.stdout

    with contextlib.ExitStack() as stack:
        if args.log_path:
            _log_fh = stack.enter_context(open(args.log_path, "w"))  # noqa: SIM115
            sys.stdout = _TeeStream(original_stdout, _log_fh)

            def _restore() -> None:
                global _log_fh
                sys.stdout = original_stdout
                _log_fh = None

            stack.callback(_restore)

        return _run(args)


def _run(args: argparse.Namespace) -> int:
    """Execute the validation pipeline — called by :func:`main`.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 on success, 1 on failure; 0 always if --keep-going).
    """
    if args.test_only:
        args.test = True
    if args.retest:
        args.test = True

    check_flags = [
        args.lint,
        args.format,
        args.changelog,
        args.toml,
        args.test_args,
        args.settings,
        args.structure,
        args.license,
        args.packages,
        args.clang_tidy,
        args.checkapi,
        args.test,
    ]
    run_all_validation = not any(check_flags)

    if args.extensions:
        extensions = resolve_extensions_by_name(args.extensions)
        modified, resolved_base = get_all_modified_files(args.base_branch)
        log_info(f"Running on {len(extensions)} explicitly specified extension(s).")
    elif args.all_extensions:
        modified: list[Path] = []
        resolved_base = args.base_branch
        extensions = all_extensions()
        log_info(f"Running on all {len(extensions)} extensions.")
        log_info("Including full source/standalone_examples tree (--all).")
    else:
        modified, resolved_base = get_all_modified_files(args.base_branch)

        if resolved_base:
            log_info(f"Base branch: {resolved_base}")
        else:
            log_warn("Could not detect base branch; only uncommitted changes will be checked.")

        if not modified and not args.standalone:
            print(colorize("No modified files detected. Nothing to validate.", Colors.GREEN), flush=True)
            return 0

        extensions = affected_extensions(modified)
        if args.standalone:
            log_info("Including full source/standalone_examples tree (--standalone).")

    py_files = [f for f in modified if f.suffix == ".py" and f.exists()]

    print(
        colorize(
            f"Modified files: {len(modified)}  |  Python files: {len(py_files)}  |  Extensions: {len(extensions)}",
            Colors.BOLD,
        ),
        flush=True,
    )
    for ext in extensions:
        log_info(ext.name)

    total_errors = 0

    format_proc: subprocess.Popen | None = None
    run_format = not args.test_only and not args.skip_format and (run_all_validation or args.format)
    if run_format:
        format_proc = start_format_check(modified_only=args.modified, files=modified, fix=args.fix)
        if format_proc:
            log_info("Code format check started in background.")

    if not args.test_only:
        if run_all_validation or args.lint:
            header("Python Linting (ruff)")
            total_errors += check_python_lint(extensions, fix=args.fix)

            # standalone_examples is not a registered extension, so it is linted
            # separately as its own section. With --all or --standalone the whole
            # tree is checked. Otherwise, when running in auto-detect mode (no
            # --all, no --extensions), only standalone_examples files present in
            # the branch diff are linted.
            if args.all_extensions or args.standalone:
                se_targets: list[Path] = [STANDALONE_EXAMPLES_DIR]
            elif not args.extensions and not args.all_extensions:
                se_targets = standalone_examples_files(modified)
            else:
                se_targets = []

            if se_targets:
                header("Python Linting (standalone_examples)")
                total_errors += check_python_lint_paths(se_targets, "standalone_examples", fix=args.fix)

        if run_all_validation or args.changelog:
            header("Changelog & Version Bump")
            total_errors += check_changelog(extensions, resolved_base, fix=args.fix)

        if run_all_validation or args.toml:
            header("extension.toml Validation")
            total_errors += check_extension_toml(extensions, fix=args.fix)

        if run_all_validation or args.test_args:
            header("Test Args Validation")
            total_errors += check_test_args(extensions, fix=args.fix)

        if run_all_validation or args.settings:
            header("Settings Docs Validation")
            total_errors += check_settings(extensions, fix=args.fix)

        if run_all_validation or args.structure:
            header("Extension Structure")
            total_errors += check_extension_structure(extensions, base_ref=resolved_base)

        if run_all_validation or args.license:
            header("License Headers")
            total_errors += validate_license_headers(modified, fix=args.fix, all_files=args.all_extensions)

        if run_all_validation or args.packages:
            header("Python Package Definitions")
            total_errors += check_python_packages()

        if args.clang_tidy:
            header("C++ Linting (clang-tidy)")
            total_errors += check_clang_tidy(extensions, fix=args.fix)

        if args.checkapi:
            header("API Docs Check (checkapi)")
            total_errors += check_checkapi(extensions, fix=args.fix)

    if args.test and not args.skip_tests:
        header("Extension Tests")
        total_errors += check_tests(
            extensions,
            modified,
            test_filter=args.test_filter,
            timeout=args.test_timeout,
            include_downstream=not args.no_downstream,
            only_extensions=args.retest,
        )

    if run_format:
        header("Code Formatting")
        total_errors += collect_format_result(format_proc, fix=args.fix)

    print(f"\n{'=' * 72}", flush=True)
    if total_errors == 0:
        print(colorize("  All checks passed.", Colors.BOLD + Colors.GREEN), flush=True)
    else:
        print(colorize(f"  {total_errors} issue(s) found.", Colors.BOLD + Colors.RED), flush=True)
    print(f"{'=' * 72}\n", flush=True)

    if args.keep_going:
        return 0
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
