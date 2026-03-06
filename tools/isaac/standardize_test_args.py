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

import argparse
import os
import sys
from typing import List, Optional

# Define standard arguments for different test sections
STANDARD_TEST_ARGS = [
    "--enable",
    "omni.kit.loop-isaac",
    "--reset-user",
    "--vulkan",
    "--/app/asyncRendering=0",
    "--/app/asyncRenderingLowLatency=0",
    "--/app/fastShutdown=1",
    "--/app/file/ignoreUnsavedStage=1",
    "--/app/hydraEngine/waitIdle=0",
    "--/app/player/useFixedTimeStepping=false",
    "--/app/renderer/skipWhileMinimized=0",
    "--/app/renderer/sleepMsOnFocus=0",
    "--/app/renderer/sleepMsOutOfFocus=0",
    "--/app/runLoops/main/manualModeEnabled=true",
    "--/app/runLoops/main/rateLimitEnabled=false",
    "--/app/settings/fabricDefaultStageFrameHistoryCount=3",
    "--/app/settings/persistent=0",
    "--/app/useFabricSceneDelegate=true",
    "--/app/viewport/createCameraModelRep=0",
    "--/crashreporter/skipOldDumpUpload=1",
    "--/exts/omni.usd/locking/onClose=0",
    "--/omni/kit/plugin/syncUsdLoads=1",
    "--/omni/replicator/asyncRendering=0",
    "--/omnihydra/parallelHydraSprimSync=1",
    '--/persistent/app/stage/upAxis="Z"',
    "--/persistent/app/viewport/defaults/tickRate=120",
    "--/persistent/app/viewport/displayOptions=31951",
    "--/persistent/omni/replicator/captureOnPlay=1",
    "--/persistent/omnigraph/updateToUsd=0",
    "--/persistent/physics/visualizationDisplayJoints=0",
    "--/persistent/renderer/startupMessageDisplayed=1",
    "--/persistent/simulation/defaultMetersPerUnit=1.0",
    "--/persistent/simulation/minFrameRate=15",
    "--/renderer/multiGpu/autoEnable=0",
    "--/renderer/multiGpu/enabled=0",
    "--/rtx-transient/dlssg/enabled=0",
    "--/rtx-transient/resourcemanager/enableTextureStreaming=1",
    "--/rtx/descriptorSets=360000",
    "--/rtx/hydra/enableSemanticSchema=1",
    "--/rtx/hydra/materialSyncLoads=1",
    "--/rtx/materialDb/syncLoads=1",
    "--/rtx/newDenoiser/enabled=1",
    "--/rtx/reservedDescriptors=900000",
    "--/UJITSO/geometry=true",
]

# Fixed: removed spaces around = to match STANDARD_TEST_ARGS format
STARTUP_TEST_ARGS = [
    "--/app/settings/fabricDefaultStageFrameHistoryCount=3",
]


def format_args_section(args_list: List[str]) -> List[str]:
    """Format the args list into a properly indented TOML array with one arg per line.

    Args:
        args_list: List of argument strings to format.

    Returns:
        List of formatted strings representing a TOML array, one line per element.
    """
    lines = ["args = ["]
    for arg in args_list:
        # Ensure all arguments are properly quoted
        arg = arg.strip()
        if not arg:  # Skip empty strings
            continue

        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            # Already properly quoted
            lines.append(f"    {arg},")
        elif '"' in arg:
            # Contains double quotes, use single quotes
            lines.append(f"    '{arg}',")
        else:
            # Use double quotes by default
            lines.append(f'    "{arg}",')
    lines.append("]")
    return lines


def read_file_preserving_lines(file_path: str) -> List[str]:
    """Read a file and return its contents as a list of lines with newlines preserved.

    Args:
        file_path: Path to the file to read.

    Returns:
        List of strings, each representing a line from the file including newline characters.

    Raises:
        IOError: If the file cannot be read.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def write_file(file_path: str, lines: List[str]) -> None:
    """Write a list of lines to a file.

    Args:
        file_path: Path to the file to write.
        lines: List of strings to write to the file.

    Raises:
        IOError: If the file cannot be written.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def find_args_section_end(lines: List[str], start_idx: int) -> Optional[int]:
    """Find the end of an args array section in TOML.

    Searches for the closing bracket of an args array, handling nested brackets
    and multi-line declarations.

    Args:
        lines: List of file lines to search through.
        start_idx: Index of the line containing 'args =' declaration.

    Returns:
        Index of the line containing the closing bracket, or None if not found.
    """
    # Check if single-line declaration
    if lines[start_idx].strip().endswith("]"):
        return start_idx

    # Multi-line: find closing bracket
    # Simple approach: look for a line with ] that's not inside quotes
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()
        # Simple heuristic: a line starting with ] is likely the closing bracket
        if line.startswith("]") or line == "]":
            return i

    return None


def process_extension_toml(file_path: str, verbose: bool = False) -> bool:
    """Process a single extension.toml file to standardize test args.

    Reads the extension.toml file, identifies all [[test]] sections, and replaces
    their args arrays with standardized arguments. Preserves extension-specific
    args marked with '### Extension specific args' comment.

    Args:
        file_path: Path to the extension.toml file to process.
        verbose: Whether to print detailed processing information.

    Returns:
        True if processing was successful, False otherwise.

    Raises:
        IOError: If the file cannot be read or written.
        Exception: For other processing errors.
    """
    if verbose:
        print(f"Processing file: {file_path}")
    else:
        print(f"Processing: {file_path}")

    try:
        # Read the file
        original_lines = read_file_preserving_lines(file_path)

        # First pass: identify all test sections
        test_sections = []
        current_test = None
        in_test_section = False

        for i, line in enumerate(original_lines):
            stripped = line.strip()

            # New test section starts
            if stripped == "[[test]]":
                in_test_section = True
                current_test = {
                    "start_line": i,
                    "is_startup": False,
                    "is_doctest": False,
                    "args_start": None,
                    "args_end": None,
                    "extension_specific_start": None,
                }
                test_sections.append(current_test)

            if in_test_section and current_test:
                # Check if this is a startup test
                if 'name = "startup"' in stripped or "name = 'startup'" in stripped:
                    current_test["is_startup"] = True

                # Check if this is a doctest (skip processing these)
                if 'name = "doctest"' in stripped or "name = 'doctest'" in stripped:
                    current_test["is_doctest"] = True

                # Found args section
                if stripped.startswith("args ="):
                    current_test["args_start"] = i
                    args_end = find_args_section_end(original_lines, i)
                    current_test["args_end"] = args_end

                    # Look for extension specific args marker within the args section
                    if args_end is not None:
                        for j in range(i + 1, args_end):
                            if "### Extension specific args" in original_lines[j]:
                                current_test["extension_specific_start"] = j
                                break

                # Another section starts (end of current test section)
                if i > current_test["start_line"] and (stripped.startswith("[[") or stripped.startswith("[package]")):
                    in_test_section = False

        # Handle case where last test section goes to end of file
        if in_test_section and current_test and current_test["args_start"] is not None:
            if current_test["args_end"] is None:
                current_test["args_end"] = len(original_lines) - 1

        # Second pass: replace the args sections
        # Process in reverse order to avoid invalidating line numbers
        result_lines = original_lines.copy()
        missing_args_sections = False

        for section in sorted(test_sections, key=lambda s: s["start_line"], reverse=True):
            # Skip doctest sections - don't modify their args
            if section["is_doctest"]:
                if verbose:
                    print(f"  Skipping doctest section at line {section['start_line'] + 1}")
                continue

            if section["args_start"] is None or section["args_end"] is None:
                if verbose:
                    print(f"  Warning: No args section found for test at line {section['start_line'] + 1}")
                missing_args_sections = True
                continue

            # Determine what to replace and what to preserve
            extension_specific_lines = []
            replace_end = section["args_end"]

            if section["extension_specific_start"] is not None:
                # Save extension-specific args (from marker to end of args section)
                ext_start = section["extension_specific_start"]
                extension_specific_lines = original_lines[ext_start : section["args_end"] + 1]
                replace_end = ext_start - 1  # Only replace up to the marker

                if verbose:
                    print(f"  Preserving extension-specific args (lines {ext_start + 1}-{section['args_end'] + 1})")

            # Generate the replacement content
            args_to_use = STARTUP_TEST_ARGS if section["is_startup"] else STANDARD_TEST_ARGS
            formatted_args = format_args_section(args_to_use)

            if verbose:
                test_type = "startup" if section["is_startup"] else "regular"
                print(
                    f"  Replacing {test_type} test args section (lines {section['args_start'] + 1}-{replace_end + 1})"
                )

            # Build replacement text
            formatted_text = [line + "\n" for line in formatted_args[:-1]]  # All except closing bracket

            # Add extension-specific args back if they exist
            if extension_specific_lines:
                # Don't add closing bracket, extension_specific_lines includes it
                result_lines[section["args_start"] : section["args_end"] + 1] = (
                    formatted_text + extension_specific_lines
                )
            else:
                # Add closing bracket
                formatted_text.append(formatted_args[-1] + "\n")
                result_lines[section["args_start"] : replace_end + 1] = formatted_text

        # Write the modified content
        write_file(file_path, result_lines)

        if verbose:
            print(f"  Successfully updated {file_path}")

        # Return False if any test sections were missing args
        if missing_args_sections:
            print(f"  Failed: Missing args section(s) in {os.path.basename(os.path.dirname(file_path))}")
            return False

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return False


def find_repo_root() -> Optional[str]:
    """Find the repository root directory from the current working directory.

    Searches upward through the directory tree looking for a directory containing
    the 'source/extensions' subdirectory structure.

    Returns:
        Absolute path to the repository root, or None if not found.
    """
    current_dir = os.path.abspath(os.curdir)

    # Navigate up the directory tree looking for a directory containing "source/extensions"
    while current_dir != os.path.dirname(current_dir):  # Stop at the filesystem root
        if os.path.isdir(os.path.join(current_dir, "source", "extensions")):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # If we reach here, we didn't find the repo root
    return None


def find_extension_tomls(root_dir: str) -> List[str]:
    """Find all extension.toml files under the given directory.

    Walks through the source/extensions and source/internal_extensions directories
    and collects paths to all extension.toml files.

    Args:
        root_dir: Root directory of the repository.

    Returns:
        List of absolute paths to extension.toml files found.
    """
    toml_files = []

    # Search directories
    search_dirs = [
        os.path.join(root_dir, "source", "extensions"),
        os.path.join(root_dir, "source", "internal_extensions"),
    ]

    for extensions_dir in search_dirs:
        if not os.path.isdir(extensions_dir):
            print(f"Directory {extensions_dir} not found, skipping.")
            continue

        for root, dirs, files in os.walk(extensions_dir):
            for file in files:
                if file == "extension.toml":
                    toml_files.append(os.path.join(root, file))

    return toml_files


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Standardize test args in extension.toml files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all extension.toml files
  %(prog)s --all

  # Process a specific file
  %(prog)s --file path/to/extension.toml

  # Process with verbose output
  %(prog)s --all --verbose
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all extension.toml files under source/extensions and source/internal_extensions",
    )
    group.add_argument("--file", type=str, help="Process a specific extension.toml file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    args = parse_args()
    verbose = args.verbose

    # Find the repository root
    repo_root = find_repo_root()
    if not repo_root:
        print("Error: Could not find repository root directory (containing source/extensions).")
        print("Please run this script from within the omni_isaac_sim repository.")
        return 1

    if verbose:
        print(f"Using repository root: {repo_root}")

    # Track files that failed processing
    failed_files = []

    if args.all:
        # Process all files under source/extensions
        toml_files = find_extension_tomls(repo_root)
        if not toml_files:
            print("No extension.toml files found.")
            return 1

        print(f"Found {len(toml_files)} extension.toml files to process.")

        # Process each file
        processed_count = 0
        for file_path in toml_files:
            try:
                result = process_extension_toml(file_path, verbose)
                if result:
                    processed_count += 1
                else:
                    failed_files.append(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                failed_files.append(file_path)

        print(f"Successfully processed {processed_count} out of {len(toml_files)} files.")
    else:
        # Process a single file
        file_path = args.file

        # Convert to absolute path if not already
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found.")
            return 1

        try:
            result = process_extension_toml(file_path, verbose)
            if not result:
                failed_files.append(file_path)
            print("File processing complete.")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            failed_files.append(file_path)
            return 1

    # Print failed files
    if failed_files:
        print("\nThe following files could not be processed successfully:")
        for file in failed_files:
            print(f"  - {file}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
