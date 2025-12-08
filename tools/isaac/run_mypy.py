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
Run mypy type checking on Isaac Sim extensions, one extension at a time.

This script works around mypy's limitation with namespace packages in monorepos
by running mypy separately on each extension, avoiding "duplicate module name" conflicts.

Usage (via repo.sh):
    # Check all extensions
    ./repo.sh run_mypy

    # Check specific extensions
    ./repo.sh run_mypy --extensions isaacsim.core.utils isaacsim.core.prims

    # Check extensions matching a pattern
    ./repo.sh run_mypy --pattern "isaacsim.core.*"

    # Show only extensions with errors
    ./repo.sh run_mypy --errors-only

    # Verbose output showing all mypy messages
    ./repo.sh run_mypy --verbose

    # Generate JSON report
    ./repo.sh run_mypy --json-output report.json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ExtensionResult:
    """Results from running mypy on a single extension."""

    def __init__(
        self,
        name: str,
        path: str,
        files_checked: int,
        errors: int,
        error_messages: Optional[List[str]] = None,
        duration_seconds: float = 0.0,
        skipped: bool = False,
        skip_reason: str = "",
    ):
        self.name = name
        self.path = path
        self.files_checked = files_checked
        self.errors = errors
        self.error_messages = error_messages if error_messages is not None else []
        self.duration_seconds = duration_seconds
        self.skipped = skipped
        self.skip_reason = skip_reason


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def colorize(text: str, color: str, use_color: bool = True) -> str:
    """Apply color to text if colors are enabled."""
    if use_color and sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def get_mypy_from_vendor() -> tuple[Optional[str], Optional[str]]:
    """Get mypy binary and vendor directory from repo_lint.

    Returns:
        Tuple of (mypy_binary_path, vendor_directory) or (None, None) if not found.
    """
    try:
        from omni.repo.lint import vendor_directory

        mypy_path = Path(vendor_directory) / "bin" / "mypy"
        if mypy_path.exists():
            return str(mypy_path), str(vendor_directory)
    except ImportError:
        pass

    return None, None


def find_extensions(extensions_dir: Path) -> List[Path]:
    """Find all extension directories in the given path."""
    extensions = []
    if not extensions_dir.exists():
        return extensions

    for item in sorted(extensions_dir.iterdir()):
        if item.is_dir() and item.name.startswith("isaacsim."):
            extensions.append(item)

    return extensions


def find_python_dir(extension_path: Path) -> Optional[Path]:
    """Find the Python source directory for an extension.

    Extensions can have different structures:
    - python/impl/  (common pattern)
    - isaacsim/.../ (namespace package pattern)
    """
    # Check for python/impl structure
    python_impl = extension_path / "python" / "impl"
    if python_impl.exists():
        return python_impl

    # Check for isaacsim namespace package structure
    isaacsim_dir = extension_path / "isaacsim"
    if isaacsim_dir.exists():
        return isaacsim_dir

    # Check for any Python files directly
    if list(extension_path.glob("*.py")):
        return extension_path

    return None


def count_python_files(directory: Path, exclude_patterns: List[str]) -> int:
    """Count Python files in a directory, excluding certain patterns."""
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


def run_mypy_on_extension(
    extension_path: Path,
    config_file: Optional[Path],
    exclude_patterns: List[str],
    mypy_bin: str,
    vendor_dir: Optional[str] = None,
) -> ExtensionResult:
    """Run mypy on a single extension and return results."""
    extension_name = extension_path.name
    result = ExtensionResult(name=extension_name, path=str(extension_path), files_checked=0, errors=0)

    # Find Python source directory
    python_dir = find_python_dir(extension_path)
    if python_dir is None:
        result.skipped = True
        result.skip_reason = "No Python source directory found"
        return result

    # Count Python files (approximate - actual exclusions handled by mypy config)
    result.files_checked = count_python_files(python_dir, [])
    if result.files_checked == 0:
        result.skipped = True
        result.skip_reason = "No Python files to check"
        return result

    # Build mypy command
    cmd = [mypy_bin]

    if config_file and config_file.exists():
        cmd.extend(["--config-file", str(config_file)])

    # Add exclude patterns (regex patterns for mypy)
    for pattern in exclude_patterns:
        cmd.extend(["--exclude", pattern])

    # Add the directory to check
    cmd.append(str(python_dir))

    # Set up environment - must include vendor_dir in PYTHONPATH for mypy to work
    env = os.environ.copy()
    if vendor_dir:
        env["PYTHONPATH"] = vendor_dir
    else:
        env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)

    start_time = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=extension_path.parent.parent.parent, env=env)
        result.duration_seconds = time.time() - start_time

        # Parse output
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if stdout:
            lines = stdout.split("\n")
            for line in lines:
                if ": error:" in line:
                    result.errors += 1
                    result.error_messages.append(line)
                elif "Found" in line and "error" in line:
                    # Summary line like "Found 5 errors in 3 files"
                    pass
                elif line.strip() and not line.startswith("Success"):
                    result.error_messages.append(line)

        if stderr and "error" in stderr.lower():
            result.error_messages.append(f"[stderr] {stderr}")

    except FileNotFoundError:
        result.skipped = True
        result.skip_reason = f"mypy not found at {mypy_bin}"
    except Exception as e:
        result.skipped = True
        result.skip_reason = f"Error running mypy: {e}"

    return result


def print_summary(
    results: List[ExtensionResult],
    use_color: bool = True,
    errors_only: bool = False,
) -> None:
    """Print a summary of all results in LLM-friendly format."""
    total_extensions = len(results)
    passed = sum(1 for r in results if r.errors == 0 and not r.skipped)
    failed = sum(1 for r in results if r.errors > 0)
    skipped = sum(1 for r in results if r.skipped)
    total_errors = sum(r.errors for r in results)
    total_files = sum(r.files_checked for r in results)
    total_time = sum(r.duration_seconds for r in results)

    # Print errors grouped by file for easy fixing
    failed_results = [r for r in results if r.errors > 0]
    if failed_results:
        print("\n" + "=" * 80)
        print("MYPY TYPE ERRORS")
        print("=" * 80)

        for result in failed_results:
            print(f"\n## {result.name} ({result.errors} errors)")

            # Group errors by file
            errors_by_file: Dict[str, List[str]] = {}
            for msg in result.error_messages:
                if ": error:" in msg and not msg.startswith("[stderr]"):
                    parts = msg.split(": error:", 1)
                    if len(parts) == 2:
                        file_info = parts[0]
                        file_path = file_info.rsplit(":", 1)[0] if ":" in file_info else file_info
                        if file_path not in errors_by_file:
                            errors_by_file[file_path] = []
                        errors_by_file[file_path].append(msg)

            for file_path, errors in errors_by_file.items():
                print(f"\n{file_path}:")
                for error in errors:
                    print(f"  {error}")

    # Print summary table
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for result in results:
        if errors_only and result.errors == 0 and not result.skipped:
            continue

        if result.skipped:
            status = colorize("SKIP", Colors.YELLOW, use_color)
            detail = result.skip_reason
        elif result.errors == 0:
            status = colorize("PASS", Colors.GREEN, use_color)
            detail = f"{result.files_checked} files"
        else:
            status = colorize("FAIL", Colors.RED, use_color)
            detail = f"{result.errors} errors"

        print(f"  [{status}] {result.name}: {detail}")

    print(f"\nTotal: {total_extensions} extensions, {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Files: {total_files}, Errors: {total_errors}, Time: {total_time:.2f}s")


def save_json_report(results: List[ExtensionResult], output_path: Path) -> None:
    """Save results as a JSON report."""
    report = {
        "summary": {
            "total_extensions": len(results),
            "passed": sum(1 for r in results if r.errors == 0 and not r.skipped),
            "failed": sum(1 for r in results if r.errors > 0),
            "skipped": sum(1 for r in results if r.skipped),
            "total_errors": sum(r.errors for r in results),
            "total_files": sum(r.files_checked for r in results),
        },
        "extensions": [
            {
                "name": r.name,
                "path": r.path,
                "files_checked": r.files_checked,
                "errors": r.errors,
                "error_messages": r.error_messages,
                "duration_seconds": r.duration_seconds,
                "skipped": r.skipped,
                "skip_reason": r.skip_reason,
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nJSON report saved to: {output_path}")


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> Callable:
    """Setup function for the repo tool integration.

    Args:
        parser: ArgumentParser to configure with command-line arguments.
        config: Configuration dictionary from repo.toml.

    Returns:
        The run_tool function to execute the tool.
    """
    parser.description = "Run mypy type checking on extensions, one at a time."

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
        "--config",
        "-c",
        help="Path to mypy configuration file (default: tools/isaac/.mypy.ini)",
    )
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
        "--exclude",
        nargs="+",
        default=[],  # Exclusions handled by .mypy.ini exclude pattern
        help="Regex patterns to exclude from checking (passed to mypy --exclude)",
    )

    # Get tool config from repo.toml if available
    tool_config = config.get("repo_run_mypy", {})

    def run_tool(args: argparse.Namespace, config: Dict[str, Any] = config) -> int:
        """Run the mypy per-extension tool.

        Args:
            args: Parsed command-line arguments.
            config: Configuration dictionary.

        Returns:
            0 if all checks passed, 1 if there were errors.
        """
        # Get root directory
        repo_root = Path(config.get("root", os.getcwd()))

        # Find extensions directory
        extensions_dir = repo_root / "source" / "extensions"
        if not extensions_dir.exists():
            print(f"Error: Extensions directory not found: {extensions_dir}")
            return 1

        # Find mypy binary from repo_lint vendor directory
        mypy_bin, vendor_dir = get_mypy_from_vendor()
        if not mypy_bin:
            print("Error: mypy not found. Make sure repo_lint dependencies are installed.")
            print("Try running: ./repo.sh lint mypy --help")
            return 1

        # Find all extensions
        all_extensions = find_extensions(extensions_dir)
        if not all_extensions:
            print(f"Error: No extensions found in {extensions_dir}")
            return 1

        # Filter extensions
        extensions_to_check = all_extensions
        if args.extensions:
            extensions_to_check = [e for e in all_extensions if e.name in args.extensions]
            if not extensions_to_check:
                print(f"Error: No matching extensions found for: {args.extensions}")
                return 1
        elif args.pattern:
            extensions_to_check = [e for e in all_extensions if fnmatch.fnmatch(e.name, args.pattern)]
            if not extensions_to_check:
                print(f"Error: No extensions matching pattern: {args.pattern}")
                return 1

        # Determine config file
        config_file = None
        if args.config:
            config_file = Path(args.config)
        else:
            # Check tool config first, then default
            config_path = tool_config.get("config", "${root}/tools/isaac/.mypy.ini")
            config_path = config_path.replace("${root}", str(repo_root))
            default_config = Path(config_path)
            if default_config.exists():
                config_file = default_config

        # Get exclude patterns from tool config or args (regex patterns for mypy --exclude)
        exclude_patterns = args.exclude or tool_config.get("exclude", [])

        # Run mypy on each extension
        use_color = not args.no_color
        print(colorize(f"Running mypy on {len(extensions_to_check)} extensions...", Colors.CYAN, use_color))
        if config_file:
            print(colorize(f"Using config: {config_file}", Colors.DIM, use_color))
        print(colorize(f"Using mypy: {mypy_bin}", Colors.DIM, use_color))

        results: List[ExtensionResult] = []
        for i, extension in enumerate(extensions_to_check, 1):
            progress = f"[{i}/{len(extensions_to_check)}]"
            print(f"  {progress} Checking {extension.name}...", end=" ", flush=True)

            result = run_mypy_on_extension(
                extension_path=extension,
                config_file=config_file,
                exclude_patterns=exclude_patterns,
                mypy_bin=mypy_bin,
                vendor_dir=vendor_dir,
            )
            results.append(result)

            if result.skipped:
                print(colorize("skipped", Colors.YELLOW, use_color))
            elif result.errors == 0:
                print(colorize("ok", Colors.GREEN, use_color))
            else:
                print(colorize(f"{result.errors} errors", Colors.RED, use_color))

        # Print summary
        print_summary(results, use_color=use_color, errors_only=args.errors_only)

        # Save JSON report if requested
        if args.json_output:
            save_json_report(results, Path(args.json_output))

        # Return exit code
        total_errors = sum(r.errors for r in results)
        return 1 if total_errors > 0 else 0

    return run_tool


def main() -> int:
    """Main entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Run mypy type checking on extensions, one at a time.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Create a minimal config for standalone use
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    config = {"root": str(repo_root)}

    run_tool = setup_repo_tool(parser, config)
    args = parser.parse_args()

    return run_tool(args, config)


if __name__ == "__main__":
    sys.exit(main())
