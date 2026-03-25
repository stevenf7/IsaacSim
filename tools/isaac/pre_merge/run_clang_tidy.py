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
"""Run clang-tidy on C++ source files.

Can be used standalone (``python clang_tidy.py source/extensions ...``) or
imported by :mod:`pre_merge_validate` to check only the extensions that
were modified in a branch.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def find_cpp_files(directory: str, exclude_patterns: list[str]) -> list[str]:
    """Find all C++ files in the given directory and its subdirectories, excluding specified patterns."""
    cpp_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".cpp", ".h", ".hpp")):
                file_path = os.path.join(root, file)
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
                    cpp_files.append(file_path)
    return sorted(cpp_files)


def files_from_compile_commands(
    compile_commands_path: str,
    source_dirs: list[str],
    exclude_patterns: list[str],
) -> list[str]:
    """Extract source files from compile_commands.json, filtered by source directories and exclude patterns."""
    with open(compile_commands_path) as f:
        entries = json.load(f)

    abs_dirs = [os.path.abspath(d) for d in source_dirs]
    seen: set[str] = set()
    cpp_files: list[str] = []
    for entry in entries:
        file_path = entry.get("file", "")
        if not file_path:
            continue
        abs_path = os.path.abspath(file_path)
        # Only include files under one of the requested source directories
        if not any(abs_path.startswith(d + os.sep) or abs_path == d for d in abs_dirs):
            continue
        if abs_path in seen:
            continue
        seen.add(abs_path)
        if any(fnmatch.fnmatch(abs_path, pattern) for pattern in exclude_patterns):
            continue
        cpp_files.append(abs_path)

    return sorted(cpp_files)


# ---------------------------------------------------------------------------
# Upstream error detection
# ---------------------------------------------------------------------------


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _has_only_upstream_errors(output: str, source_dirs: list[str]) -> bool:
    """Check if all errors in the output come from upstream/external headers (not our source code)."""
    # Strip ANSI escape codes before parsing (clang-tidy --use-color adds them)
    clean = _ANSI_RE.sub("", output)
    error_lines = re.findall(r"^(.*?):\d+:\d+: error:", clean, re.MULTILINE)
    if not error_lines:
        return False
    for path in error_lines:
        path = path.strip()
        if any(d in path for d in source_dirs if d):
            return False
    return True


# ---------------------------------------------------------------------------
# Single-file runner
# ---------------------------------------------------------------------------


def run_clang_tidy(
    file_path: str,
    compile_commands: str,
    config_file: str,
    extra_args: list[str],
    output_file: Optional[str] = None,
    fix: bool = False,
    verbose: bool = False,
    header_filter: Optional[str] = None,
    source_dirs: Optional[list[str]] = None,
) -> bool:
    """Run clang-tidy on a single file."""
    if source_dirs is None:
        source_dirs = ["source/"]

    command = ["clang-tidy", "-p", compile_commands]
    command.extend(["--config-file", config_file])

    if header_filter:
        command.extend(["--header-filter", header_filter])

    # Don't add color output if writing to a file
    if "--use-color" not in extra_args and not output_file:
        command.append("--use-color")

    if fix:
        command.append("-fix")

    command.extend(extra_args)
    command.append(file_path)

    if verbose:
        print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        if result.returncode != 0:
            if _has_only_upstream_errors(result.stdout, source_dirs):
                if verbose:
                    print(f"Ignoring upstream compile errors for {file_path}")
                return True
            # Real errors — now print the output
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"\n--- {file_path} ---\n")
                    f.write(result.stdout)
            elif result.stdout.strip():
                print(result.stdout, end="")
            print(f"Error analyzing {file_path} (exit code {result.returncode})")
            return False

        # Success — print any warnings
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"\n--- {file_path} ---\n")
                f.write(result.stdout)
        elif result.stdout.strip():
            print(result.stdout, end="")

        return True
    except Exception as e:
        print(f"Exception while analyzing {file_path}: {e}")
        return False


def _run_single_file(
    file_path, compile_commands, config_file, extra_args, output_file, fix, verbose, header_filter, source_dirs
):
    """Wrapper for parallel execution of run_clang_tidy."""
    success = run_clang_tidy(
        file_path, compile_commands, config_file, extra_args, output_file, fix, verbose, header_filter, source_dirs
    )
    return (file_path, success)


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------


def run_clang_tidy_on_files(
    files: list[str],
    compile_commands: str,
    config_file: str,
    extra_args: list[str],
    output_file: Optional[str] = None,
    fix: bool = False,
    verbose: bool = False,
    header_filter: Optional[str] = None,
    jobs: int = 0,
    source_dirs: Optional[list[str]] = None,
) -> int:
    """Run clang-tidy on all specified files using multiple processes.

    Returns:
        0 if all files analyzed successfully, 1 otherwise.
    """
    if source_dirs is None:
        source_dirs = ["source/"]
    if jobs <= 0:
        jobs = multiprocessing.cpu_count()

    print(f"Running clang-tidy on {len(files)} files using {jobs} parallel jobs...")

    if output_file:
        with open(output_file, "w") as f:
            f.write(f"Clang-tidy results for {len(files)} files\n")

    success_count = 0

    if jobs == 1 or fix:
        for file_path in files:
            if run_clang_tidy(
                file_path,
                compile_commands,
                config_file,
                extra_args,
                output_file,
                fix,
                verbose,
                header_filter,
                source_dirs,
            ):
                success_count += 1
                if verbose:
                    print(f"Successfully analyzed: {file_path}")
    else:
        worker = partial(
            _run_single_file,
            compile_commands=compile_commands,
            config_file=config_file,
            extra_args=extra_args,
            output_file=output_file,
            fix=fix,
            verbose=verbose,
            header_filter=header_filter,
            source_dirs=source_dirs,
        )
        with multiprocessing.Pool(processes=jobs) as pool:
            for file_path, success in pool.imap_unordered(worker, files):
                if success:
                    success_count += 1
                    if verbose:
                        print(f"Successfully analyzed: {file_path}")

    print(f"\nSummary: {success_count}/{len(files)} files analyzed successfully")

    if success_count < len(files):
        return 1
    return 0


# ---------------------------------------------------------------------------
# Pre-merge integration — called from pre_merge_validate.py
# ---------------------------------------------------------------------------


def check_extensions(
    extensions: list[Path],
    repo_root: Path,
    fix: bool = False,
    jobs: int = 0,
) -> int:
    """Run clang-tidy on C++ files belonging to the given extensions.

    Finds files via compile_commands.json, filtering to only those under
    the given extension directories.  All files are run in a single process
    pool for maximum parallelism, then results are reported per-extension.

    Args:
        extensions: Extension directory paths (absolute).
        repo_root: Repository root path.
        fix: Whether to apply clang-tidy auto-fixes.
        jobs: Number of parallel jobs (0 = cpu_count).

    Returns:
        Number of extensions with clang-tidy issues (0 = all clean).
    """
    if not shutil.which("clang-tidy"):
        print("clang-tidy not found in PATH; skipping C++ lint check.")
        return 0

    config_file = str(repo_root / ".clang-tidy")
    compile_commands = str(repo_root / "_build" / "linux-x86_64" / "release" / "compile_commands.json")
    exclude_patterns = ["*/isaacsim.robot.schema/*"]
    extra_args = ["--extra-arg=-std=c++17", "--extra-arg=-Wno-error", "--quiet", "--warnings-as-errors=-*"]

    if not os.path.isfile(config_file):
        print(f".clang-tidy config not found at {config_file}; skipping.")
        return 0

    if not os.path.isfile(compile_commands):
        print(f"compile_commands.json not found at {compile_commands}.")
        print("Build the project first (./build.sh --no-docker) to generate it.")
        return 0

    # Collect files per-extension from compile_commands.json
    source_dirs = [str(ext) for ext in extensions]
    cpp_files = files_from_compile_commands(compile_commands, source_dirs, exclude_patterns)

    if not cpp_files:
        print("No C++ files found in modified extensions.")
        return 0

    # Map files back to extensions for per-extension reporting
    ext_files: dict[str, list[str]] = {}
    file_to_ext: dict[str, str] = {}
    for f in cpp_files:
        for ext in extensions:
            if f.startswith(str(ext) + os.sep):
                ext_files.setdefault(ext.name, []).append(f)
                file_to_ext[f] = ext.name
                break

    for ext_name, ext_cpp_files in sorted(ext_files.items()):
        print(f"\n  {ext_name}: {len(ext_cpp_files)} C++ files")

    # Run all files in a single pool for maximum parallelism
    if jobs <= 0:
        jobs = multiprocessing.cpu_count()

    print(f"\nRunning clang-tidy on {len(cpp_files)} files using {jobs} parallel jobs...")

    failed_files: set[str] = set()

    if jobs == 1 or fix:
        for file_path in cpp_files:
            if not run_clang_tidy(
                file_path,
                compile_commands,
                config_file,
                extra_args,
                fix=fix,
                source_dirs=source_dirs,
            ):
                failed_files.add(file_path)
    else:
        worker = partial(
            _run_single_file,
            compile_commands=compile_commands,
            config_file=config_file,
            extra_args=extra_args,
            output_file=None,
            fix=fix,
            verbose=False,
            header_filter=None,
            source_dirs=source_dirs,
        )
        with multiprocessing.Pool(processes=jobs) as pool:
            for file_path, success in pool.imap_unordered(worker, cpp_files):
                if not success:
                    failed_files.add(file_path)

    # Report per-extension results
    errors = 0
    for ext_name, ext_cpp_files in sorted(ext_files.items()):
        ext_failed = [f for f in ext_cpp_files if f in failed_files]
        success_count = len(ext_cpp_files) - len(ext_failed)
        print(f"\n  {ext_name}: {success_count}/{len(ext_cpp_files)} files analyzed successfully")
        if ext_failed:
            errors += 1

    print(f"\nSummary: {len(cpp_files) - len(failed_files)}/{len(cpp_files)} files analyzed successfully")

    return errors


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------


def main():
    """Main function when run directly from command line."""
    parser = argparse.ArgumentParser(description="Run clang-tidy on C++ source files")
    parser.add_argument("source_dirs", nargs="+", help="Directories containing source files to analyze")
    parser.add_argument("--config-file", default=".clang-tidy", help="Path to .clang-tidy config file")
    parser.add_argument(
        "--compile-commands",
        default="_build/linux-x86_64/release/compile_commands.json",
        help="Path to compile_commands.json",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=["*/isaacsim.robot.schema/*"],
        help="Patterns to exclude from analysis",
    )
    parser.add_argument("--extra-args", action="append", default=[], help="Extra arguments to pass to clang-tidy")
    parser.add_argument("--fix", action="store_true", help="Apply fixes for fixable issues")
    parser.add_argument("--verbose", action="store_true", help="Print detailed information during execution")
    parser.add_argument("--output-file", help="Write clang-tidy output to a file (without color formatting)")
    parser.add_argument(
        "--header-filter",
        default=None,
        help="Regex to filter headers for warnings (default: use HeaderFilterRegex from .clang-tidy config)",
    )
    parser.add_argument(
        "--use-compile-commands",
        action="store_true",
        help="Extract file list from compile_commands.json instead of walking the source directory",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=0,
        help="Number of parallel jobs (default: number of CPU cores, use 1 for sequential)",
    )
    args = parser.parse_args()

    for d in args.source_dirs:
        if not os.path.isdir(d):
            print(f"Error: Directory '{d}' does not exist")
            sys.exit(1)

    if not os.path.isfile(args.config_file):
        print(f"Error: .clang-tidy config file not found at '{args.config_file}'")
        sys.exit(1)

    if not os.path.isfile(args.compile_commands):
        print(f"Error: compile_commands.json not found at '{args.compile_commands}'")
        print("       Build the project first to generate it.")
        sys.exit(1)

    if not args.extra_args:
        args.extra_args = ["--extra-arg=-std=c++17", "--extra-arg=-Wno-error", "--quiet", "--warnings-as-errors=-*"]

    if args.use_compile_commands:
        cpp_files = files_from_compile_commands(args.compile_commands, args.source_dirs, args.exclude)
    else:
        cpp_files = []
        for d in args.source_dirs:
            cpp_files.extend(find_cpp_files(d, args.exclude))
        cpp_files.sort()

    if not cpp_files:
        print(f"No C++ files found in {args.source_dirs} (after applying exclusions)")
        print("Hint: try --use-compile-commands to extract files from compile_commands.json")
        sys.exit(0)

    exit_code = run_clang_tidy_on_files(
        cpp_files,
        args.compile_commands,
        args.config_file,
        args.extra_args,
        args.output_file,
        args.fix,
        args.verbose,
        args.header_filter,
        args.jobs,
        args.source_dirs,
    )
    sys.exit(exit_code)


def setup_repo_tool(parser: argparse.ArgumentParser, config: dict) -> callable:
    """Set up the repo tool for running clang-tidy."""
    root_dir = config.get("root", os.getcwd())

    parser.add_argument("source_dirs", nargs="+", help="Directories containing source files to analyze")
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="release",
        help="Build configuration to use. (default: %(default)s)",
    )
    parser.add_argument("--fix", action="store_true", help="Apply fixes for fixable issues")
    parser.add_argument("--verbose", action="store_true", help="Print detailed information during execution")
    parser.add_argument("--output-file", help="Write clang-tidy output to a file (without color formatting)")
    parser.add_argument(
        "--header-filter",
        default=None,
        help="Regex to filter headers for warnings (default from config or '.*/source/.*')",
    )
    parser.add_argument(
        "--use-compile-commands",
        action="store_true",
        help="Extract file list from compile_commands.json instead of walking the source directory",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=0,
        help="Number of parallel jobs (default: number of CPU cores, use 1 for sequential)",
    )

    def run_tool(args, config=config):
        """Run the clang-tidy tool with the given arguments."""
        clang_tidy_config = config.get("repo_clang_tidy", {})

        from omni.repo.man import get_and_validate_host_platform

        platform = get_and_validate_host_platform(["windows-x86_64", "linux-x86_64"])

        config_file = clang_tidy_config.get("config_file", os.path.join(root_dir, ".clang-tidy"))
        config_file = config_file.replace("${root}", root_dir)

        compile_commands = clang_tidy_config.get(
            "compile_commands", os.path.join(root_dir, "_build/linux-x86_64/release/compile_commands.json")
        )
        compile_commands = compile_commands.replace("${root}", root_dir)
        compile_commands = compile_commands.replace("${platform}", platform)
        compile_commands = compile_commands.replace("${config}", args.config)

        exclude_paths = clang_tidy_config.get("exclude_paths", ["*/isaacsim.robot.schema/*"])
        extra_args = clang_tidy_config.get(
            "extra_args", ["--extra-arg=-std=c++17", "--extra-arg=-Wno-error", "--quiet", "--warnings-as-errors=-*"]
        )
        header_filter = args.header_filter or clang_tidy_config.get("header_filter", None)

        print("Running clang-tidy with the following configuration:")
        print(f"  Source directories: {args.source_dirs}")
        print(f"  Config file: {config_file}")
        print(f"  Compile commands: {compile_commands}")
        print(f"  Excluded paths: {exclude_paths}")
        print(f"  Extra arguments: {extra_args}")
        print(f"  Header filter: {header_filter}")
        print(f"  Apply fixes: {args.fix}")
        if args.output_file:
            print(f"  Output file: {args.output_file}")
        print("")

        for d in args.source_dirs:
            if not os.path.isdir(d):
                print(f"Error: Directory '{d}' does not exist")
                return 1

        if not os.path.isfile(config_file):
            print(f"Error: .clang-tidy config file not found at '{config_file}'")
            return 1

        if not os.path.isfile(compile_commands):
            print(f"Error: compile_commands.json not found at '{compile_commands}'")
            print("       Build the project first to generate it.")
            return 1

        if args.use_compile_commands:
            cpp_files = files_from_compile_commands(compile_commands, args.source_dirs, exclude_paths)
        else:
            cpp_files = []
            for d in args.source_dirs:
                cpp_files.extend(find_cpp_files(d, exclude_paths))
            cpp_files.sort()

        if not cpp_files:
            print(f"No C++ files found in {args.source_dirs} (after applying exclusions)")
            print("Hint: try --use-compile-commands to extract files from compile_commands.json")
            return 0

        return run_clang_tidy_on_files(
            cpp_files,
            compile_commands,
            config_file,
            extra_args,
            args.output_file,
            args.fix,
            args.verbose,
            header_filter,
            args.jobs,
            args.source_dirs,
        )

    return run_tool


if __name__ == "__main__":
    main()
