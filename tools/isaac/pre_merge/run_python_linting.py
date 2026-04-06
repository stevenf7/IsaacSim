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

"""Run Python linting tools on Isaac Sim extensions, one extension at a time.

This script runs multiple linting tools on each extension separately, providing
comprehensive code quality checks. Extensions are discovered under:
    - source/extensions
    - source/internal_extensions
    - source/deprecated

Tools:
    - mypy: Static type checking
    - darglint: Docstring argument/return validation
    - interrogate: Docstring coverage metrics
    - pydoclint: Docstring validation (enforces no types in docstrings)
    - ruff: Fast linter with code quality checks:
        - Default: docstring style (D, Google convention), type annotations (ANN),
          modern annotations and f-strings (UP), pycodestyle (E711/E712/E722),
          bugbear (B006), naming (N), comprehensions (C4), return hygiene (RET),
          simplify (SIM)
        - Also enabled by default: unused imports (F401), unnecessary pass (PIE790)
          (disable with --no-ruff-clean)
        - Use --ruff-select to run specific rule groups (e.g., --ruff-select D ANN)
        - Use --ruff-list-groups to see all available groups

Usage (via repo.sh):
    # Run all tools on all extensions
    ./repo.sh run_python_linting

    # Run only mypy
    ./repo.sh run_python_linting --mypy

    # Run ruff to check docstrings, type annotations, and code quality
    ./repo.sh run_python_linting --ruff

    # Run ruff with auto-fix enabled (includes cleanup rules by default)
    ./repo.sh run_python_linting --ruff --fix

    # Run ruff with cleanup rules disabled
    ./repo.sh run_python_linting --ruff --no-ruff-clean

    # Run ruff checking only docstring rules
    ./repo.sh run_python_linting --ruff --ruff-select D

    # Run ruff checking only type annotation rules
    ./repo.sh run_python_linting --ruff --ruff-select ANN

    # Run ruff checking multiple specific groups
    ./repo.sh run_python_linting --ruff --ruff-select D ANN UP

    # List all available ruff rule groups
    ./repo.sh run_python_linting --ruff-list-groups

    # Run pydoclint to check docstrings don't contain types
    ./repo.sh run_python_linting --pydoclint

    # Check specific extensions
    ./repo.sh run_python_linting --extensions isaacsim.core.utils isaacsim.core.prims

    # Check extensions matching a pattern
    ./repo.sh run_python_linting --pattern "isaacsim.core.*"

    # Show only extensions with errors
    ./repo.sh run_python_linting --errors-only

    # Generate JSON report
    ./repo.sh run_python_linting --json-output report.json

    # Run all tools and report issues without failing (exit code 0)
    ./repo.sh run_python_linting --keep-going

    # Run tools only on files with a diff
    ./repo.sh run_python_linting --diff-only
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Ensure this script's directory is on sys.path so repo_helpers and term_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import EXTENSION_ROOTS, REPO_ROOT, all_extensions, get_uncommitted_files  # noqa: E402
from term_helpers import Colors, colorize  # noqa: E402

# =============================================================================
# Tool Configurations (hardcoded defaults when config files not supported)
# =============================================================================

# darglint configuration
# Note: "long" strictness doesn't require Returns section when function returns None
DARGLINT_CONFIG: dict[str, Any] = {
    "docstring_style": "google",
    "strictness": "long",  # short, long, or full (full is too strict about None returns)
}

# interrogate configuration
INTERROGATE_CONFIG: dict[str, Any] = {
    "ignore_init_method": True,
    "ignore_init_module": True,
    "ignore_magic": False,  # We want __del__ documented
    "ignore_private": True,
    "fail_under": 0,  # Don't fail, just report coverage
    "exclude": ["_vendor"],
}

# pydoclint configuration (enforces no types in docstrings - types belong in signatures)
# See python_docstrings.mdc for rationale on these settings
PYDOCLINT_CONFIG: dict[str, Any] = {
    "style": "google",
    "arg_type_hints_in_docstring": False,  # Types should NOT be in docstrings (rule: line 18)
    "arg_type_hints_in_signature": True,  # Types should be in function signatures (rule: line 18)
    "check_return_types": False,  # Disabled: we don't put types in docstrings (rule: line 35, 212)
    "check_yield_types": False,  # Disabled: we don't put types in docstrings
    "require_return_section_when_returning_nothing": False,  # Don't require Returns for void functions
    "skip_checking_short_docstrings": False,
    "skip_checking_raises": True,  # Raises documentation is optional per our conventions
    "check_class_attributes": False,  # Skip DOC602/DOC603 - Attributes sections are optional
    "exclude": ["_vendor"],
}

# ruff configuration (enforces docstring style, modern Python, naming, and code quality)
# D   = pydocstyle rules for docstring style (replaces standalone pydocstyle tool)
# ANN = flake8-annotations rules for enforcing type annotations
# UP  = pyupgrade rules for modernizing type annotations and syntax
# E   = pycodestyle error rules
# B   = flake8-bugbear rules for common pitfalls
# N   = pep8-naming rules for naming conventions
# C4  = flake8-comprehensions rules
# RET = flake8-return rules for return statement hygiene
# SIM = flake8-simplify rules
RUFF_CONFIG: dict[str, Any] = {
    "select": [
        # pydocstyle: docstring style checking (Google convention)
        # Replaces standalone pydocstyle tool. See python_docstrings.mdc for rationale on ignores.
        "D",  # all pydocstyle rules (D100-D418)
        # pyupgrade: modern type annotations and syntax
        "UP006",  # non-pep585-annotation: List[X] -> list[X], Dict -> dict, Set -> set
        "UP007",  # non-pep604-annotation-union: Union[X, Y] -> X | Y
        "UP008",  # super-call-with-parameters: Use super() instead of super(__class__, self)
        "UP015",  # redundant-open-modes: Unnecessary open mode parameters (e.g., open(f, "r"))
        "UP018",  # native-literals: Unnecessary call to str(), int(), float(), bytes()
        "UP031",  # printf-string-formatting: Use format specifiers instead of percent format
        "UP032",  # f-string: Use f-string instead of format() call
        "UP034",  # extraneous-parentheses: Extraneous parentheses
        "UP035",  # deprecated-import: deprecated typing module imports
        "UP039",  # unnecessary-class-parentheses: Unnecessary parentheses after class definition
        # flake8-annotations: enforce type annotations on all functions and methods
        "ANN001",  # missing-type-function-argument: Missing type annotation for function argument
        "ANN002",  # missing-type-args: Missing type annotation for *args
        "ANN003",  # missing-type-kwargs: Missing type annotation for **kwargs
        "ANN201",  # missing-return-type-public-function: Missing return type annotation for public function
        "ANN202",  # missing-return-type-private-function: Missing return type annotation for private function
        "ANN204",  # missing-return-type-special-method: Missing return type annotation for special method
        "ANN205",  # missing-return-type-static-method: Missing return type annotation for staticmethod
        "ANN206",  # missing-return-type-class-method: Missing return type annotation for classmethod
        # pycodestyle: basic error detection
        "E711",  # comparison-to-none: Use `is` / `is not` for None comparisons
        "E712",  # comparison-to-true-false: Use `if x:` / `if not x:` for booleans
        "E722",  # bare-except: Do not use bare `except`
        # flake8-bugbear: common pitfalls
        "B006",  # mutable-argument-default: Do not use mutable data structures for argument defaults
        # pep8-naming: enforce PEP 8 naming conventions
        "N801",  # invalid-class-name: Class name should use CapWords (PascalCase)
        "N802",  # invalid-function-name: Function name should be lowercase (snake_case)
        # flake8-comprehensions: simplify comprehensions
        "C4",  # all C4xx rules: unnecessary generators, list/dict/set comprehension simplifications
        # flake8-return: return statement hygiene
        "RET501",  # unnecessary-return-none: Do not explicitly return None if it's the only return
        "RET502",  # implicit-return-value: Do not implicitly return None when other branches return values
        # flake8-simplify: code simplifications
        "SIM101",  # duplicate-isinstance-call: Multiple isinstance calls for same variable, merge into one
        "SIM110",  # reimplemented-builtin: Use any()/all() instead of for-loop with early return
        "SIM115",  # open-file-with-context-handler: Use context handler for opening files
        "SIM118",  # in-dict-keys: Use `key in dict` instead of `key in dict.keys()`
        "SIM201",  # negate-equal-op: Use `!=` instead of `not ... ==`
        "SIM300",  # yoda-conditions: Yoda condition detected
        # pycodestyle: invalid escape sequences (SyntaxWarning in 3.12+, SyntaxError in future)
        "W605",  # invalid-escape-sequence: Invalid escape sequence in string
    ],
    # Ignored pydocstyle rules (see python_docstrings.mdc for rationale):
    # D104: Missing docstring in public package - we skip __init__.py files intentionally
    # D107: Missing docstring in __init__ - constructor Args go in class docstring for Sphinx autodoc
    # D412: No blank lines allowed between section header and content - our Example sections use
    #        .. code-block:: python RST directive which requires a blank line for proper Sphinx rendering
    "ignore": ["D104", "D107", "D412"],
    "pydocstyle_convention": "google",
    "target_version": "py310",  # Python 3.10+ for native union syntax
    "exclude": ["_vendor"],
}

# ruff cleanup rules for auto-fixable code hygiene
RUFF_CLEANUP_SELECT = [
    "F401",  # unused-import
    "PIE790",  # unnecessary-pass
]

# Named rule groups for --ruff-select (prefix -> human-readable description).
# Each key is matched as a prefix against the rules in RUFF_CONFIG["select"] and
# RUFF_CLEANUP_SELECT so users can test one category at a time.
RUFF_RULE_GROUPS: dict[str, str] = {
    "D": "pydocstyle – docstring style (Google convention)",
    "ANN": "flake8-annotations – type annotations on functions/methods",
    "UP": "pyupgrade – modern type annotations, syntax, f-strings",
    "E": "pycodestyle errors – None comparisons, bare except",
    "W": "pycodestyle warnings – invalid escape sequences",
    "B": "flake8-bugbear – mutable argument defaults",
    "N": "pep8-naming – PascalCase classes, snake_case functions",
    "C4": "flake8-comprehensions – unnecessary generators/comprehensions",
    "RET": "flake8-return – return statement hygiene",
    "SIM": "flake8-simplify – code simplifications",
    "F": "pyflakes – unused imports (cleanup)",
    "PIE": "flake8-pie – unnecessary pass (cleanup)",
}


# =============================================================================
# Result Classes
# =============================================================================


class ToolResult:
    """Results from running a single tool on an extension.

    Args:
        tool_name: Name of the tool that produced these results.
        errors: Number of errors reported.
        warnings: Number of warnings reported.
        messages: List of error/warning messages.
        coverage: Docstring coverage percentage, if applicable.
        duration_seconds: Time taken to run the tool.
        skipped: Whether the tool was skipped.
        skip_reason: Reason for skipping, if skipped.
    """

    def __init__(
        self,
        tool_name: str,
        errors: int = 0,
        warnings: int = 0,
        messages: list[str] | None = None,
        coverage: float | None = None,
        duration_seconds: float = 0.0,
        skipped: bool = False,
        skip_reason: str = "",
    ):
        self.tool_name = tool_name
        self.errors = errors
        self.warnings = warnings
        self.messages: list[str] = messages if messages is not None else []
        self.coverage = coverage
        self.duration_seconds = duration_seconds
        self.skipped = skipped
        self.skip_reason = skip_reason


class ExtensionResult:
    """Results from running all tools on a single extension.

    Args:
        name: Extension name.
        path: Path to the extension directory.
        files_checked: Number of Python files checked.
        tool_results: Dictionary mapping tool names to ToolResult objects.
        duration_seconds: Total time taken across all tools.
        skipped: Whether the extension was skipped.
        skip_reason: Reason for skipping, if skipped.
    """

    def __init__(
        self,
        name: str,
        path: str,
        files_checked: int = 0,
        tool_results: dict[str, ToolResult] | None = None,
        duration_seconds: float = 0.0,
        skipped: bool = False,
        skip_reason: str = "",
    ):
        self.name = name
        self.path = path
        self.files_checked = files_checked
        self.tool_results: dict[str, ToolResult] = tool_results if tool_results is not None else {}
        self.duration_seconds = duration_seconds
        self.skipped = skipped
        self.skip_reason = skip_reason

    @property
    def total_errors(self) -> int:
        """Get total errors across all tools."""
        return sum(r.errors for r in self.tool_results.values())

    @property
    def has_errors(self) -> bool:
        """Check if any tool reported errors."""
        return self.total_errors > 0


# =============================================================================
# Tool Discovery
# =============================================================================


class ToolInfo:
    """Information about an available tool.

    Args:
        name: Tool name.
        binary_path: Path to the tool binary.
        available: Whether the tool was found.
        version: Tool version string.
        error_message: Error message if tool was not found.
    """

    def __init__(
        self,
        name: str,
        binary_path: str | None = None,
        available: bool = False,
        version: str = "",
        error_message: str = "",
    ):
        self.name = name
        self.binary_path = binary_path
        self.available = available
        self.version = version
        self.error_message = error_message


def get_packman_python_bin() -> str | None:
    """Get the bin directory for the currently running Python environment.

    This uses sys.executable to find the bin directory, which works correctly
    when running under packman's Python via repo.sh.

    Returns:
        Path to the bin directory, or None if not found.
    """
    python_exe = Path(sys.executable).resolve()
    # Python executable is typically at .../python or .../bin/python
    # We want the bin directory
    if python_exe.parent.name == "bin":
        bin_dir = python_exe.parent
    else:
        # Python exe is directly in version dir (e.g., .../3.10.19-nv2-linux-x86_64/python)
        bin_dir = python_exe.parent / "bin"

    if bin_dir.exists():
        return str(bin_dir)
    return None


def find_tool(name: str, vendor_dir: str | None = None, packman_bin: str | None = None) -> ToolInfo:
    """Find a tool binary, checking vendor directory and packman bin first, then PATH.

    Args:
        name: Name of the tool (e.g., 'mypy', 'ruff').
        vendor_dir: Vendor directory to check first. Defaults to None.
        packman_bin: Packman Python bin directory. Defaults to None.

    Returns:
        ToolInfo with availability status and path.
    """
    info = ToolInfo(name=name)

    # Check vendor directory first (for repo_lint tools)
    if vendor_dir:
        vendor_path = Path(vendor_dir) / "bin" / name
        if vendor_path.exists():
            info.binary_path = str(vendor_path)
            info.available = True
            return info

    # Check packman Python bin directory (for pip-installed tools in packman env)
    if packman_bin:
        packman_path = Path(packman_bin) / name
        if packman_path.exists():
            info.binary_path = str(packman_path)
            info.available = True
            return info

    # Check system PATH
    system_path = shutil.which(name)
    if system_path:
        info.binary_path = system_path
        info.available = True
        return info

    info.error_message = f"{name} not found. Install with: pip install {name}"
    return info


def get_vendor_directory() -> str | None:
    """Get vendor directory from repo_lint if available.

    Returns:
        Path to the vendor directory, or None if omni.repo.lint is not available.
    """
    try:
        from omni.repo.lint import vendor_directory

        return str(vendor_directory)
    except ImportError:
        return None


def discover_tools(vendor_dir: str | None = None) -> dict[str, ToolInfo]:
    """Discover all available linting tools.

    Args:
        vendor_dir: Vendor directory to check for tools. Defaults to None.

    Returns:
        Dictionary mapping tool names to ToolInfo objects.
    """
    packman_bin = get_packman_python_bin()
    tools = {}
    for name in ["mypy", "darglint", "interrogate", "pydoclint", "ruff"]:
        tools[name] = find_tool(name, vendor_dir, packman_bin)
    return tools


# =============================================================================
# Extension Discovery
# =============================================================================


def find_python_dir(extension_path: Path) -> Path | None:
    """Find the Python source directory for an extension.

    Extensions can have different structures:
    - python/impl/  (common pattern)
    - python/       (simple python directory)
    - isaacsim/.../ (namespace package pattern)

    Args:
        extension_path: Path to the extension directory.

    Returns:
        Path to the Python source directory, or None if not found.
    """
    # Check for python/impl structure
    python_impl = extension_path / "python" / "impl"
    if python_impl.exists():
        return python_impl

    # Check for python directory with Python files
    python_dir = extension_path / "python"
    if python_dir.exists() and list(python_dir.rglob("*.py")):
        return python_dir

    # Check for isaacsim namespace package structure
    isaacsim_dir = extension_path / "isaacsim"
    if isaacsim_dir.exists():
        return isaacsim_dir

    # Check for any Python files directly
    if list(extension_path.glob("*.py")):
        return extension_path

    return None


def count_python_files(directory: Path, exclude_patterns: list[str] | None = None) -> int:
    """Count Python files in a directory, excluding certain patterns.

    Args:
        directory: Directory to search recursively.
        exclude_patterns: Glob patterns to exclude from the count.

    Returns:
        Number of Python files not matching any exclude pattern.
    """
    exclude_patterns = exclude_patterns or []
    count = 0
    for py_file in directory.rglob("*.py"):
        relative_path = str(py_file.relative_to(directory))
        excluded = False
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(py_file.name, pattern):
                excluded = True
                break
        if not excluded:
            count += 1
    return count


def filter_extensions_by_diff(extensions: list[Path], diff_files: set[Path]) -> list[Path]:
    """Filter extensions to those with changed Python files.

    Args:
        extensions: List of extension paths to filter.
        diff_files: Set of changed Python file paths.

    Returns:
        Extensions that contain at least one changed Python file.
    """
    filtered: list[Path] = []
    for extension in extensions:
        python_dir = find_python_dir(extension)
        if python_dir is None:
            continue
        python_dir_resolved = python_dir.resolve()
        for file_path in diff_files:
            try:
                if file_path.resolve().is_relative_to(python_dir_resolved):
                    filtered.append(extension)
                    break
            except ValueError:
                continue
    return filtered


# =============================================================================
# Tool Runners
# =============================================================================


def run_mypy(
    python_dir: Path,
    python_files: list[Path] | None,
    config_file: Path | None,
    exclude_patterns: list[str],
    tool_info: ToolInfo,
    vendor_dir: str | None,
    cwd: Path,
) -> ToolResult:
    """Run mypy on a directory.

    Args:
        python_dir: Directory containing Python files to check.
        python_files: Specific Python files to check, or None for all files in python_dir.
        config_file: Path to mypy configuration file.
        exclude_patterns: Patterns to exclude from checking.
        tool_info: Information about the mypy tool.
        vendor_dir: Vendor directory for PYTHONPATH.
        cwd: Current working directory for running the command.

    Returns:
        ToolResult with errors, warnings, and messages.
    """
    result = ToolResult(tool_name="mypy")

    if not tool_info.available:
        result.skipped = True
        result.skip_reason = tool_info.error_message
        return result

    assert tool_info.binary_path is not None
    cmd = [tool_info.binary_path]
    if config_file and config_file.exists():
        cmd.extend(["--config-file", str(config_file)])

    for pattern in exclude_patterns:
        cmd.extend(["--exclude", pattern])

    if python_files:
        cmd.extend([str(p) for p in python_files])
    else:
        cmd.append(str(python_dir))

    env = os.environ.copy()
    if vendor_dir:
        env["PYTHONPATH"] = vendor_dir
    else:
        env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
        result.duration_seconds = time.time() - start_time

        if proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                if ": error:" in line:
                    result.errors += 1
                    result.messages.append(line)
                elif ": warning:" in line:
                    result.warnings += 1
                    result.messages.append(line)
                elif line.strip() and not line.startswith("Success"):
                    result.messages.append(line)

    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running mypy: {e}"

    return result


def run_darglint(
    python_dir: Path,
    python_files: list[Path] | None,
    tool_info: ToolInfo,
    cwd: Path,
) -> ToolResult:
    """Run darglint on a directory.

    Args:
        python_dir: Directory containing Python files to check.
        python_files: Specific Python files to check, or None for all files in python_dir.
        tool_info: Information about the darglint tool.
        cwd: Current working directory for running the command.

    Returns:
        ToolResult with errors, warnings, and messages.
    """
    result = ToolResult(tool_name="darglint")

    if not tool_info.available:
        result.skipped = True
        result.skip_reason = tool_info.error_message
        return result

    # Find all Python files (darglint doesn't support directories directly)
    py_files = python_files if python_files is not None else list(python_dir.rglob("*.py"))
    # Exclude vendor files
    py_files = [f for f in py_files if "/_vendor/" not in str(f)]

    if not py_files:
        result.skipped = True
        result.skip_reason = "No Python files to check"
        return result

    assert tool_info.binary_path is not None
    cmd = [
        tool_info.binary_path,
        "--docstring-style={}".format(DARGLINT_CONFIG["docstring_style"]),
        "--strictness={}".format(DARGLINT_CONFIG["strictness"]),
    ] + [str(f) for f in py_files]

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        result.duration_seconds = time.time() - start_time

        # Check for tool crashes (e.g., ModuleNotFoundError)
        combined_output = (proc.stdout or "") + (proc.stderr or "")
        if "Traceback" in combined_output or "ModuleNotFoundError" in combined_output:
            result.skipped = True
            result.skip_reason = "darglint crashed (possibly not installed in this Python environment)"
            return result

        if proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    # darglint outputs errors as DAR### codes
                    if "DAR" in line:
                        result.errors += 1
                    result.messages.append(line)

    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running darglint: {e}"

    return result


def run_interrogate(
    python_dir: Path,
    python_files: list[Path] | None,
    tool_info: ToolInfo,
    cwd: Path,
) -> ToolResult:
    """Run interrogate on a directory.

    Args:
        python_dir: Directory containing Python files to check.
        python_files: Specific Python files to check, or None for all files in python_dir.
        tool_info: Information about the interrogate tool.
        cwd: Current working directory for running the command.

    Returns:
        ToolResult with errors, coverage, and messages.
    """
    result = ToolResult(tool_name="interrogate")

    if not tool_info.available:
        result.skipped = True
        result.skip_reason = tool_info.error_message
        return result

    assert tool_info.binary_path is not None
    cmd = [
        tool_info.binary_path,
        "--verbose",
        "--fail-under={}".format(INTERROGATE_CONFIG["fail_under"]),
    ]

    if INTERROGATE_CONFIG["ignore_init_method"]:
        cmd.append("--ignore-init-method")
    if INTERROGATE_CONFIG["ignore_init_module"]:
        cmd.append("--ignore-init-module")
    if INTERROGATE_CONFIG["ignore_magic"]:
        cmd.append("--ignore-magic")
    if INTERROGATE_CONFIG["ignore_private"]:
        cmd.append("--ignore-private")

    for exclude in INTERROGATE_CONFIG["exclude"]:
        cmd.extend(["--exclude", exclude])

    if python_files:
        cmd.extend([str(p) for p in python_files])
    else:
        cmd.append(str(python_dir))

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        result.duration_seconds = time.time() - start_time

        # Check for tool crashes (e.g., ModuleNotFoundError)
        combined_output = (proc.stdout or "") + (proc.stderr or "")
        if "Traceback" in combined_output or "ModuleNotFoundError" in combined_output:
            result.skipped = True
            result.skip_reason = "interrogate crashed (possibly not installed in this Python environment)"
            return result

        # Parse output for coverage percentage
        if proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                result.messages.append(line)
                # Look for coverage line like "TOTAL ... 85.0%"
                if "%" in line and ("TOTAL" in line or "actual" in line.lower()):
                    try:
                        # Extract percentage
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                result.coverage = float(part.replace("%", ""))
                                break
                    except ValueError:
                        pass

        # interrogate returns non-zero if below threshold
        if proc.returncode != 0 and result.coverage is not None:
            if result.coverage < INTERROGATE_CONFIG["fail_under"]:
                result.errors = 1

    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running interrogate: {e}"

    return result


def run_pydoclint(
    python_dir: Path,
    python_files: list[Path] | None,
    tool_info: ToolInfo,
    cwd: Path,
) -> ToolResult:
    """Run pydoclint on a directory.

    pydoclint validates that docstrings match function signatures and enforces
    that types are NOT included in docstrings (types belong in signatures only).

    Args:
        python_dir: Directory containing Python files to check.
        python_files: Specific Python files to check, or None for all files in python_dir.
        tool_info: Information about the pydoclint tool.
        cwd: Current working directory for running the command.

    Returns:
        ToolResult with errors and messages.
    """
    result = ToolResult(tool_name="pydoclint")

    if not tool_info.available:
        result.skipped = True
        result.skip_reason = tool_info.error_message
        return result

    assert tool_info.binary_path is not None
    cmd = [
        tool_info.binary_path,
        "--style={}".format(PYDOCLINT_CONFIG["style"]),
        "--arg-type-hints-in-docstring={}".format(str(PYDOCLINT_CONFIG["arg_type_hints_in_docstring"]).lower()),
        "--arg-type-hints-in-signature={}".format(str(PYDOCLINT_CONFIG["arg_type_hints_in_signature"]).lower()),
        "--check-return-types={}".format(str(PYDOCLINT_CONFIG["check_return_types"]).lower()),
        "--check-yield-types={}".format(str(PYDOCLINT_CONFIG["check_yield_types"]).lower()),
        "--require-return-section-when-returning-nothing={}".format(
            str(PYDOCLINT_CONFIG["require_return_section_when_returning_nothing"]).lower()
        ),
        "--skip-checking-short-docstrings={}".format(str(PYDOCLINT_CONFIG["skip_checking_short_docstrings"]).lower()),
        "--skip-checking-raises={}".format(str(PYDOCLINT_CONFIG["skip_checking_raises"]).lower()),
        "--check-class-attributes={}".format(str(PYDOCLINT_CONFIG["check_class_attributes"]).lower()),
    ]

    for exclude in PYDOCLINT_CONFIG["exclude"]:
        cmd.extend(["--exclude", exclude])

    if python_files:
        cmd.extend([str(p) for p in python_files])
    else:
        cmd.append(str(python_dir))

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        result.duration_seconds = time.time() - start_time

        # Check for tool crashes (e.g., ModuleNotFoundError)
        if proc.stderr and ("Traceback" in proc.stderr or "ModuleNotFoundError" in proc.stderr):
            result.skipped = True
            result.skip_reason = "pydoclint crashed (possibly not installed in this Python environment)"
            return result

        # pydoclint outputs to stderr, not stdout
        output = proc.stderr.strip() if proc.stderr.strip() else proc.stdout.strip()
        if output:
            for line in output.split("\n"):
                if line.strip():
                    # Look for DOC error codes (e.g., DOC111, DOC203)
                    if ": DOC" in line:
                        result.errors += 1
                        result.messages.append(line)

    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running pydoclint: {e}"

    return result


def run_ruff(
    python_dir: Path,
    python_files: list[Path] | None,
    tool_info: ToolInfo,
    cwd: Path,
    fix: bool = False,
    cleanup: bool = False,
    ruff_select: list[str] | None = None,
) -> ToolResult:
    """Run ruff on a directory.

    ruff checks for docstring style, type annotations, naming, and code quality:
    - D: pydocstyle rules for docstring style (Google convention)
    - ANN: flake8-annotations rules (require type annotations on all functions/methods)
    - UP: pyupgrade rules for modern annotations, syntax, and f-strings
    - E: pycodestyle error rules (None comparisons, bare except)
    - B: flake8-bugbear rules (mutable defaults)
    - N: pep8-naming conventions (PascalCase classes, snake_case functions)
    - C4: flake8-comprehensions rules
    - RET: return statement hygiene
    - SIM: flake8-simplify rules
    Cleanup rules (enabled by default, disable with --no-ruff-clean):
    - F401: Remove unused imports
    - PIE790: Remove unnecessary pass statements

    Args:
        python_dir: Directory containing Python files to check.
        python_files: Specific Python files to check, or None for all files in python_dir.
        tool_info: Information about the ruff tool.
        cwd: Current working directory for running the command.
        fix: If True, automatically fix issues.
        cleanup: If True, include cleanup rules.
        ruff_select: If provided, only include rules whose code starts with one of
            these prefixes (e.g. ``["D", "ANN"]``).

    Returns:
        ToolResult with errors, warnings, and messages.
    """
    result = ToolResult(tool_name="ruff")

    if not tool_info.available:
        result.skipped = True
        result.skip_reason = tool_info.error_message
        return result

    # Build select rules string
    select_rules = list(RUFF_CONFIG["select"])
    if cleanup:
        select_rules.extend(RUFF_CLEANUP_SELECT)
    select_rules = sorted(set(select_rules))

    # Filter to only the requested rule groups
    if ruff_select:
        prefixes = [p.upper() for p in ruff_select]
        select_rules = [r for r in select_rules if any(r.startswith(p) for p in prefixes)]
        if not select_rules:
            result.skipped = True
            result.skip_reason = (
                f"No rules match --ruff-select {' '.join(ruff_select)}. "
                "Use --ruff-list-groups to see available groups."
            )
            return result
    select_rules_arg = ",".join(select_rules)
    select_rules_set = set(select_rules)

    assert tool_info.binary_path is not None
    cmd = [
        tool_info.binary_path,
        "check",
        f"--select={select_rules_arg}",
        "--target-version={}".format(RUFF_CONFIG["target_version"]),
    ]

    # Add pydocstyle convention if D rules are selected
    if any(rule.startswith("D") for rule in select_rules):
        cmd.append('--config=lint.pydocstyle.convention="{}"'.format(RUFF_CONFIG["pydocstyle_convention"]))

    # Add ignored rules
    if RUFF_CONFIG.get("ignore"):
        cmd.append("--ignore={}".format(",".join(RUFF_CONFIG["ignore"])))

    if fix:
        cmd.append("--fix")
    else:
        cmd.append("--no-fix")

    for exclude in RUFF_CONFIG["exclude"]:
        cmd.extend(["--exclude", exclude])

    if python_files:
        cmd.extend([str(p) for p in python_files])
    else:
        cmd.append(str(python_dir))

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        result.duration_seconds = time.time() - start_time

        # ruff outputs errors with file:line:col: CODE message format
        if proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    # Count lines with selected rule codes as errors
                    if any(rule in line for rule in select_rules_set):
                        result.errors += 1
                    result.messages.append(line)

        # Also check stderr for any errors
        if proc.stderr.strip():
            # ruff may output summary to stderr
            for line in proc.stderr.strip().split("\n"):
                if line.strip() and "error" in line.lower():
                    result.messages.append(f"[stderr] {line}")

    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running ruff: {e}"

    return result


# =============================================================================
# Main Runner
# =============================================================================


def run_tools_on_extension(
    extension_path: Path,
    tools: dict[str, ToolInfo],
    enabled_tools: set[str],
    mypy_config: Path | None,
    exclude_patterns: list[str],
    vendor_dir: str | None,
    fix: bool = False,
    cleanup: bool = False,
    diff_files: set[Path] | None = None,
    ruff_select: list[str] | None = None,
) -> ExtensionResult:
    """Run all enabled tools on a single extension.

    Args:
        extension_path: Path to the extension directory.
        tools: Dictionary mapping tool names to ToolInfo objects.
        enabled_tools: Set of tool names to run.
        mypy_config: Path to mypy configuration file.
        exclude_patterns: List of patterns to exclude from checking.
        vendor_dir: Vendor directory for tools.
        fix: If True, automatically fix issues where supported.
        cleanup: If True, include ruff cleanup rules.
        diff_files: Set of changed Python file paths, or None to check all files.
        ruff_select: If provided, only run these ruff rule groups.

    Returns:
        ExtensionResult with results from all enabled tools.
    """
    result = ExtensionResult(name=extension_path.name, path=str(extension_path))

    # Find Python source directory
    python_dir = find_python_dir(extension_path)
    if python_dir is None:
        result.skipped = True
        result.skip_reason = "No Python source directory found"
        return result

    python_dir_resolved = python_dir.resolve()
    python_files: list[Path] | None = None
    if diff_files is not None:
        python_files = []
        for file_path in diff_files:
            try:
                if file_path.resolve().is_relative_to(python_dir_resolved):
                    python_files.append(file_path)
            except ValueError:
                continue
        if not python_files:
            result.skipped = True
            result.skip_reason = "No changed Python files to check"
            return result
        result.files_checked = len(python_files)
    else:
        result.files_checked = count_python_files(python_dir)
        if result.files_checked == 0:
            result.skipped = True
            result.skip_reason = "No Python files to check"
            return result

    if result.files_checked == 0:
        result.skipped = True
        result.skip_reason = "No Python files to check"
        return result

    cwd = extension_path.parent.parent.parent
    start_time = time.time()

    # Run each enabled tool
    if "mypy" in enabled_tools:
        result.tool_results["mypy"] = run_mypy(
            python_dir, python_files, mypy_config, exclude_patterns, tools["mypy"], vendor_dir, cwd
        )

    if "darglint" in enabled_tools:
        result.tool_results["darglint"] = run_darglint(python_dir, python_files, tools["darglint"], cwd)

    if "interrogate" in enabled_tools:
        result.tool_results["interrogate"] = run_interrogate(python_dir, python_files, tools["interrogate"], cwd)

    if "pydoclint" in enabled_tools:
        result.tool_results["pydoclint"] = run_pydoclint(python_dir, python_files, tools["pydoclint"], cwd)

    if "ruff" in enabled_tools:
        result.tool_results["ruff"] = run_ruff(
            python_dir, python_files, tools["ruff"], cwd, fix=fix, cleanup=cleanup, ruff_select=ruff_select
        )

    result.duration_seconds = time.time() - start_time
    return result


def run_tools_on_directory(
    target: Path,
    tools: dict[str, ToolInfo],
    enabled_tools: set[str],
    mypy_config: Path | None,
    exclude_patterns: list[str],
    vendor_dir: str | None,
    fix: bool = False,
    cleanup: bool = False,
    ruff_select: list[str] | None = None,
) -> ExtensionResult:
    """Run all enabled tools directly on an arbitrary directory or file.

    Unlike `run_tools_on_extension`, this does not look for extension-specific
    sub-directories (python/, isaacsim/, etc.).  It treats the given *target*
    as the Python source root.

    Args:
        target: Path to a directory (recursively scanned) or single .py file.
        tools: Dictionary mapping tool names to ToolInfo objects.
        enabled_tools: Set of tool names to run.
        mypy_config: Path to mypy configuration file.
        exclude_patterns: List of patterns to exclude from checking.
        vendor_dir: Vendor directory for tools.
        fix: If True, automatically fix issues where supported.
        cleanup: If True, include ruff cleanup rules.
        ruff_select: If provided, only run these ruff rule groups.

    Returns:
        ExtensionResult with results from all enabled tools.
    """
    result = ExtensionResult(name=target.name, path=str(target))

    if target.is_file():
        python_dir = target.parent
        python_files: list[Path] | None = [target]
        result.files_checked = 1
    else:
        python_dir = target
        python_files = None
        result.files_checked = count_python_files(target, exclude_patterns)
        if result.files_checked == 0:
            result.skipped = True
            result.skip_reason = "No Python files found"
            return result

    cwd = target if target.is_dir() else target.parent
    start_time = time.time()

    if "mypy" in enabled_tools:
        result.tool_results["mypy"] = run_mypy(
            python_dir, python_files, mypy_config, exclude_patterns, tools["mypy"], vendor_dir, cwd
        )

    if "darglint" in enabled_tools:
        result.tool_results["darglint"] = run_darglint(python_dir, python_files, tools["darglint"], cwd)

    if "interrogate" in enabled_tools:
        result.tool_results["interrogate"] = run_interrogate(python_dir, python_files, tools["interrogate"], cwd)

    if "pydoclint" in enabled_tools:
        result.tool_results["pydoclint"] = run_pydoclint(python_dir, python_files, tools["pydoclint"], cwd)

    if "ruff" in enabled_tools:
        result.tool_results["ruff"] = run_ruff(
            python_dir, python_files, tools["ruff"], cwd, fix=fix, cleanup=cleanup, ruff_select=ruff_select
        )

    result.duration_seconds = time.time() - start_time
    return result


# =============================================================================
# Output Formatting
# =============================================================================


def print_tool_availability(tools: dict[str, ToolInfo], use_color: bool = True) -> None:
    """Print tool availability status.

    Args:
        tools: Dictionary mapping tool names to ToolInfo objects.
        use_color: Whether to use colored output.
    """
    print("\nTool availability:")
    for name, info in tools.items():
        if info.available:
            status = colorize("available", Colors.GREEN, use_color)
            path = colorize(f"({info.binary_path})", Colors.DIM, use_color)
            print(f"  {name}: {status} {path}")
        else:
            status = colorize("NOT FOUND", Colors.RED, use_color)
            print(f"  {name}: {status} - {info.error_message}")


def print_summary(
    results: list[ExtensionResult],
    enabled_tools: set[str],
    use_color: bool = True,
    errors_only: bool = False,
) -> None:
    """Print a summary of all results.

    Args:
        results: List of ExtensionResult objects from each extension.
        enabled_tools: Set of tool names that were run.
        use_color: Whether to use colored output.
        errors_only: If True, only show extensions with errors in the summary table.
    """
    total_extensions = len(results)
    passed = sum(1 for r in results if not r.has_errors and not r.skipped)
    failed = sum(1 for r in results if r.has_errors)
    skipped = sum(1 for r in results if r.skipped)
    total_time = sum(r.duration_seconds for r in results)

    # Print errors grouped by tool and extension
    failed_results = [r for r in results if r.has_errors]
    if failed_results:
        for tool_name in enabled_tools:
            tool_errors = [
                (r, r.tool_results[tool_name])
                for r in failed_results
                if tool_name in r.tool_results and r.tool_results[tool_name].errors > 0
            ]

            if tool_errors:
                print("\n" + "=" * 80)
                print(f"{tool_name.upper()} ERRORS")
                print("=" * 80)

                for ext_result, tool_result in tool_errors:
                    print(f"\n## {ext_result.name} ({tool_result.errors} errors)")
                    for msg in tool_result.messages:
                        print(f"  {msg}")

    # Print skipped tools summary
    skipped_tools_info: dict[str, list[tuple[str, str]]] = {}  # tool_name -> [(ext_name, reason), ...]
    for r in results:
        for tool_name, tr in r.tool_results.items():
            if tr.skipped:
                if tool_name not in skipped_tools_info:
                    skipped_tools_info[tool_name] = []
                skipped_tools_info[tool_name].append((r.name, tr.skip_reason))

    if skipped_tools_info:
        print("\n" + "=" * 80)
        print("SKIPPED TOOLS")
        print("=" * 80)
        for tool_name, skip_list in sorted(skipped_tools_info.items()):
            print(f"\n  {tool_name} ({len(skip_list)} skipped):")
            # Show unique skip reasons
            reasons = {reason for _, reason in skip_list}
            for reason in reasons:
                print(f"    - {colorize(reason, Colors.YELLOW, use_color)}")

    # Print coverage summary for interrogate
    if "interrogate" in enabled_tools:
        coverage_results = [
            (r.name, r.tool_results["interrogate"].coverage)
            for r in results
            if "interrogate" in r.tool_results
            and r.tool_results["interrogate"].coverage is not None
            and not r.tool_results["interrogate"].skipped
        ]
        if coverage_results:
            print("\n" + "=" * 80)
            print("DOCSTRING COVERAGE (interrogate)")
            print("=" * 80)
            for name, coverage in sorted(coverage_results, key=lambda x: x[1] or 0):
                color = Colors.GREEN if coverage >= 80 else Colors.YELLOW if coverage >= 50 else Colors.RED
                print("  {}: {}".format(name, colorize(f"{coverage:.1f}%", color, use_color)))

    # Print summary table
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for result in results:
        if errors_only and not result.has_errors and not result.skipped:
            continue

        if result.skipped:
            status = colorize("SKIP", Colors.YELLOW, use_color)
            detail = result.skip_reason
        elif not result.has_errors:
            status = colorize("PASS", Colors.GREEN, use_color)
            tool_summary = []
            for tool_name in enabled_tools:
                if tool_name in result.tool_results:
                    tr = result.tool_results[tool_name]
                    if not tr.skipped:
                        if tool_name == "interrogate" and tr.coverage is not None:
                            tool_summary.append(f"{tool_name}:{tr.coverage:.0f}%")
                        else:
                            tool_summary.append(f"{tool_name}:ok")
            detail = ", ".join(tool_summary) if tool_summary else f"{result.files_checked} files"
        else:
            status = colorize("FAIL", Colors.RED, use_color)
            err_labels: list[str] = []
            tool_skipped: list[str] = []
            for tool_name in enabled_tools:
                if tool_name in result.tool_results:
                    tr = result.tool_results[tool_name]
                    if tr.errors > 0:
                        err_labels.append(f"{tool_name}:{tr.errors}")
                    elif tr.skipped:
                        tool_skipped.append(f"{tool_name}:skip")
            parts: list[str] = err_labels + tool_skipped
            detail = ", ".join(parts) if parts else "errors found"

        print(f"  [{status}] {result.name}: {detail}")

    print(f"\nTotal: {total_extensions} extensions, {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Time: {total_time:.2f}s")


def save_json_report(results: list[ExtensionResult], output_path: Path) -> None:
    """Save results as a JSON report.

    Args:
        results: List of ExtensionResult objects to serialize.
        output_path: Path to write the JSON file.
    """
    report = {
        "summary": {
            "total_extensions": len(results),
            "passed": sum(1 for r in results if not r.has_errors and not r.skipped),
            "failed": sum(1 for r in results if r.has_errors),
            "skipped": sum(1 for r in results if r.skipped),
        },
        "extensions": [
            {
                "name": r.name,
                "path": r.path,
                "files_checked": r.files_checked,
                "total_errors": r.total_errors,
                "duration_seconds": r.duration_seconds,
                "skipped": r.skipped,
                "skip_reason": r.skip_reason,
                "tools": {
                    name: {
                        "errors": tr.errors,
                        "warnings": tr.warnings,
                        "messages": tr.messages,
                        "coverage": tr.coverage,
                        "duration_seconds": tr.duration_seconds,
                        "skipped": tr.skipped,
                        "skip_reason": tr.skip_reason,
                    }
                    for name, tr in r.tool_results.items()
                },
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nJSON report saved to: {output_path}")


# =============================================================================
# Repo Tool Integration
# =============================================================================


def setup_repo_tool(parser: argparse.ArgumentParser, config: dict[str, Any]) -> Callable:
    """Setup function for the repo tool integration.

    Args:
        parser: ArgumentParser to configure with command-line arguments.
        config: Configuration dictionary from repo.toml.

    Returns:
        The run_tool function to execute the tool.
    """
    parser.description = (
        "Run Python linting tools on extensions under source/extensions, source/internal_extensions, "
        "and source/deprecated (mypy, darglint, interrogate, pydoclint, ruff). "
        "Ruff enforces docstring style (Google convention), type annotations (ANN), modern annotations, "
        "naming, pycodestyle, bugbear, comprehensions, return hygiene, and simplify rules by default. "
        "Ruff cleanup rules for unused imports/pass removal are enabled by default; "
        "use --no-ruff-clean to disable."
    )

    # Target selection
    parser.add_argument(
        "--path",
        nargs="+",
        type=Path,
        help="Run linting on one or more arbitrary directories/files instead of "
        "discovering extensions (e.g., tools/isaac/pre_merge).",
    )

    # Extension selection
    parser.add_argument(
        "--extensions",
        "-e",
        nargs="+",
        help="Specific extension names to check (e.g., isaacsim.core.utils)",
    )
    parser.add_argument(
        "--pattern",
        "-p",
        help="Glob pattern to filter extensions (e.g., 'isaacsim.core.*')",
    )
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only run tools on Python files with a diff (staged, unstaged, or untracked)",
    )

    # Tool selection (if none specified, all are enabled)
    parser.add_argument(
        "--mypy",
        action="store_true",
        help="Run mypy type checking",
    )
    parser.add_argument(
        "--darglint",
        action="store_true",
        help="Run darglint docstring argument validation",
    )
    parser.add_argument(
        "--interrogate",
        action="store_true",
        help="Run interrogate docstring coverage",
    )
    parser.add_argument(
        "--pydoclint",
        action="store_true",
        help="Run pydoclint to validate docstrings don't contain types (types belong in signatures)",
    )
    parser.add_argument(
        "--ruff",
        action="store_true",
        help="Run ruff to check docstring style, modern type annotations, and code quality",
    )
    parser.add_argument(
        "--ruff-clean",
        dest="ruff_clean",
        action="store_true",
        default=True,
        help="Include ruff cleanup rules (enabled by default)",
    )
    parser.add_argument(
        "--no-ruff-clean",
        dest="ruff_clean",
        action="store_false",
        help="Disable ruff cleanup rules",
    )
    parser.add_argument(
        "--ruff-select",
        nargs="+",
        metavar="GROUP",
        help="Only check specific ruff rule groups (e.g., D ANN UP). "
        "Use --ruff-list-groups to see available groups.",
    )
    parser.add_argument(
        "--ruff-list-groups",
        action="store_true",
        help="List available ruff rule groups and exit",
    )

    # Configuration
    parser.add_argument(
        "--mypy-config",
        help="Path to mypy configuration file (default: tools/isaac/pre_merge/.mypy.ini)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Regex patterns to exclude from mypy checking",
    )

    # Fix options
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues where supported (currently: ruff)",
    )

    # Output options
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only show extensions with errors in summary",
    )
    parser.add_argument(
        "--json-output",
        "-j",
        help="Save results to JSON file",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--keep-going",
        "-k",
        action="store_true",
        help="Return exit code 0 even if errors are found (report all issues without failing)",
    )

    tool_config = config.get("repo_run_python_linting", {})

    def run_tool(args: argparse.Namespace, config: dict[str, Any] = config) -> int:
        """Run the Python linting tool.

        Args:
            args: Parsed command-line arguments.
            config: Configuration dictionary.

        Returns:
            0 if all checks passed (or --keep-going is set), 1 if there were errors.
        """
        repo_root = Path(config.get("root", os.getcwd()))
        use_color = not args.no_color

        # Handle --ruff-list-groups: print groups and exit
        if args.ruff_list_groups:
            print("\nAvailable ruff rule groups (use with --ruff-select):\n")
            all_rules = list(RUFF_CONFIG["select"]) + RUFF_CLEANUP_SELECT
            for prefix, description in sorted(RUFF_RULE_GROUPS.items()):
                matching = sorted(r for r in all_rules if r.startswith(prefix))
                rules_str = ", ".join(matching) if len(matching) <= 8 else f"{len(matching)} rules"
                print(f"  {prefix:5s}  {description}")
                print(f"         rules: {rules_str}")
            return 0

        # --ruff-select implies --ruff
        if args.ruff_select:
            args.ruff = True

        # Determine which tools to run
        tool_flags = {
            "mypy": args.mypy,
            "darglint": args.darglint,
            "interrogate": args.interrogate,
            "pydoclint": args.pydoclint,
            "ruff": args.ruff,
        }
        # If no specific tools requested, run all
        if not any(tool_flags.values()):
            enabled_tools = set(tool_flags.keys())
        else:
            enabled_tools = {name for name, enabled in tool_flags.items() if enabled}

        # Discover available tools
        vendor_dir = get_vendor_directory()
        tools = discover_tools(vendor_dir)

        # Print tool availability
        print_tool_availability(tools, use_color)

        # Check if any enabled tools are missing
        missing_tools = [name for name in enabled_tools if not tools[name].available]
        if missing_tools:
            print(
                colorize(
                    "\nWarning: Some tools not available: {}".format(", ".join(missing_tools)), Colors.YELLOW, use_color
                )
            )
            print("These tools will be skipped.\n")

        # Determine mypy config file
        mypy_config = None
        if args.mypy_config:
            mypy_config = Path(args.mypy_config)
        else:
            config_path = tool_config.get("mypy_config", "${root}/tools/isaac/pre_merge/.mypy.ini")
            config_path = config_path.replace("${root}", str(repo_root))
            default_config = Path(config_path)
            if default_config.exists():
                mypy_config = default_config

        exclude_patterns = args.exclude or tool_config.get("exclude", [])

        # ---- Path mode: lint arbitrary directories/files ----
        if args.path:
            targets = [p.resolve() for p in args.path]
            for t in targets:
                if not t.exists():
                    print(f"Error: path does not exist: {t}")
                    return 1

            print(
                colorize(
                    "\nRunning {} on {} path(s)...".format(", ".join(sorted(enabled_tools)), len(targets)),
                    Colors.CYAN,
                    use_color,
                )
            )
            if args.fix:
                print(colorize("Fix mode enabled: ruff will auto-fix issues", Colors.YELLOW, use_color))
                if args.ruff_clean:
                    print(colorize("Ruff cleanup enabled: unused imports and pass removal", Colors.DIM, use_color))
            if args.ruff_select and "ruff" in enabled_tools:
                print(colorize(f"Ruff rule groups: {' '.join(args.ruff_select)}", Colors.DIM, use_color))
            if mypy_config and "mypy" in enabled_tools:
                print(colorize(f"Using mypy config: {mypy_config}", Colors.DIM, use_color))

            results: list[ExtensionResult] = []
            for i, target in enumerate(targets, 1):
                progress = f"[{i}/{len(targets)}]"
                print(f"  {progress} Checking {target}...", end=" ", flush=True)

                result = run_tools_on_directory(
                    target=target,
                    tools=tools,
                    enabled_tools=enabled_tools,
                    mypy_config=mypy_config,
                    exclude_patterns=exclude_patterns,
                    vendor_dir=vendor_dir,
                    fix=args.fix,
                    cleanup=args.ruff_clean,
                    ruff_select=args.ruff_select,
                )
                results.append(result)

                if result.skipped:
                    print(colorize("skipped", Colors.YELLOW, use_color))
                elif not result.has_errors:
                    print(colorize("ok", Colors.GREEN, use_color))
                else:
                    error_summary = ", ".join(
                        f"{name}:{tr.errors}" for name, tr in result.tool_results.items() if tr.errors > 0
                    )
                    print(colorize(error_summary, Colors.RED, use_color))

            # Print summary
            print_summary(results, enabled_tools, use_color=use_color, errors_only=args.errors_only)

            if args.json_output:
                save_json_report(results, Path(args.json_output))

            total_errors = sum(r.total_errors for r in results)
            if args.keep_going:
                return 0
            return 1 if total_errors > 0 else 0

        # ---- Extension mode (default) ----

        discovered_extensions = all_extensions()
        if not discovered_extensions:
            root_list = ", ".join(str(p) for p in EXTENSION_ROOTS)
            print(f"Error: No extensions found in {root_list}")
            return 1

        extensions_to_check = discovered_extensions
        if args.extensions:
            extensions_to_check = [e for e in discovered_extensions if e.name in args.extensions]
            if not extensions_to_check:
                print(f"Error: No matching extensions found for: {args.extensions}")
                return 1
        elif args.pattern:
            extensions_to_check = [e for e in discovered_extensions if fnmatch.fnmatch(e.name, args.pattern)]
            if not extensions_to_check:
                print(f"Error: No extensions matching pattern: {args.pattern}")
                return 1

        diff_files: set[Path] | None = None
        if args.diff_only:
            diff_files = {p for p in get_uncommitted_files() if p.suffix == ".py"}
            if not diff_files:
                print(colorize("\nNo changed Python files found.", Colors.YELLOW, use_color))
                return 0
            extensions_to_check = filter_extensions_by_diff(extensions_to_check, diff_files)
            if not extensions_to_check:
                print(colorize("\nNo extensions contain changed Python files.", Colors.YELLOW, use_color))
                return 0

        # Run tools on each extension
        print(
            colorize(
                "\nRunning {} on {} extensions...".format(", ".join(sorted(enabled_tools)), len(extensions_to_check)),
                Colors.CYAN,
                use_color,
            )
        )
        if args.diff_only:
            print(colorize("Diff-only mode enabled: checking changed Python files only", Colors.DIM, use_color))
        if args.fix:
            print(colorize("Fix mode enabled: ruff will auto-fix issues", Colors.YELLOW, use_color))
            if args.ruff_clean:
                print(colorize("Ruff cleanup enabled: unused imports and pass removal", Colors.DIM, use_color))
        if args.ruff_select and "ruff" in enabled_tools:
            print(colorize(f"Ruff rule groups: {' '.join(args.ruff_select)}", Colors.DIM, use_color))
        if mypy_config and "mypy" in enabled_tools:
            print(colorize(f"Using mypy config: {mypy_config}", Colors.DIM, use_color))

        results = []
        for i, extension in enumerate(extensions_to_check, 1):
            progress = f"[{i}/{len(extensions_to_check)}]"
            print(f"  {progress} Checking {extension.name}...", end=" ", flush=True)

            result = run_tools_on_extension(
                extension_path=extension,
                tools=tools,
                enabled_tools=enabled_tools,
                mypy_config=mypy_config,
                exclude_patterns=exclude_patterns,
                vendor_dir=vendor_dir,
                fix=args.fix,
                cleanup=args.ruff_clean,
                diff_files=diff_files,
                ruff_select=args.ruff_select,
            )
            results.append(result)

            if result.skipped:
                print(colorize("skipped", Colors.YELLOW, use_color))
            elif not result.has_errors:
                print(colorize("ok", Colors.GREEN, use_color))
            else:
                error_summary = ", ".join(
                    f"{name}:{tr.errors}" for name, tr in result.tool_results.items() if tr.errors > 0
                )
                print(colorize(error_summary, Colors.RED, use_color))

        # Print summary
        print_summary(results, enabled_tools, use_color=use_color, errors_only=args.errors_only)

        # Save JSON report if requested
        if args.json_output:
            save_json_report(results, Path(args.json_output))

        # Return exit code
        total_errors = sum(r.total_errors for r in results)
        if args.keep_going:
            return 0  # Always return success when --keep-going is specified
        return 1 if total_errors > 0 else 0

    return run_tool


def main() -> int:
    """Main entry point for standalone execution.

    Returns:
        0 on success, 1 if linting errors were found.
    """
    parser = argparse.ArgumentParser(
        description="Run Python linting tools on extensions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    config = {"root": str(REPO_ROOT)}

    run_tool = setup_repo_tool(parser, config)
    args = parser.parse_args()

    return run_tool(args, config)


if __name__ == "__main__":
    sys.exit(main())
