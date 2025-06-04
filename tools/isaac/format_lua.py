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
Script to recursively find and format all Lua files in a directory using Stylua.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict


def find_lua_files(directory):
    """Find all Lua files in the given directory and its subdirectories."""
    lua_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".lua"):
                lua_files.append(os.path.join(root, file))
    return lua_files


def format_lua_file(file_path, stylua_path, config_path=None, check_only=False, verbose=False):
    """Format a single Lua file using Stylua."""
    command = [stylua_path]

    if check_only:
        command.append("--check")

    if config_path:
        command.extend(["--config-path", config_path])

    command.append(file_path)

    # Print the command being executed if verbose
    if verbose:
        print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"The following changes would be made to {file_path}:")
            print(result.stdout)
            return False
        return True
    except Exception as e:
        print(f"Exception while formatting {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Format Lua files using Stylua")
    parser.add_argument("directory", help="Directory containing Lua files to format")
    parser.add_argument("--stylua", default="stylua", help="Path to stylua executable")
    parser.add_argument("--config", help="Path to stylua config file")
    parser.add_argument("--check", action="store_true", help="Check formatting without modifying files")
    args = parser.parse_args()

    # Verify the directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    # Verify stylua is available
    try:
        subprocess.run([args.stylua, "--version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print(f"Error: Stylua not found at '{args.stylua}'")
        print("Make sure stylua is installed and in your PATH, or specify the path with --stylua")
        sys.exit(1)

    # Find all Lua files
    lua_files = find_lua_files(args.directory)
    print(f"Found {len(lua_files)} Lua files to process")

    # Format each file
    success_count = 0
    for file_path in lua_files:
        if format_lua_file(file_path, args.stylua, args.config, args.check):
            success_count += 1
            print(f"Successfully {'checked' if args.check else 'formatted'}: {file_path}")

    # Print summary
    print(f"\nSummary: {success_count}/{len(lua_files)} files {'checked' if args.check else 'formatted'} successfully")

    if success_count < len(lua_files):
        sys.exit(1)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict):
    """Set up the repo tool for formatting Lua files."""
    # Get the root directory from the config
    root_dir = config.get("root", os.getcwd())

    parser.add_argument(
        "--directory", default=root_dir, help="Directory containing Lua files to format (default: repo root)"
    )
    parser.add_argument(
        "--stylua",
        default=config.get("repo_format_lua", {}).get("stylua_path", "stylua"),
        help="Path to stylua executable",
    )
    parser.add_argument(
        "--config",
        default=config.get("repo_format_lua", {}).get("config_path", None),
        help="Path to stylua config file",
    )
    parser.add_argument("--check", action="store_true", help="Check formatting without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed information during execution")

    def run_tool(args, config=config):
        """Run the Lua formatting tool with the given arguments."""
        # Get exclude directories from config
        exclude_dirs = config.get("repo_format_lua", {}).get("exclude_dirs", [])

        # Verify the directory exists
        if not os.path.isdir(args.directory):
            print(f"Error: Directory '{args.directory}' does not exist")
            return 1

        # Verify stylua is available
        try:
            subprocess.run([args.stylua, "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"Error: Stylua not found at '{args.stylua}'")
            print("Make sure stylua is installed and in your PATH, or specify the path with --stylua")
            return 1

        # Find all Lua files, excluding specified directories
        lua_files = []
        for root, dirs, files in os.walk(args.directory):
            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(
                    os.path.join(root, d).startswith(os.path.join(args.directory, excl)) for excl in exclude_dirs
                )
            ]

            for file in files:
                if file.endswith(".lua"):
                    lua_files.append(os.path.join(root, file))

        print(f"Found {len(lua_files)} Lua files to process")

        # Format each file
        success_count = 0
        for file_path in lua_files:
            if format_lua_file(file_path, args.stylua, args.config, args.check, args.verbose):
                success_count += 1
                if args.verbose:
                    print(f"Successfully {'checked' if args.check else 'formatted'}: {file_path}")

        # Print summary
        print(
            f"\nSummary: {success_count}/{len(lua_files)} files {'checked' if args.check else 'formatted'} successfully"
        )

        if success_count < len(lua_files):
            return 1

        return 0

    return run_tool


if __name__ == "__main__":
    main()
