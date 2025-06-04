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
"""
Script to run clang-tidy on C++ source files.
"""

import argparse
import fnmatch
import glob
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def find_cpp_files(directory: str, exclude_patterns: List[str]) -> List[str]:
    """Find all C++ files in the given directory and its subdirectories, excluding specified patterns."""
    cpp_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".cpp", ".h")):
                file_path = os.path.join(root, file)
                # Check if file should be excluded using proper glob pattern matching
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
                    cpp_files.append(file_path)
    return cpp_files


def run_clang_tidy(
    file_path: str,
    compile_commands: str,
    config_file: str,
    extra_args: List[str],
    output_file: Optional[str] = None,
    fix: bool = False,
    verbose: bool = False,
) -> bool:
    """Run clang-tidy on a single file."""
    command = ["clang-tidy", "-p", compile_commands]
    command.extend(["--config-file", config_file])

    # Don't add color output if writing to a file
    if "--use-color" not in extra_args and not output_file:
        command.append("--use-color")

    # Add fix flag if requested
    if fix:
        command.append("-fix")

    command.extend(extra_args)
    command.append(file_path)

    # Always print the command, not just in verbose mode
    print(f"Running: {' '.join(command)}")

    try:
        if output_file:
            # Capture output and write to file
            result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # Append to output file
            with open(output_file, "a") as f:
                f.write(f"\n--- {file_path} ---\n")
                f.write(result.stdout)

            if result.returncode != 0:
                print(f"Error analyzing {file_path} (exit code {result.returncode})")
                return False
        else:
            # Don't capture output to allow color to pass through to terminal
            result = subprocess.run(command, check=False)

            if result.returncode != 0:
                print(f"Error analyzing {file_path} (exit code {result.returncode})")
                return False

        return True
    except Exception as e:
        print(f"Exception while analyzing {file_path}: {e}")
        return False


def run_clang_tidy_on_files(
    files: List[str],
    compile_commands: str,
    config_file: str,
    extra_args: List[str],
    output_file: Optional[str] = None,
    fix: bool = False,
    verbose: bool = False,
) -> int:
    """Run clang-tidy on all specified files using multiple processes."""
    print(f"Running clang-tidy on {len(files)} files...")

    # Clear output file if specified
    if output_file:
        with open(output_file, "w") as f:
            f.write(f"Clang-tidy results for {len(files)} files\n")

    success_count = 0
    num_processes = multiprocessing.cpu_count()

    for file_path in files:
        if run_clang_tidy(file_path, compile_commands, config_file, extra_args, output_file, fix, verbose):
            success_count += 1
            if verbose:
                print(f"Successfully analyzed: {file_path}")

    print(f"\nSummary: {success_count}/{len(files)} files analyzed successfully")

    if success_count < len(files):
        return 1
    return 0


def main():
    """Main function when run directly from command line."""
    parser = argparse.ArgumentParser(description="Run clang-tidy on C++ source files")
    parser.add_argument("source_dir", help="Directory containing source files to analyze")
    parser.add_argument("--config-file", default=".clang-tidy", help="Path to .clang-tidy config file")
    parser.add_argument(
        "--compile-commands",
        default="_build/linux-x86_64/release/compile_commands.json",
        help="Path to compile_commands.json",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=["*/isaac_ros2_messages/*", "*/isaacsim.robot.schema/*"],
        help="Patterns to exclude from analysis",
    )
    parser.add_argument("--extra-args", action="append", default=[], help="Extra arguments to pass to clang-tidy")
    parser.add_argument("--fix", action="store_true", help="Apply fixes for fixable issues")
    parser.add_argument("--verbose", action="store_true", help="Print detailed information during execution")
    parser.add_argument("--output-file", help="Write clang-tidy output to a file (without color formatting)")
    args = parser.parse_args()

    if not os.path.isdir(args.source_dir):
        print(f"Error: Directory '{args.source_dir}' does not exist")
        sys.exit(1)

    if not os.path.isfile(args.config_file):
        print(f"Error: .clang-tidy config file not found at '{args.config_file}'")
        sys.exit(1)

    if not os.path.isfile(args.compile_commands):
        print(f"Error: compile_commands.json not found at '{args.compile_commands}'")
        print("       Make sure to generate it first with:")
        print("       cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..")
        sys.exit(1)

    # Use default extra args if none specified
    if not args.extra_args:
        args.extra_args = ["--extra-arg=-std=c++17", "--extra-arg=-Wno-error", "--quiet", "--warnings-as-errors=-*"]

    # Find all C++ files
    cpp_files = find_cpp_files(args.source_dir, args.exclude)

    # Run clang-tidy on found files
    exit_code = run_clang_tidy_on_files(
        cpp_files, args.compile_commands, args.config_file, args.extra_args, args.output_file, args.fix, args.verbose
    )
    sys.exit(exit_code)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> callable:
    """Set up the repo tool for running clang-tidy."""
    # Get the root directory from the config
    root_dir = config.get("root", os.getcwd())

    # Add command line arguments
    parser.add_argument("source_dir", help="Directory containing source files to analyze")
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

    def run_tool(args, config=config):
        """Run the clang-tidy tool with the given arguments."""
        # Get clang-tidy config from repo.toml
        clang_tidy_config = config.get("repo_clang_tidy", {})

        # Get platform
        from omni.repo.man import get_and_validate_host_platform

        platform = get_and_validate_host_platform(["windows-x86_64", "linux-x86_64"])

        # Replace template variables in paths
        config_file = clang_tidy_config.get("config_file", os.path.join(root_dir, ".clang-tidy"))
        config_file = config_file.replace("${root}", root_dir)

        compile_commands = clang_tidy_config.get(
            "compile_commands", os.path.join(root_dir, "_build/linux-x86_64/release/compile_commands.json")
        )
        compile_commands = compile_commands.replace("${root}", root_dir)
        compile_commands = compile_commands.replace("${platform}", platform)
        compile_commands = compile_commands.replace("${config}", args.config)

        # Get exclude paths and extra args
        exclude_paths = clang_tidy_config.get("exclude_paths", ["*/isaac_ros2_messages/*", "*/isaacsim.robot.schema/*"])

        extra_args = clang_tidy_config.get(
            "extra_args", ["--extra-arg=-std=c++17", "--extra-arg=-Wno-error", "--quiet", "--warnings-as-errors=-*"]
        )

        # Print configuration information
        print(f"Running clang-tidy with the following configuration:")
        print(f"  Source directory: {args.source_dir}")
        print(f"  Config file: {config_file}")
        print(f"  Compile commands: {compile_commands}")
        print(f"  Excluded paths: {exclude_paths}")
        print(f"  Extra arguments: {extra_args}")
        print(f"  Apply fixes: {args.fix}")
        if args.output_file:
            print(f"  Output file: {args.output_file}")
        print("")

        if not os.path.isdir(args.source_dir):
            print(f"Error: Directory '{args.source_dir}' does not exist")
            return 1

        if not os.path.isfile(config_file):
            print(f"Error: .clang-tidy config file not found at '{config_file}'")
            return 1

        if not os.path.isfile(compile_commands):
            print(f"Error: compile_commands.json not found at '{compile_commands}'")
            print("       Make sure to generate it first with:")
            print("       cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..")
            return 1

        # Find all C++ files
        cpp_files = find_cpp_files(args.source_dir, exclude_paths)

        if not cpp_files:
            print(f"No C++ files found in {args.source_dir} (after applying exclusions)")
            return 0

        # Run clang-tidy on found files
        return run_clang_tidy_on_files(
            cpp_files, compile_commands, config_file, extra_args, args.output_file, args.fix, args.verbose
        )

    return run_tool


if __name__ == "__main__":
    main()
