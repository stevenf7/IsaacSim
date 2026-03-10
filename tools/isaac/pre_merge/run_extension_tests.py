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

r"""Discover and run tests for Isaac Sim extensions.

Scans the build directory for test scripts related to each specified extension:
  - Extension unit tests:    tests-{ext}.sh  (.bat on Windows)
  - Python sample tests:     tests-nativepython-{ext}.*.sh
  - Python testing tests:    tests-nativepython-testing-{ext}.*.sh

Tests are executed in two tiers:
  - Tier 1 (direct):     tests for the explicitly specified extensions.
  - Tier 2 (downstream): tests for extensions that depend on a Tier 1 extension.

Tier 2 only runs if every Tier 1 test passes.

When --downstream is enabled (default), extensions that declare a direct
dependency on any specified extension are automatically included in Tier 2.

A rolling terminal window shows the last 20 lines of test output in real time
when attached to a TTY.

Extensions can be specified by name or by directory path:
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser
    python tools/isaac/pre_merge/run_extension_tests.py source/extensions/isaacsim.robot.poser

Usage:
    # Run tests for specific extensions
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser

    # Multiple extensions
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser isaacsim.robot.schema

    # Include isaacsim.app.setup when source/apps/ changed
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser --apps-changed

    # Skip downstream dependents
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser --no-downstream

    # Filter to specific test names
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser \\
        --filter "test_named_poses*"

    # Re-run only specific failing extensions from a previous run
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser isaacsim.robot.schema \\
        --only isaacsim.robot.poser

    # Write results to a log file as tests finish
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser --log test_results.log

    # List discovered tests without running them
    python tools/isaac/pre_merge/run_extension_tests.py isaacsim.robot.poser --list
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TextIO

# Ensure this script's directory is on sys.path so repo_helpers and term_helpers (same dir) can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import (
    APP_SETUP_EXT,
    BUILD_DIR,
    TEST_SCRIPT_EXT,
    all_extension_names,
    build_reverse_deps,
)
from term_helpers import Colors, log_fail, log_info, log_pass, log_warn

_ROLLING_WINDOW_LINES = 20
_REDRAW_MIN_INTERVAL = 0.10


# ---------------------------------------------------------------------------
# Test script discovery
# ---------------------------------------------------------------------------


def _find_all_test_scripts(ext_name: str, all_ext_names: list[str]) -> list[Path]:
    """Locate all test scripts related to the given extension in the build directory.

    Searches for (using .sh on Linux, .bat on Windows):
      - Extension unit tests:  tests-{ext_name}{ext}
      - Python sample tests:   tests-nativepython-{ext_name}.*{ext}
      - Python testing tests:  tests-nativepython-testing-{ext_name}.*{ext}

    Scripts belonging to a longer-named extension that shares the same prefix
    are excluded (e.g. isaacsim.robot.poser.ui tests are not claimed when
    searching for isaacsim.robot.poser).

    Args:
        ext_name: Extension name to search for (e.g. isaacsim.robot.poser).
        all_ext_names: All known extension names, used to exclude longer prefixes.

    Returns:
        Sorted list of test script paths for the extension.

    """
    tests_dir = BUILD_DIR / "tests"
    if not tests_dir.exists():
        return []

    longer_exts = [e for e in all_ext_names if e != ext_name and e.startswith(ext_name + ".")]

    def _matches(fname: str, name: str) -> bool:
        return any(
            fname.startswith(p)
            for p in (f"tests-{name}.", f"tests-nativepython-{name}.", f"tests-nativepython-testing-{name}.")
        )

    return [
        s
        for s in sorted(tests_dir.glob(f"*{TEST_SCRIPT_EXT}"))
        if _matches(s.name, ext_name) and not any(_matches(s.name, le) for le in longer_exts)
    ]


# ---------------------------------------------------------------------------
# Test execution with rolling terminal window
# ---------------------------------------------------------------------------


def _run_test_script(
    script: Path,
    test_filter: str | None = None,
    timeout: int = 600,
) -> tuple[bool, str]:
    """Run a single test shell script with live rolling output.

    When attached to a TTY, displays a rolling window of the last
    ``_ROLLING_WINDOW_LINES`` lines of test output that updates in real time.
    Redraws are throttled to at most once per ``_REDRAW_MIN_INTERVAL`` seconds.
    The window is cleared when the test finishes, leaving only the pass/fail
    summary.

    Args:
        script: Path to the test shell script (.sh or .bat).
        test_filter: Optional filter expression passed to the script via -f.
        timeout: Per-script timeout in seconds.

    Returns:
        Tuple of (passed, output). On success output is "passed"; on failure
        it contains the complete test output for full stack-trace visibility.

    """
    cmd = ["cmd.exe", "/c", str(script)] if script.suffix == ".bat" else ["bash", str(script)]
    if test_filter:
        cmd.extend(["-f", test_filter])

    is_tty = sys.stdout.isatty()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=BUILD_DIR,
    )

    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 120

    all_lines: list[str] = []
    window: collections.deque[str] = collections.deque(maxlen=_ROLLING_WINDOW_LINES)
    drawn_count = 0
    last_redraw_time = 0.0
    dirty = False
    lock = threading.Lock()

    def _redraw_locked() -> None:
        """Redraw the rolling window.  Caller must hold *lock*."""
        nonlocal drawn_count, last_redraw_time, dirty
        if drawn_count > 0:
            sys.stdout.write(f"\033[{drawn_count}A")
        for line in window:
            truncated = line[: term_width - 6]
            sys.stdout.write(f"\033[2K    {Colors.DIM}{truncated}{Colors.RESET}\n")
        drawn_count = len(window)
        sys.stdout.flush()
        last_redraw_time = time.monotonic()
        dirty = False

    def _clear_window() -> None:
        nonlocal drawn_count
        with lock:
            if drawn_count > 0:
                sys.stdout.write(f"\033[{drawn_count}A")
                for _ in range(drawn_count):
                    sys.stdout.write("\033[2K\n")
                sys.stdout.write(f"\033[{drawn_count}A")
                drawn_count = 0
                sys.stdout.flush()

    def _reader() -> None:
        nonlocal dirty
        assert proc.stdout is not None
        while True:
            raw_line = proc.stdout.readline()
            if not raw_line:
                break
            line = raw_line.rstrip("\n\r")
            with lock:
                all_lines.append(line)
                window.append(line)
                if is_tty:
                    now = time.monotonic()
                    if now - last_redraw_time >= _REDRAW_MIN_INTERVAL:
                        _redraw_locked()
                    else:
                        dirty = True

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        timed_out = True

    reader_thread.join(timeout=5)

    if is_tty:
        with lock:
            if dirty:
                _redraw_locked()
        _clear_window()

    if timed_out:
        full_output = "\n".join(all_lines) if all_lines else "(no output)"
        return False, f"timed out after {timeout}s\n{full_output}"

    if proc.returncode != 0:
        full_output = "\n".join(all_lines) if all_lines else "(no output)"
        return False, full_output

    return True, "passed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_discovery(
    discovery: dict[str, list[Path]],
    dep_reasons: dict[str, set[str]] | None = None,
) -> None:
    """Print the test-script discovery table for one tier.

    When dep_reasons is provided, each extension line is annotated with the
    Tier 1 extension(s) it directly depends on.

    Args:
        discovery: Map of extension name to list of test script paths.
        dep_reasons: Optional map of extension name to set of Tier 1 deps.

    """
    for name in sorted(discovery):
        scripts = discovery[name]
        reason = ""
        if dep_reasons and name in dep_reasons:
            deps = ", ".join(sorted(dep_reasons[name]))
            reason = f"  [depends on: {deps}]"
        if not scripts:
            log_info(f"  {name}: (none){reason}")
        else:
            log_info(f"  {name}: {len(scripts)} script(s){reason}")
            for s in scripts:
                log_info(f"    {s.name}")


def _write_test_result(
    log_fh: TextIO,
    script_name: str,
    passed: bool,
    detail: str,
) -> None:
    """Append one test result to the log file and flush immediately.

    Args:
        log_fh: Open log file handle.
        script_name: Name of the test script.
        passed: Whether the test passed.
        detail: Full output on failure, or "passed" on success.

    """
    status = "PASS" if passed else "FAIL"
    log_fh.write(f"{'=' * 72}\n")
    log_fh.write(f"{script_name} [{status}]\n")
    log_fh.write(f"{'=' * 72}\n")
    if not passed:
        log_fh.write(detail)
        log_fh.write("\n")
    log_fh.write("\n")
    log_fh.flush()


def _run_tier(
    discovery: dict[str, list[Path]],
    test_filter: str | None,
    timeout: int,
    log_fh: TextIO | None,
    failures: list[tuple[str, str]],
) -> int:
    """Execute all test scripts in discovery, returning the failure count.

    Failed test labels and their full output are appended to failures so the
    caller can print a consolidated summary after all tiers complete.

    Args:
        discovery: Map of extension name to list of test script paths.
        test_filter: Optional filter expression passed to test scripts.
        timeout: Per-script timeout in seconds.
        log_fh: Optional log file handle for incremental result writing.
        failures: List to append (label, detail) tuples for failed tests.

    Returns:
        Number of test scripts that failed.

    """
    errors = 0
    for name in sorted(discovery):
        scripts = discovery[name]
        if not scripts:
            continue
        for script in scripts:
            label = script.stem
            log_info(f"Running {script.name} ...")
            passed, detail = _run_test_script(script, test_filter=test_filter, timeout=timeout)
            if passed:
                log_pass(f"{label}: {detail}")
            else:
                for line in detail.splitlines():
                    print(f"    {line}", flush=True)
                log_fail(f"{label}: tests failed.")
                failures.append((label, detail))
                errors += 1
            if log_fh:
                _write_test_result(log_fh, script.name, passed, detail)
    return errors


def _extract_errors(output: str) -> str:
    """Extract only error/failure blocks from test output.

    Recognises unittest-style output (``======`` separator followed by
    ``FAIL:`` / ``ERROR:`` lines) and generic Python tracebacks.  Falls back
    to the last 50 lines when no pattern is matched.

    Args:
        output: Full test output string.

    Returns:
        Extracted error/failure portion of the output.

    """
    lines = output.splitlines()

    for i, line in enumerate(lines):
        if (
            line.startswith("=" * 20)
            and i + 1 < len(lines)
            and (lines[i + 1].startswith("FAIL:") or lines[i + 1].startswith("ERROR:"))
        ):
            return "\n".join(lines[i:])

    for i, line in enumerate(lines):
        if "Traceback (most recent call last):" in line:
            start = max(0, i - 2)
            return "\n".join(lines[start:])

    if len(lines) > 50:
        return "\n".join(lines[-50:])
    return output


def _print_failure_summary(
    failures: list[tuple[str, str]],
    log_fh: TextIO | None,
) -> None:
    """Print a consolidated failure report at the end of the run.

    Only the error/traceback portion of each failure is shown, not the
    full test output.

    Args:
        failures: List of (label, detail) tuples for failed tests.
        log_fh: Optional log file handle to write the summary.

    """
    separator = "=" * 72
    print(f"\n{separator}", flush=True)
    print(f"  FAILURE SUMMARY  ({len(failures)} failed)", flush=True)
    print(separator, flush=True)
    for label, detail in failures:
        errors = _extract_errors(detail)
        print(f"\n--- {label} ---", flush=True)
        for line in errors.splitlines():
            print(f"    {line}", flush=True)
    print(separator, flush=True)

    if log_fh:
        log_fh.write(f"\n{'#' * 72}\n# Failure summary ({len(failures)} failed)\n{'#' * 72}\n")
        for label, detail in failures:
            errors = _extract_errors(detail)
            log_fh.write(f"\n--- {label} ---\n")
            log_fh.write(errors)
            log_fh.write("\n")
        log_fh.flush()


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def run_tests(
    ext_names: list[str],
    *,
    include_downstream: bool = True,
    apps_changed: bool = False,
    test_filter: str | None = None,
    timeout: int = 600,
    log_path: Path | None = None,
    list_only: bool = False,
    only_extensions: list[str] | None = None,
) -> int:
    """Discover and run all tests related to the given extensions.

    Execution is split into two tiers:

    - **Tier 1 (direct):** tests for the extensions explicitly listed in
      ext_names.  These run first.
    - **Tier 2 (downstream):** tests for extensions that declare a direct
      dependency on any Tier 1 extension (no transitive walk — with adequate
      coverage, passing direct dependents implies upstream correctness).
      Only executed when every Tier 1 test passes.

    When log_path is set, results (including full output for failures) are
    written incrementally after each test finishes.

    Args:
        ext_names: Extension names or directory paths to test.
        include_downstream: Whether to include downstream dependent extensions.
        apps_changed: If True, add isaacsim.app.setup when source/apps/ changed.
        test_filter: Optional filter expression passed to test scripts.
        timeout: Per-script timeout in seconds.
        log_path: Optional path to write incremental results.
        list_only: If True, only list discovered tests without running.
        only_extensions: Optional whitelist of extension names to run.

    Returns:
        Total number of test scripts that failed.

    """
    if not BUILD_DIR.exists():
        log_warn(f"Build directory not found ({BUILD_DIR}). Build first, then re-run.")
        return 0

    if apps_changed and APP_SETUP_EXT not in ext_names:
        log_info(f"source/apps/ modified -- adding {APP_SETUP_EXT} tests.")
        ext_names.append(APP_SETUP_EXT)

    if not ext_names:
        log_info("No extensions to test.")
        return 0

    direct_names = list(dict.fromkeys(ext_names))
    downstream_names: list[str] = []
    downstream_reasons: dict[str, set[str]] = {}

    if include_downstream:
        reverse_deps = build_reverse_deps()
        for name in direct_names:
            for dep_name in reverse_deps.get(name, set()):
                if dep_name not in direct_names:
                    downstream_reasons.setdefault(dep_name, set()).add(name)
        downstream_names = sorted(downstream_reasons)
        if downstream_names:
            log_info(f"Including {len(downstream_names)} downstream dependent extension(s):")
            for dname in downstream_names:
                deps = ", ".join(sorted(downstream_reasons[dname]))
                log_info(f"  {dname}  [depends on: {deps}]")

    all_names = all_extension_names()

    # --- Discovery phase ---
    direct_discovery: dict[str, list[Path]] = {}
    for name in sorted(set(direct_names)):
        direct_discovery[name] = _find_all_test_scripts(name, all_names)

    downstream_discovery: dict[str, list[Path]] = {}
    for name in downstream_names:
        downstream_discovery[name] = _find_all_test_scripts(name, all_names)

    if only_extensions:
        only_set = set(only_extensions)
        dropped_direct = {n for n in direct_discovery if n not in only_set}
        dropped_downstream = {n for n in downstream_discovery if n not in only_set}
        for n in dropped_direct:
            del direct_discovery[n]
        for n in dropped_downstream:
            del downstream_discovery[n]
        total_dropped = len(dropped_direct) + len(dropped_downstream)
        if total_dropped:
            log_info(
                f"--only filter: kept {len(direct_discovery) + len(downstream_discovery)} "
                f"extension(s), dropped {total_dropped}."
            )

    total_direct = sum(len(s) for s in direct_discovery.values())
    total_downstream = sum(len(s) for s in downstream_discovery.values())

    if total_direct + total_downstream == 0:
        log_info("No test scripts found for the specified extensions.")
        return 0

    if total_direct:
        log_info(f"Tier 1 (direct): {total_direct} test script(s) across " f"{len(direct_discovery)} extension(s):")
        _print_discovery(direct_discovery)
    if total_downstream:
        log_info(
            f"Tier 2 (downstream): {total_downstream} test script(s) across "
            f"{len(downstream_discovery)} extension(s):"
        )
        _print_discovery(downstream_discovery, dep_reasons=downstream_reasons)

    if list_only:
        return 0

    # --- Open log file ---
    failures: list[tuple[str, str]] = []

    with contextlib.ExitStack() as stack:
        log_fh: TextIO | None = None
        if log_path:
            log_fh = stack.enter_context(open(log_path, "w"))  # noqa: SIM115
            log_info(f"Logging results to {log_path}")

        # --- Tier 1: Direct extension tests ---
        direct_errors = 0
        if total_direct:
            log_info("Tier 1: Running direct extension tests ...")
            if log_fh:
                log_fh.write(f"{'#' * 72}\n# Tier 1: Direct extension tests\n{'#' * 72}\n\n")
                log_fh.flush()

            direct_errors = _run_tier(direct_discovery, test_filter, timeout, log_fh, failures)

            if direct_errors:
                log_fail(f"Tier 1 finished with {direct_errors} failure(s). " "Skipping downstream tests.")
                if log_fh:
                    log_fh.write(f"\nTier 1 finished with {direct_errors} failure(s). " "Downstream tests skipped.\n")
                    log_fh.flush()
                _print_failure_summary(failures, log_fh)
                return direct_errors

            log_pass("Tier 1: All direct extension tests passed.")
            if log_fh:
                log_fh.write("\nTier 1: All direct extension tests passed.\n\n")
                log_fh.flush()

        # --- Tier 2: Downstream dependency tests ---
        downstream_errors = 0
        if total_downstream:
            log_info("Tier 2: Running downstream dependency tests ...")
            if log_fh:
                log_fh.write(f"{'#' * 72}\n# Tier 2: Downstream dependency tests\n{'#' * 72}\n\n")
                log_fh.flush()

            downstream_errors = _run_tier(downstream_discovery, test_filter, timeout, log_fh, failures)

        if failures:
            _print_failure_summary(failures, log_fh)

        return direct_errors + downstream_errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse CLI arguments and run extension tests.

    Returns:
        0 if all tests passed, 1 otherwise.

    """
    parser = argparse.ArgumentParser(
        description="Discover and run tests for Isaac Sim extensions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "extensions",
        nargs="+",
        help="Extension names (e.g. isaacsim.robot.poser) or directory paths.",
    )
    parser.add_argument(
        "--filter",
        "-f",
        default=None,
        dest="test_filter",
        help="Filter expression passed to test scripts via -f (supports wildcards).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-test-script timeout in seconds (default: 600).",
    )
    parser.add_argument(
        "--no-downstream",
        action="store_true",
        help="Do not include downstream dependent extensions.",
    )
    parser.add_argument(
        "--apps-changed",
        action="store_true",
        help="Include isaacsim.app.setup tests (set when source/apps/ files changed).",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        default=None,
        dest="only_extensions",
        help="Whitelist filter: only run tests for these extension names. "
        "Applied after all discovery (including downstream), dropping "
        "any extension not in this list. Useful for re-running only "
        "the extensions that failed in a previous run.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_only",
        help="List discovered test scripts without executing them.",
    )
    parser.add_argument(
        "--log",
        default=None,
        type=Path,
        dest="log_path",
        help="Path to a log file. Results (including full output for failures) "
        "are written incrementally as each test finishes.",
    )
    args = parser.parse_args()

    known_names = set(all_extension_names())
    ext_names: list[str] = []
    for arg in args.extensions:
        p = Path(arg)
        if p.is_dir():
            ext_names.append(p.resolve().name)
        else:
            ext_names.append(p.name if "/" in arg or "\\" in arg else arg)

    unknown = [n for n in ext_names if n not in known_names]
    if unknown:
        for n in unknown:
            log_warn(f"Unknown extension: {n}")
    ext_names = [n for n in ext_names if n in known_names]
    if not ext_names:
        print("No valid extensions provided.", flush=True)
        return 1

    errors = run_tests(
        ext_names,
        include_downstream=not args.no_downstream,
        apps_changed=args.apps_changed,
        test_filter=args.test_filter,
        timeout=args.timeout,
        log_path=args.log_path,
        list_only=args.list_only,
        only_extensions=args.only_extensions,
    )
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
