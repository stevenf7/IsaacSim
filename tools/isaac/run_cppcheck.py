#!/usr/bin/env python3
"""
cppcheck runner script for Isaac Sim source code.

This script provides a convenient wrapper around cppcheck with support for
compile_commands.json integration and various analysis modes.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


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
    cppcheck_bin: str = "cppcheck",
    simple_mode: bool = False,
    max_configs: int = 12,
    jobs: int = 1,
    fast_mode: bool = False,
) -> List[str]:
    """Build the cppcheck command with appropriate arguments.

    Args:
        source_dir: Directory to analyze.
        includes: Set of include paths to add.
        defines: Set of preprocessor defines to add.
        output_file: Optional output file for results.
        cppcheck_bin: Path to the cppcheck executable.
        simple_mode: Whether running in simple mode (affects suppressions).
        max_configs: Maximum number of preprocessor configurations to check.
        jobs: Number of parallel jobs to run.
        fast_mode: Enable fast mode with reduced checks.

    Returns:
        List of command arguments for subprocess execution.
    """
    cmd = [cppcheck_bin]

    # Add standard cppcheck options for thorough analysis
    if fast_mode:
        # Fast mode: reduced checks for speed
        standard_options = [
            "--enable=error,warning",  # Only error and warning, not style/performance/portability
            "--std=c++17",
            "--suppress=missingIncludeSystem",
            "--suppress=unusedFunction",
            "--suppress=noValidConfiguration",
            "--suppress=noConstructor",
            "--suppress=*:*_build*",
            "--suppress=invalidPointerCast:*isaacsim.ros2.bridge/library/backend/Ros2DynamicMessage.cpp",
            "--xml",
        ]
    else:
        # Full analysis mode
        standard_options = [
            "--enable=all",
            "--inconclusive",
            "--std=c++17",
            "--suppress=missingIncludeSystem",
            "--suppress=unusedFunction",
            "--suppress=noValidConfiguration",
            "--suppress=noConstructor",
            "--suppress=*:*_build*",
            "--suppress=invalidPointerCast:*isaacsim.ros2.bridge/library/backend/Ros2DynamicMessage.cpp",
            "--xml",
        ]

    # Add performance options

    # Add missingInclude suppression in simple mode
    if simple_mode:
        standard_options.append("--suppress=missingInclude")
        standard_options.append("--suppress=unmatchedSuppression")
        standard_options.append("--suppress=unknownMacro")
        standard_options.append("--force")
    else:
        standard_options.extend(
            [
                f"--max-configs={max_configs}",
                f"-j{jobs}",
            ]
        )

    cmd.extend(standard_options)

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


def run_cppcheck_per_file(
    compile_commands_path: str,
    cppcheck_bin: str,
    max_configs: int,
    jobs: int,
    fast_mode: bool,
    simple_mode: bool,
    timeout: int,
    output_file: Optional[str] = None,
    debug: bool = False,
) -> int:
    """Run cppcheck on each file individually using compile_commands.json.

    Args:
        compile_commands_path: Path to compile_commands.json.
        cppcheck_bin: Path to cppcheck executable.
        max_configs: Maximum preprocessor configurations per file.
        jobs: Number of parallel jobs (applied per file).
        fast_mode: Enable fast mode.
        simple_mode: Enable simple mode suppressions.
        timeout: Timeout per file in seconds.
        output_file: Optional output file.
        debug: Print debug information.

    Returns:
        Exit code (0 for success).
    """
    with open(compile_commands_path, "r") as f:
        compile_commands = json.load(f)

    # Filter to only C++ source files
    cpp_files = []
    for entry in compile_commands:
        file_path = entry.get("file", "")
        if any(file_path.endswith(ext) for ext in [".cpp", ".cc", ".cxx", ".c++"]):
            cpp_files.append(entry)

    print(f"Found {len(cpp_files)} C++ source files to analyze")

    failed_files = []
    timeout_files = []

    for i, entry in enumerate(cpp_files, 1):
        file_path = entry["file"]
        print(f"[{i}/{len(cpp_files)}] Analyzing {file_path}")

        # Build cppcheck command for this specific file
        cmd = [cppcheck_bin]

        # Add performance and analysis options
        if fast_mode:
            cmd.extend(["--enable=error,warning"])
        else:
            cmd.extend(["--enable=all", "--inconclusive"])

        cmd.extend(
            [
                "--std=c++17",
                f"--max-configs={max_configs}",
                f"-j{jobs}",
                "--suppress=missingIncludeSystem",
                "--suppress=unusedFunction",
                "--suppress=noValidConfiguration",
                "--suppress=noConstructor",
                "--suppress=*:*_build*",
                "--suppress=invalidPointerCast:*isaacsim.ros2.bridge/library/backend/Ros2DynamicMessage.cpp",
                "--force",
                "--xml",
            ]
        )

        if simple_mode:
            cmd.append("--suppress=missingInclude")
            cmd.append("--suppress=unknownMacro")
            cmd.append("--check-level=exhaustive")

        # Use project mode with file filter for this specific file
        cmd.extend([f"--project={compile_commands_path}", f"--file-filter={file_path}"])

        if debug:
            print(f"  Command: {' '.join(cmd)}")

        try:
            # Run with timeout
            result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)

            if result.returncode != 0:
                failed_files.append((file_path, result.returncode))
                if debug:
                    print(f"  Failed with return code {result.returncode}")
                    if result.stderr:
                        print(f"  Error: {result.stderr[:200]}...")

            # If output file specified, append results
            if output_file and result.stdout:
                with open(output_file, "a") as f:
                    f.write(result.stdout)

        except subprocess.TimeoutExpired:
            timeout_files.append(file_path)
            print(f"  TIMEOUT after {timeout} seconds")
        except Exception as e:
            failed_files.append((file_path, str(e)))
            print(f"  ERROR: {e}")

    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total files: {len(cpp_files)}")
    print(f"Failed files: {len(failed_files)}")
    print(f"Timeout files: {len(timeout_files)}")

    if failed_files:
        print("\nFailed files:")
        for file_path, error in failed_files[:10]:  # Show first 10
            print(f"  {file_path}: {error}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")

    if timeout_files:
        print("\nTimeout files:")
        for file_path in timeout_files[:10]:  # Show first 10
            print(f"  {file_path}")
        if len(timeout_files) > 10:
            print(f"  ... and {len(timeout_files) - 10} more")

    return 1 if (failed_files or timeout_files) else 0


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
  %(prog)s --fast --max-configs=5    # Fast mode with limited configurations
  %(prog)s --per-file -j4            # Per-file mode with 4 parallel jobs per file
  %(prog)s --per-file --timeout=60   # Per-file mode with 60s timeout per file
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

    parser.add_argument("--debug", action="store_true", help="Print the full cppcheck command before execution")

    parser.add_argument("--cppcheck", default="cppcheck", help="Path to the cppcheck binary")

    parser.add_argument(
        "--max-configs",
        type=int,
        default=12,
        help="Maximum number of preprocessor configurations to check per file (default: 12)",
    )

    parser.add_argument("--jobs", "-j", type=int, default=1, help="Number of parallel jobs (default: 1)")

    parser.add_argument("--timeout", type=int, default=300, help="Timeout per file in seconds (default: 300)")

    parser.add_argument("--fast", action="store_true", help="Enable fast mode (reduces checks for speed)")

    parser.add_argument(
        "--per-file", action="store_true", help="Run cppcheck on each file individually using compile_commands.json"
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

    # Check if we should use per-file mode
    if args.per_file and not args.simple:
        compile_commands_path = find_compile_commands()
        if compile_commands_path and os.path.exists(compile_commands_path):
            print(f"Using per-file mode with compile_commands.json: {compile_commands_path}")
            return run_cppcheck_per_file(
                compile_commands_path=compile_commands_path,
                cppcheck_bin=args.cppcheck,
                max_configs=args.max_configs,
                jobs=args.jobs,
                fast_mode=args.fast,
                simple_mode=args.simple,
                timeout=args.timeout,
                output_file=args.output_file,
                debug=args.debug,
            )
        else:
            print("Per-file mode requested but no compile_commands.json found, falling back to aggregate mode")

    # Build and execute cppcheck command
    cmd = build_cppcheck_command(
        source_dir=source_dir,
        includes=includes if includes else None,
        defines=defines if defines else None,
        output_file=args.output_file,
        cppcheck_bin=args.cppcheck,
        simple_mode=args.simple,
        max_configs=args.max_configs,
        jobs=args.jobs,
        fast_mode=args.fast,
    )

    if args.dry_run:
        print("Would execute:")
        print(" ".join(cmd))
        return

    print(f"Running cppcheck on {source_dir}...")
    print(f"Command: {' '.join(cmd)} ... ({len(cmd)} total arguments)")
    if args.debug:
        print(" ".join(cmd))

    try:
        # Add timeout for aggregate mode too
        timeout_seconds = args.timeout * 10  # Give more time for aggregate mode
        result = subprocess.run(cmd, check=False, timeout=timeout_seconds)
        if result.returncode == 0:
            print("cppcheck completed successfully")
        else:
            print(f"cppcheck completed with return code {result.returncode}")
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print(f"Error: cppcheck timed out after {timeout_seconds} seconds", file=sys.stderr)
        print("Try using --per-file mode or --fast mode for better performance", file=sys.stderr)
        sys.exit(124)
    except FileNotFoundError:
        print("Error: cppcheck not found. Please install cppcheck.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
