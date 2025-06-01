#!/usr/bin/env python3

import argparse
import os
import re
import sys
from pathlib import Path

# Define standard arguments for different test sections
STANDARD_TEST_ARGS = [
    "--/app/asyncRendering=0",
    "--/app/asyncRenderingLowLatency=0",
    "--/app/fastShutdown=1",
    "--/app/file/ignoreUnsavedOnExit=1",
    "--/app/hydraEngine/waitIdle=0",
    "--/app/renderer/skipWhileMinimized=0",
    "--/app/renderer/sleepMsOnFocus=0",
    "--/app/renderer/sleepMsOutOfFocus=0",
    "--/app/settings/fabricDefaultStageFrameHistoryCount=3",
    "--/app/settings/persistent=0",
    "--/app/viewport/createCameraModelRep=0",
    "--/crashreporter/skipOldDumpUpload=1",
    "--/exts/omni.usd/locking/onClose=0",
    "--/omni/kit/plugin/syncUsdLoads=1",
    "--/omni/replicator/asyncRendering=0",
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
    "--/'rtx-transient'/resourcemanager/enableTextureStreaming=1",
    "--/rtx/descriptorSets=360000",
    "--/rtx/hydra/enableSemanticSchema=1",
    "--/rtx/hydra/materialSyncLoads=1",
    "--/rtx/materialDb/syncLoads=1",
    "--/rtx/newDenoiser/enabled=1",
    "--/rtx/reservedDescriptors=900000",
    "--vulkan",
    "--/app/useFabricSceneDelegate=true",
    "--/app/player/useFixedTimeStepping=false",
    "--/app/runLoops/main/rateLimitEnabled=false",
    "--/app/runLoops/main/manualModeEnabled=true",
]

STARTUP_TEST_ARGS = [
    "--/app/settings/fabricDefaultStageFrameHistoryCount = 3",
]


def format_args_section(args_list):
    """Format the args list into a properly indented TOML array with one arg per line."""
    lines = ["args = ["]
    for arg in args_list:
        # Ensure all arguments are properly quoted
        arg = arg.strip()
        if arg.startswith("'") and arg.endswith("'"):
            # Already has single quotes, keep as is
            lines.append(f"    {arg},")
        elif arg.startswith('"') and arg.endswith('"'):
            # Already has double quotes, keep as is
            lines.append(f"    {arg},")
        elif '"' in arg:
            # Contains double quotes, use single quotes
            lines.append(f"    '{arg}',")
        else:
            # Use double quotes by default
            lines.append(f'    "{arg}",')
    lines.append("]")
    return lines


def read_file_preserving_lines(file_path):
    """Read a file and return its contents as a list of lines with newlines preserved."""
    with open(file_path, "r") as f:
        return f.readlines()


def write_file(file_path, lines):
    """Write a list of lines to a file."""
    with open(file_path, "w") as f:
        f.writelines(lines)


def process_extension_toml(file_path, verbose=False):
    """Process a single extension.toml file.

    Args:
        file_path: Path to the extension.toml file.
        verbose: Whether to print detailed processing information.

    Returns:
        True if processing was successful, False otherwise.
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

            if stripped == "[[test]]":
                in_test_section = True
                current_test = {
                    "start_line": i,
                    "is_startup": False,
                    "args_start": None,
                    "args_end": None,
                    "extension_specific_start": None,
                }
                test_sections.append(current_test)

            if in_test_section:
                if stripped.startswith('name = "startup"'):
                    current_test["is_startup"] = True

                if stripped.startswith("args ="):
                    current_test["args_start"] = i

                    # Check if this is a single-line args declaration
                    if stripped.endswith("]"):
                        current_test["args_end"] = i
                    else:
                        # Find the closing bracket
                        bracket_count = line.count("[") - line.count("]")

                        # Also look for extension specific args marker
                        for j in range(i + 1, len(original_lines)):
                            next_line = original_lines[j]
                            next_stripped = next_line.strip()

                            # Check for extension specific args marker
                            if "### Extension specific args" in next_line:
                                current_test["extension_specific_start"] = j

                            # Count brackets to find the end of the args section
                            bracket_count += next_line.count("[") - next_line.count("]")
                            if bracket_count <= 0:
                                current_test["args_end"] = j
                                break

                # End of this test section detected
                if i > current_test["start_line"] and stripped.startswith("[["):
                    in_test_section = False

        # Second pass: replace the args sections
        # We process in reverse order to avoid invalidating line numbers
        result_lines = original_lines.copy()

        missing_args_sections = False

        for section in sorted(test_sections, key=lambda s: s["start_line"], reverse=True):
            if section["args_start"] is None or section["args_end"] is None:
                if verbose:
                    print(f"  Warning: No args section found for test at line {section['start_line'] + 1}")
                missing_args_sections = True
                continue

            # Check if there are extension-specific args to preserve
            extension_specific_lines = []
            if section["extension_specific_start"] is not None:
                # Save all lines from the extension specific marker to the end of the args section
                extension_specific_start = section["extension_specific_start"]
                extension_specific_end = section["args_end"]
                extension_specific_lines = original_lines[extension_specific_start : extension_specific_end + 1]
                if verbose:
                    print(
                        f"  Preserving extension-specific args (lines {extension_specific_start + 1}-{extension_specific_end + 1})"
                    )

                # Adjust the end of the section we're replacing
                adjusted_end = extension_specific_start - 1
            else:
                adjusted_end = section["args_end"]

            # Generate the replacement content
            if section["is_startup"]:
                formatted_args = format_args_section(STARTUP_TEST_ARGS)
                if verbose:
                    print(
                        f"  Replacing startup test args section (lines {section['args_start'] + 1}-{adjusted_end + 1})"
                    )
            else:
                formatted_args = format_args_section(STANDARD_TEST_ARGS)
                if verbose:
                    print(
                        f"  Replacing regular test args section (lines {section['args_start'] + 1}-{adjusted_end + 1})"
                    )

            # Format with proper line endings
            formatted_text = [line + "\n" for line in formatted_args[:-1]]  # All except the closing bracket

            # If we have extension-specific args, don't add the closing bracket
            if extension_specific_lines:
                # Replace the section before the extension specific args
                result_lines[section["args_start"] : extension_specific_start] = formatted_text
            else:
                # Add the closing bracket and replace the entire section
                formatted_text.append(formatted_args[-1] + "\n")  # Add the closing bracket
                result_lines[section["args_start"] : adjusted_end + 1] = formatted_text

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
        return False


def find_repo_root():
    """Find the repository root directory from the current working directory."""
    current_dir = os.path.abspath(os.curdir)

    # Navigate up the directory tree looking for a directory containing "source/extensions"
    while current_dir != os.path.dirname(current_dir):  # Stop at the filesystem root
        if os.path.isdir(os.path.join(current_dir, "source", "extensions")):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # If we reach here, we didn't find the repo root
    return None


def find_extension_tomls(root_dir):
    """Find all extension.toml files under the given directory."""
    extensions_dir = os.path.join(root_dir, "source", "extensions")
    if not os.path.isdir(extensions_dir):
        print(f"Directory {extensions_dir} not found.")
        return []

    toml_files = []
    for root, dirs, files in os.walk(extensions_dir):
        for file in files:
            if file == "extension.toml":
                toml_files.append(os.path.join(root, file))
    return toml_files


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Standardize test args in extension.toml files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Process all extension.toml files under source/extensions")
    group.add_argument("--file", type=str, help="Process a specific extension.toml file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def main():
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
