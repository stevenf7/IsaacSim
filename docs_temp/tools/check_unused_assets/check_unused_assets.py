"""
Script to check for unreferenced assets in the documentation.

This script scans the image directory and checks if each image file is referenced
in any of the RST files in the documentation. It reports any unreferenced images,
which can then be removed to keep the documentation clean.

Usage:
    python check_unused_assets.py [--print-all] [--output-file FILENAME]

Options:
    --print-all       Print all files and their reference status instead of only unreferenced ones
    --output-file     Specify an output file for the report (default: unused_assets_report.log)
"""

import argparse
import mimetypes
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path


def get_all_images(image_dir):
    """
    Get all image and video files in the given directory and its subdirectories.

    Args:
        image_dir (str): Path to the images directory

    Returns:
        dict: Dictionary mapping filenames to their full paths
    """
    mimetypes.init()
    images = {}

    for root, _, files in os.walk(image_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, image_dir)

            # Use only filename as the key to avoid path separator issues
            filename = os.path.basename(relative_path)

            # Check if it's an image or video file
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and (mime_type.startswith("image/") or mime_type.startswith("video/")):
                images[filename] = file_path
            # Include files with known image/video extensions
            elif any(
                file.lower().endswith(ext)
                for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".webm", ".mov")
            ):
                images[filename] = file_path

    return images


def find_rst_files(docs_dir):
    """
    Find all RST files in the documentation directory and its subdirectories.

    Args:
        docs_dir (str): Path to the documentation directory

    Returns:
        list: List of RST file paths
    """
    rst_files = []

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(".rst"):
                rst_files.append(os.path.join(root, file))

    return rst_files


def extract_image_references(rst_files):
    """
    Extract all image references from RST files using both pattern matching and simple string search.

    Args:
        rst_files (list): List of RST file paths

    Returns:
        dict: Dictionary mapping image filenames to the files that reference them
    """
    referenced_images = defaultdict(list)

    # Process each RST file once
    for rst_file in rst_files:
        try:
            with open(rst_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

                # Build a list of all filenames in the content
                # This is a simple approach that captures all occurrences of the filename
                # even if they're not in a standard image directive
                words = re.findall(r'[^\s\'"()<>:;,]+', content)

                for word in words:
                    # Check if this word looks like an image filename (has an image extension)
                    if re.search(r"\.(png|jpg|jpeg|gif|webp|svg|mp4|webm|mov)$", word, re.IGNORECASE):
                        # Get just the filename part, removing any path components
                        filename = os.path.basename(word)
                        referenced_images[filename].append(rst_file)

        except UnicodeDecodeError:
            print(f"Warning: Could not read {rst_file} due to encoding issues")

    return referenced_images


def check_image_references(images, rst_files, image_dir):
    """
    Check if each image is referenced in any of the RST files using a simple string search approach.
    Focus only on filenames to avoid path separator issues between Windows and Linux.

    Args:
        images (dict): Dictionary mapping filenames to their full paths
        rst_files (list): List of RST file paths
        image_dir (str): Path to the images directory

    Returns:
        tuple: (List of unreferenced image file paths, Dictionary of referenced images with their source files)
    """
    # Build a dictionary of all image references in RST files
    referenced_image_dict = extract_image_references(rst_files)

    unreferenced_images = []
    referenced_images = {}

    # Check each image against the reference dictionary
    for filename, full_path in images.items():
        # Check if the image is referenced by its filename
        if filename in referenced_image_dict:
            # Image is referenced, store the first file that references it
            referenced_images[full_path] = referenced_image_dict[filename][0]
        else:
            # Image is not referenced
            unreferenced_images.append(full_path)

    return unreferenced_images, referenced_images


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Check for unreferenced assets in documentation.")
    parser.add_argument("--print-all", action="store_true", help="Print all files and their reference status")
    parser.add_argument(
        "--output-file",
        default="unused_assets_report.log",
        help="Output file name (saved in _validate_asset_references directory)",
    )
    args = parser.parse_args()

    # Set paths
    # Assuming the script is run from the root of the codebase
    try:
        # Track script execution time
        script_start = time.time()

        # Default image directory and docs directory using relative paths from the root
        image_dir = os.path.abspath("docs/app_isaacsim/images")
        docs_dir = os.path.abspath("docs/app_isaacsim")

        # Check if the directories exist
        if not os.path.exists(image_dir):
            raise FileNotFoundError(f"Image directory not found: {image_dir}")

        if not os.path.exists(docs_dir):
            raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")

        # Get all images
        images = get_all_images(image_dir)
        print(f"Found {len(images)} image files in {image_dir}")

        # Get all RST files
        rst_files = find_rst_files(docs_dir)
        print(f"Found {len(rst_files)} RST files in {docs_dir}")

        # Check image references
        unreferenced_images, referenced_images = check_image_references(images, rst_files, image_dir)

        # Prepare output text
        output_lines = []
        output_lines.append(f"Found {len(images)} image files in {image_dir}")
        output_lines.append(f"Found {len(rst_files)} RST files in {docs_dir}")

        if args.print_all:
            output_lines.append("\nAll image files:")

            # First add all referenced images (sorted)
            output_lines.append("\nReferenced Images:")
            for image in sorted(referenced_images.keys()):
                output_lines.append(
                    f"  [REFERENCED] {image} (in {os.path.relpath(referenced_images[image], os.getcwd())})"
                )

            # Then add all unreferenced images (sorted)
            if unreferenced_images:
                output_lines.append("\nUnreferenced Assets:")
                for image in sorted(unreferenced_images):
                    output_lines.append(f"  [UNREFERENCED] {image}")

            output_lines.append(
                f"\nTotal: {len(referenced_images)} referenced, {len(unreferenced_images)} unreferenced"
            )
        elif unreferenced_images:
            output_lines.append("\nUnreferenced assets:")
            for image in sorted(unreferenced_images):
                output_lines.append(f"  {image}")
            output_lines.append(f"\nTotal: {len(unreferenced_images)} unreferenced assets")

        # Print output to console
        for line in output_lines:
            print(line)

        # Create output directory if it doesn't exist
        output_dir = "_validate_asset_references"
        os.makedirs(output_dir, exist_ok=True)

        # Write output to file
        if os.path.isabs(args.output_file):
            # If the path is absolute, use it as is
            output_path = args.output_file
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            # If it's a relative path or just a filename, place it in the _validate_asset_references directory
            output_path = os.path.join(output_dir, args.output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")

        print(f"\nReport saved to {output_path}")

        # Show execution time
        total_duration = time.time() - script_start
        print(f"Script execution time: {total_duration:.2f} seconds")

        return 1 if unreferenced_images else 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
