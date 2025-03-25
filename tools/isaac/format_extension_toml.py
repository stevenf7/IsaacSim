#!/usr/bin/env python3
"""
Script to format all extension.toml files in the repository using tomlkit.
This script preserves comments and formatting while standardizing the TOML structure.
"""

import argparse
import difflib
import os
import re
import sys
from pathlib import Path

# Check if tomlkit is installed
try:
    import tomlkit
except ImportError:
    print("Error: The 'tomlkit' package is required to run this script.")
    print("Please install it using: pip install tomlkit")
    sys.exit(1)


def find_extension_toml_files(base_dir, filename_pattern="extension.toml"):
    """
    Recursively find all extension.toml files in the extensions directory.

    Args:
        base_dir (str): Base directory to start the search from
        filename_pattern (str): Filename pattern to search for

    Returns:
        list: List of paths to extension.toml files
    """
    extension_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == filename_pattern:
                extension_files.append(os.path.join(root, file))
    return extension_files


def print_diff(file_path, original_content, formatted_content):
    """
    Generate and print the diff between original and formatted content.

    Args:
        file_path (str): Path to the file being formatted
        original_content (str): Original file content
        formatted_content (str): Formatted file content

    Returns:
        bool: True if there are differences, False if the content is identical
    """
    # Split content into lines for difflib
    original_lines = original_content.splitlines(keepends=True)
    formatted_lines = formatted_content.splitlines(keepends=True)

    # Generate unified diff
    diff = list(
        difflib.unified_diff(
            original_lines,
            formatted_lines,
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (formatted)",
            n=3,  # Context lines
        )
    )

    if diff:
        # Print the diff
        print(f"\nDiff for {file_path}:")
        print("".join(diff))
        return True
    else:
        print(f"\nNo differences found in {file_path}")
        return False


def apply_strict_formatting(content):
    """
    Apply strict formatting rules to TOML content that tomlkit might not handle.

    Args:
        content (str): The TOML content to format

    Returns:
        str: The formatted TOML content
    """
    # Format equals signs (key = value) with exactly one space on each side
    content = re.sub(r"(\w+)\s*=\s*", r"\1 = ", content)

    # Remove excessive whitespace at the end of lines
    content = re.sub(r"\s+$", "", content, flags=re.MULTILINE)

    # Ensure not more than 2 consecutive empty lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Add space after comment markers if missing
    content = re.sub(r"#([^\s])", r"# \1", content)

    # Fix issues with array formatting - we want to preserve array structure
    # rather than have the regex break it

    # Parse the TOML again to get a clean structure (but ignore our formatting)
    # This ensures arrays and other complex structures are preserved properly
    try:
        parsed = tomlkit.parse(content)
        content = tomlkit.dumps(parsed)
    except Exception as e:
        # If parsing fails, keep the original content
        print(f"Warning: Could not parse TOML for strict formatting: {e}")

    # Fix empty line between sections
    lines = content.splitlines()
    result_lines = []
    prev_line_empty = False
    prev_line_section = False

    for line in lines:
        line_empty = not line.strip()
        line_section = line.strip().startswith("[")

        # Skip consecutive empty lines
        if line_empty and prev_line_empty:
            continue

        # Ensure a blank line before a section header, unless it's the first line
        if line_section and not prev_line_empty and result_lines:
            result_lines.append("")

        result_lines.append(line)

        prev_line_empty = line_empty
        prev_line_section = line_section

    return "\n".join(result_lines)


def format_toml_file(file_path, print_diffs=True, apply_changes=True, debug=False, strict=False):
    """
    Format a TOML file using tomlkit, preserving comments.

    Args:
        file_path (str): Path to the TOML file
        print_diffs (bool): Whether to print diffs between original and formatted content
        apply_changes (bool): Whether to apply the changes to the file
        debug (bool): Whether to print debug information
        strict (bool): Whether to apply strict formatting rules beyond what tomlkit does

    Returns:
        bool: True if formatting was successful, False otherwise
    """
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        if debug:
            print("\nORIGINAL CONTENT:")
            print("-" * 80)
            print(original_content)
            print("-" * 80)

        # Parse the TOML content
        parsed_toml = tomlkit.parse(original_content)

        # Format the content with tomlkit
        tomlkit_formatted = tomlkit.dumps(parsed_toml)

        # Apply additional formatting if strict mode is enabled
        if strict:
            formatted_content = apply_strict_formatting(tomlkit_formatted)
        else:
            formatted_content = tomlkit_formatted

        if debug:
            print("\nFORMATTED CONTENT:")
            print("-" * 80)
            print(formatted_content)
            print("-" * 80)

        # Show diff if requested
        has_changes = False
        if print_diffs:
            has_changes = print_diff(file_path, original_content, formatted_content)
            if not has_changes and not apply_changes:
                return True

        # Write back to the file if apply_changes is True and there are changes
        if apply_changes and (original_content != formatted_content):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_content)

        return True
    except Exception as e:
        print(f"Error formatting {file_path}: {e}")
        return False


def format_specific_file(file_path, print_diffs=True, apply_changes=True, debug=False, strict=False):
    """
    Format a specific TOML file.

    Args:
        file_path (str): Path to the TOML file
        print_diffs (bool): Whether to print diffs between original and formatted content
        apply_changes (bool): Whether to apply the changes to the file
        debug (bool): Whether to print debug information
        strict (bool): Whether to apply strict formatting rules beyond what tomlkit does

    Returns:
        bool: True if formatting was successful, False otherwise
    """
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    if not file_path.endswith(".toml"):
        print(f"Error: Not a TOML file: {file_path}")
        return False

    return format_toml_file(file_path, print_diffs, apply_changes, debug, strict)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Format extension.toml files using tomlkit library.")
    parser.add_argument("--dry-run", action="store_true", help="Show diffs without making changes to files")
    parser.add_argument("--no-diff", action="store_true", help="Don't print diffs (useful for processing many files)")
    parser.add_argument(
        "--dir",
        type=str,
        default=os.path.join("source", "extensions"),
        help="Base directory to search for extension.toml files (default: source/extensions)",
    )
    parser.add_argument("--file", type=str, help="Format a specific TOML file instead of searching for files")
    parser.add_argument(
        "--pattern", type=str, default="extension.toml", help="Filename pattern to search for (default: extension.toml)"
    )
    parser.add_argument("--verbose", action="store_true", help="Print more detailed information during processing")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    parser.add_argument("--strict", action="store_true", help="Apply strict formatting rules beyond what tomlkit does")
    return parser.parse_args()


def main():
    args = parse_args()

    # Process a single file if specified
    if args.file:
        print(f"Processing file: {args.file}")
        success = format_specific_file(args.file, not args.no_diff, not args.dry_run, args.debug, args.strict)
        if success:
            print("Processing completed successfully.")
            if args.dry_run:
                print("No changes were applied (dry-run mode).")
        else:
            print("Processing failed.")
        return

    # Define the extensions directory path
    extensions_dir = args.dir

    # Check if the directory exists
    if not os.path.isdir(extensions_dir):
        print(f"Error: Directory not found at {extensions_dir}")
        sys.exit(1)

    # Find all extension.toml files
    toml_files = find_extension_toml_files(extensions_dir, args.pattern)

    if not toml_files:
        print(f"No {args.pattern} files found.")
        sys.exit(0)

    toml_files.sort()  # Sort files for consistent output

    print(f"Found {len(toml_files)} {args.pattern} files.")

    # Format each file
    success_count = 0
    changed_count = 0
    failed_files = []

    for file_path in toml_files:
        print(f"Processing {file_path}...", end=" ")

        # In dry-run mode, we print diffs but don't apply changes
        if format_toml_file(file_path, not args.no_diff, not args.dry_run, args.debug, args.strict):
            success_count += 1
            print("Done")
        else:
            failed_files.append(file_path)
            print("Failed")

    # Summary
    print(f"\nSuccessfully processed {success_count} out of {len(toml_files)} files.")

    if args.dry_run:
        print("No changes were applied (dry-run mode).")

    if failed_files:
        print("\nFailed to process the following files:")
        for file_path in failed_files:
            print(f"  {file_path}")


if __name__ == "__main__":
    main()
