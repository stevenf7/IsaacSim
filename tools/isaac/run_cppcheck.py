#!/usr/bin/env python3
"""
cppcheck runner script for Isaac Sim source code.

This script provides a convenient wrapper around cppcheck for simple static
analysis of C++ source code.
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional


def build_cppcheck_command(
    source_dir: str,
    output_file: Optional[str] = None,
    cppcheck_bin: str = "cppcheck",
) -> List[str]:
    """Build the cppcheck command with appropriate arguments.

    Args:
        source_dir: Directory to analyze.
        output_file: Optional output file for results.
        cppcheck_bin: Path to the cppcheck executable.

    Returns:
        List of command arguments for subprocess execution.
    """
    cmd = [cppcheck_bin]

    # Add standard cppcheck options for simple mode analysis
    standard_options = [
        "--enable=all",
        "--std=c++17",
        "--suppress=missingIncludeSystem",
        "--suppress=unusedFunction",
        "--suppress=unusedStructMember",
        "--suppress=noValidConfiguration",
        "--suppress=noConstructor",
        "--suppress=*:*_build*",
        "--suppress=invalidPointerCast:*isaacsim.ros2.bridge/library/backend/Ros2DynamicMessage.cpp",
        "--suppress=missingInclude",
        "--suppress=unmatchedSuppression",
        "--suppress=unknownMacro",
        "--check-level=exhaustive",
        "--force",
        "--xml",
    ]

    cmd.extend(standard_options)

    # Add output file option
    if output_file:
        cmd.extend(["--output-file=" + output_file])

    # Add file filter to only check files in the source directory
    # This prevents checking files in _build, external dependencies, etc.
    cmd.extend(["--file-filter=" + source_dir + "/*"])

    # Add source directory
    cmd.append(source_dir)

    return cmd


def main():
    """Main entry point for the cppcheck runner script.

    Parses command line arguments and executes cppcheck in simple mode.
    """
    parser = argparse.ArgumentParser(
        description="Run cppcheck on Isaac Sim source code in simple mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run cppcheck on source directory
  %(prog)s --output report.txt       # Save results to file
  %(prog)s --source-dir custom/path  # Analyze custom directory
        """,
    )

    parser.add_argument("--source-dir", default="source", help="Source directory to analyze (default: source)")

    parser.add_argument("--output", "-o", dest="output_file", help="Output file for cppcheck results")

    parser.add_argument(
        "--dry-run", action="store_true", help="Print the command that would be executed without running it"
    )

    parser.add_argument("--debug", action="store_true", help="Print the full cppcheck command before execution")

    parser.add_argument("--cppcheck", default="cppcheck", help="Path to the cppcheck binary")

    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")

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

    print("Running cppcheck in simple mode")

    # Build and execute cppcheck command
    cmd = build_cppcheck_command(
        source_dir=source_dir,
        output_file=args.output_file,
        cppcheck_bin=args.cppcheck,
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
        result = subprocess.run(cmd, check=False, timeout=args.timeout)
        if result.returncode == 0:
            print("cppcheck completed successfully")
        else:
            print(f"cppcheck completed with return code {result.returncode}")
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print(f"Error: cppcheck timed out after {args.timeout} seconds", file=sys.stderr)
        sys.exit(124)
    except FileNotFoundError:
        print("Error: cppcheck not found. Please install cppcheck.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
