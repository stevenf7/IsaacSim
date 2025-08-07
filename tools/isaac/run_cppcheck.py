#!/usr/bin/env python3
"""
cppcheck runner script for Isaac Sim source code.

This script provides a convenient wrapper around cppcheck with support for
compile_commands.json integration and various analysis modes.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set


def parse_compile_commands(compile_commands_path: str) -> tuple[Set[str], Set[str]]:
    """Parse compile_commands.json to extract include paths and defines.

    Args:
        compile_commands_path: Path to the compile_commands.json file.

    Returns:
        A tuple containing sets of include paths and preprocessor defines.

    Raises:
        FileNotFoundError: If the compile_commands.json file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    includes = set()
    defines = set()

    with open(compile_commands_path, "r") as f:
        commands = json.load(f)

    for entry in commands:
        command = entry.get("command", "")
        directory = entry.get("directory", "")

        # Split command into arguments, handling quotes
        import shlex

        args = shlex.split(command)

        for i, arg in enumerate(args):
            if arg.startswith("-I"):
                include_path = None
                if len(arg) > 2:
                    # -Ipath format
                    include_path = arg[2:]
                elif i + 1 < len(args):
                    # -I path format
                    include_path = args[i + 1]

                if include_path:
                    # Resolve relative paths based on the compilation directory
                    if not os.path.isabs(include_path):
                        include_path = os.path.normpath(os.path.join(directory, include_path))
                    includes.add(include_path)

            elif arg.startswith("-isystem"):
                include_path = None
                if len(arg) > 8:
                    # -isystempath format
                    include_path = arg[8:]
                elif i + 1 < len(args):
                    # -isystem path format
                    include_path = args[i + 1]

                if include_path:
                    # Resolve relative paths based on the compilation directory
                    if not os.path.isabs(include_path):
                        include_path = os.path.normpath(os.path.join(directory, include_path))
                    includes.add(include_path)

            elif arg.startswith("-D"):
                if len(arg) > 2:
                    # -DDEFINE format
                    defines.add(arg[2:])
                elif i + 1 < len(args):
                    # -D DEFINE format
                    defines.add(args[i + 1])

    return includes, defines


def build_cppcheck_command(
    source_dir: str,
    includes: Optional[Set[str]] = None,
    defines: Optional[Set[str]] = None,
    output_file: Optional[str] = None,
    simple_mode: bool = False,
) -> List[str]:
    """Build the cppcheck command with appropriate arguments.

    Args:
        source_dir: Directory to analyze.
        includes: Set of include paths to add.
        defines: Set of preprocessor defines to add.
        output_file: Optional output file for results.
        simple_mode: If True, run with minimal configuration.

    Returns:
        List of command arguments for subprocess execution.
    """
    cmd = ["cppcheck"]

    # Add standard cppcheck options for thorough analysis
    cmd.extend(
        [
            "--enable=all",
            "--inconclusive",
            "--std=c++17",
            "--suppress=missingIncludeSystem",
            "--suppress=unusedFunction",
            "--suppress=noValidConfiguration",
            "--suppress=preprocessorErrorDirective",
            "--suppress=noConstructor",
            "--suppress=*:*_build*",
            "--suppress=invalidPointerCast:*isaacsim.ros2.bridge/library/backend/Ros2DynamicMessage.cpp",
            "--force",
            "--xml",
        ]
    )

    # Add include paths (already resolved to absolute paths)
    if includes:
        for include in includes:
            cmd.extend(["-I", include])

    # Add preprocessor defines
    if defines:
        for define in defines:
            cmd.extend(["-D", define])

    # Add output file option
    if output_file:
        cmd.extend(["--output-file=" + output_file])

    # Add file filter to only check files in the source directory
    # This prevents checking files in _build, external dependencies, etc.
    cmd.extend(["--file-filter=" + source_dir + "/*"])

    # Add source directory
    cmd.append(source_dir)

    return cmd


def find_compile_commands() -> Optional[str]:
    """Find compile_commands.json in common build directories.

    Returns:
        Path to compile_commands.json if found, None otherwise.
    """
    # Get workspace root (3 levels up from this script)
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    possible_paths = [
        os.path.join(workspace_root, "_build/linux-x86_64/release/compile_commands.json"),
        os.path.join(workspace_root, "_build/compile_commands.json"),
        os.path.join(workspace_root, "build/compile_commands.json"),
        os.path.join(workspace_root, "compile_commands.json"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def main():
    """Main entry point for the cppcheck runner script.

    Parses command line arguments and executes cppcheck with the appropriate
    configuration based on available compile_commands.json and user options.
    """
    parser = argparse.ArgumentParser(
        description="Run cppcheck on Isaac Sim source code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run with compile_commands.json if available
  %(prog)s --simple                  # Run in simple mode (no compile_commands.json)
  %(prog)s --output report.txt       # Save results to file
        """,
    )

    parser.add_argument("--source-dir", default="source", help="Source directory to analyze (default: source)")

    parser.add_argument("--output", "-o", dest="output_file", help="Output file for cppcheck results")

    parser.add_argument(
        "--simple", action="store_true", help="Run in simple mode (basic error checking only, no compile_commands.json)"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Print the command that would be executed without running it"
    )

    args = parser.parse_args()

    # Get workspace root for relative paths
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Resolve source directory path
    if not os.path.isabs(args.source_dir):
        source_dir = os.path.join(workspace_root, args.source_dir)
    else:
        source_dir = args.source_dir

    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    includes = set()
    defines = set()

    # Handle compile_commands.json
    if args.simple:
        print("Simple mode: skipping compile_commands.json")
    else:
        compile_commands_path = find_compile_commands()

        if compile_commands_path:
            if os.path.exists(compile_commands_path):
                print(f"Using compile_commands.json: {compile_commands_path}")
                try:
                    includes, defines = parse_compile_commands(compile_commands_path)
                    print(f"Extracted {len(includes)} include paths and {len(defines)} defines")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Failed to parse compile_commands.json: {e}", file=sys.stderr)
                    print("Continuing without compile database information...")
            else:
                print(f"Warning: compile_commands.json not found at {compile_commands_path}", file=sys.stderr)
        else:
            print("No compile_commands.json found, running without compile database")

    # Build and execute cppcheck command
    cmd = build_cppcheck_command(
        source_dir=source_dir,
        includes=includes if includes else None,
        defines=defines if defines else None,
        output_file=args.output_file,
        simple_mode=args.simple,
    )

    if args.dry_run:
        print("Would execute:")
        print(" ".join(cmd))
        return

    print(f"Running cppcheck on {source_dir}...")
    print(f"Command: {' '.join(cmd[:3])} ... ({len(cmd)} total arguments)")

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("cppcheck completed successfully")
        else:
            print(f"cppcheck completed with return code {result.returncode}")
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: cppcheck not found. Please install cppcheck.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
