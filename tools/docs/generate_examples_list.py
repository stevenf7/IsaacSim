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
Script to generate a list of all Python examples in the standalone_examples directory.
The output is an RST (reStructuredText) file containing relative paths to all Python scripts,
organized hierarchically by directory structure.
"""

import argparse
import os
from collections import defaultdict
from pathlib import Path


def find_python_files(root_dir):
    """Find all Python files in the given directory recursively.

    Args:
        root_dir: The root directory to start the search from.

    Returns:
        A sorted list of all Python files with paths relative to root_dir.
    """
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                # Get the path relative to root_dir
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                python_files.append(rel_path)

    # Sort the files alphabetically
    return sorted(python_files)


def organize_files_by_directory(python_files):
    """Organize Python files into a hierarchical structure based on their directory paths.

    Args:
        python_files: List of Python file paths.

    Returns:
        A nested dictionary representing the directory structure.
    """
    file_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for file_path in python_files:
        parts = file_path.split(os.sep)

        if len(parts) == 1:
            # Files at the root level
            file_tree[""][""][""].append(parts[0])
        elif len(parts) == 2:
            # Files one level deep
            file_tree[parts[0]][""][""].append(parts[1])
        elif len(parts) == 3:
            # Files two levels deep
            file_tree[parts[0]][parts[1]][""].append(parts[2])
        else:
            # Files three or more levels deep
            file_tree[parts[0]][parts[1]]["/".join(parts[2:-1])].append(parts[-1])

    return file_tree


def generate_rst_content(python_files, root_dir_name):
    """Generate RST content with hierarchical headings from the list of Python files.

    Args:
        python_files: List of Python file paths.
        root_dir_name: Name of the root directory (for title).

    Returns:
        A string containing the formatted RST content.
    """
    # Main title (level 1)
    content = [
        ".. _standalone_examples_reference_list:",
        "",
        "=====================================",
        "Standalone Examples Reference List",
        "=====================================",
        "",
        f"This document lists all standalone examples available in Isaac Sim.",
        "",
    ]

    # Organize files by directory
    file_tree = organize_files_by_directory(python_files)

    # Sort first level directories
    for first_level in sorted(file_tree.keys()):
        if first_level == "":
            # Handle root-level Python files
            if file_tree[""][""][""] and len(file_tree[""][""][""]) > 0:
                content.append("standalone_examples")
                content.append("-------------------")
                content.append("")

                for py_file in sorted(file_tree[""][""][""]):
                    content.append(f"* ``{py_file}``")

                content.append("")
            continue

        # Add level 2 heading for first-level directories
        content.append("standalone_examples/" + first_level)
        content.append("-" * len("standalone_examples/" + first_level))
        content.append("")

        # Sort second level directories
        for second_level in sorted(file_tree[first_level].keys()):
            if second_level == "":
                # Handle Python files directly under the first level
                if file_tree[first_level][""][""] and len(file_tree[first_level][""][""]) > 0:
                    for py_file in sorted(file_tree[first_level][""][""]):
                        content.append(f"* ``{py_file}``")

                    content.append("")
                continue

            # Add level 3 heading for second-level directories
            content.append(second_level)
            content.append("~" * len(second_level))
            content.append("")

            # Sort third level directories
            for third_level in sorted(file_tree[first_level][second_level].keys()):
                if third_level == "":
                    # Handle Python files directly under the second level
                    for py_file in sorted(file_tree[first_level][second_level][""]):
                        content.append(f"* ``{py_file}``")

                    content.append("")
                else:
                    # Add level 4 (paragraph) heading for third-level directories
                    content.append(third_level)
                    content.append("^" * len(third_level))
                    content.append("")

                    # List Python files under this directory
                    for py_file in sorted(file_tree[first_level][second_level][third_level]):
                        full_path = os.path.join(third_level, py_file) if third_level else py_file
                        content.append(f"* ``{full_path}``")

                    content.append("")

    # Add a blank line at the end
    if not content[-1] == "":
        content.append("")

    return "\n".join(content)


def main():
    """Main function to parse arguments and generate the RST file.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    parser = argparse.ArgumentParser(description="Generate RST file listing all Python examples.")
    parser.add_argument(
        "--examples-dir",
        type=str,
        default="../../source/standalone_examples",
        help="Path to the standalone_examples directory",
    )
    parser.add_argument("--output", type=str, default="standalone_examples_list.rst", help="Output RST file path")
    args = parser.parse_args()

    examples_dir = Path(args.examples_dir)
    if not examples_dir.exists():
        print(f"Error: Directory '{examples_dir}' does not exist.")
        return 1

    print(f"Scanning for Python files in '{examples_dir}'...")
    python_files = find_python_files(examples_dir)

    # Use the last part of the examples_dir as the root_dir_name for the title
    root_dir_name = examples_dir.name

    rst_content = generate_rst_content(python_files, root_dir_name)

    # Write the RST content to the output file
    with open(args.output, "w") as f:
        f.write(rst_content)

    print(f"Found {len(python_files)} Python files.")
    print(f"RST file generated: {args.output}")
    return 0


def setup_repo_tool(parser, config):
    """Setup function for repo tool integration

    Args:
        parser: The argument parser
        config: The tool configuration
    """
    parser.add_argument(
        "--examples-dir",
        type=str,
        help="Path to the examples directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output RST file path",
    )
    parser.add_argument("-c", "--config", type=str, default="release", help="Build configuration (debug or release)")

    def execute(args, config=None):
        # Get config from repo_tools
        tool_config = config.get("repo_examples_list", {})

        # Use command-line args or config values
        examples_dir = args.examples_dir or tool_config.get("examples_dir")
        output_file = args.output or tool_config.get("output_file")

        if not examples_dir:
            print("ERROR: No examples directory specified. Use --examples-dir or set examples_dir in repo.toml.")
            return 1

        if not output_file:
            print("ERROR: No output file specified. Use --output or set output_file in repo.toml.")
            return 1

        # Resolve variables in paths if we have a repository object that has substitute_variables
        if hasattr(config, "substitute_variables"):
            examples_dir = config.substitute_variables(examples_dir, args)
            output_file = config.substitute_variables(output_file, args)

        examples_dir_path = Path(examples_dir)
        if not examples_dir_path.exists():
            print(f"ERROR: Directory '{examples_dir_path}' does not exist.")
            return 1

        print(f"Scanning for Python files in '{examples_dir_path}'...")
        python_files = find_python_files(examples_dir_path)

        # Use the last part of the examples_dir as the root_dir_name for the title
        root_dir_name = examples_dir_path.name

        rst_content = generate_rst_content(python_files, root_dir_name)

        # Create parent directories if they don't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the RST content to the output file
        with open(output_file, "w") as f:
            f.write(rst_content)

        print(f"Found {len(python_files)} Python files.")
        print(f"RST file generated: {output_file}")
        return 0

    return execute


if __name__ == "__main__":
    exit(main())
