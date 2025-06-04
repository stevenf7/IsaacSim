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
import pathlib
import re
from pathlib import Path


def get_header_files(repo_root: Path, ignore_folders: list[str], ignore_files: list[str]) -> list[str]:
    """Get sorted list of header files with relative paths"""
    # Look in both extensions and deprecated directories
    scan_dirs = [repo_root / "source/extensions", repo_root / "source/deprecated"]
    header_files = []

    for base_dir in scan_dirs:
        if not base_dir.exists():
            continue

        for header_path in base_dir.rglob("*.h"):
            # Skip if matches ignore patterns
            if any(ignore in str(header_path) for ignore in ignore_folders):
                continue
            # Skip specific filenames
            if header_path.name in ignore_files:
                continue

            if header_path.is_file():
                rel_path = header_path.relative_to(repo_root)
                header_files.append(f'  "{rel_path.as_posix()}",')

    return sorted(header_files)


def update_repo_toml(repo_root: Path, header_files: list[str]):
    """Update doxygen_input section in repo.toml"""
    toml_path = repo_root / "repo.toml"

    # Generate new doxygen input section
    new_content = "doxygen_input = [\n" + "\n".join(header_files) + "\n]"

    # Read existing TOML content
    with open(toml_path, "r") as f:
        content = f.read()

    # Replace existing doxygen_input section using regex
    updated_content = re.sub(r"doxygen_input\s*=\s*\[[^\]]*\]", new_content, content, flags=re.DOTALL)

    # Write updated content back to file
    with open(toml_path, "w") as f:
        f.write(updated_content)


def setup_repo_tool(parser, config):
    """Setup function for repo tool integration

    Args:
        parser: The argument parser
        config: The tool configuration
    """
    parser.add_argument(
        "--root", type=str, default=".", help="Root directory of the repository (default: current directory)"
    )

    def execute(args, config=None):
        # Convert to absolute path
        root_path = Path(args.root).resolve()

        # Get configuration from repo.toml
        tool_config = config.get("repo_generate_doxygen_input", {})

        # Get scan directories from config or use defaults
        scan_dirs_config = tool_config.get("scan_dirs", ["${root}/source/extensions", "${root}/source/deprecated"])

        # Replace ${root} with actual root path
        scan_dirs = [Path(dir.replace("${root}", str(root_path))) for dir in scan_dirs_config]

        # Get ignore patterns from config or use defaults
        ignore_folders = tool_config.get("ignore_folders", ["isaac_ros2_messages"])
        ignore_files = tool_config.get("ignore_files", ["UsdPCH.h"])

        # Get headers and update TOML
        headers = get_header_files_with_dirs(root_path, scan_dirs, ignore_folders, ignore_files)
        update_repo_toml(root_path, headers)
        print(f"Updated {root_path/'repo.toml'} with {len(headers)} header files")
        print(f"Scanned directories: {[str(d) for d in scan_dirs]}")
        print(f"Ignored folders: {ignore_folders}")
        print(f"Ignored files: {ignore_files}")
        return 0

    return execute


def get_header_files_with_dirs(
    repo_root: Path, scan_dirs: list[Path], ignore_folders: list[str], ignore_files: list[str]
) -> list[str]:
    """Get sorted list of header files with relative paths using configurable scan directories"""
    header_files = []

    for base_dir in scan_dirs:
        if not base_dir.exists():
            print(f"Warning: Directory {base_dir} does not exist, skipping")
            continue

        for header_path in base_dir.rglob("*.h"):
            # Skip if matches ignore patterns
            if any(ignore in str(header_path) for ignore in ignore_folders):
                continue
            # Skip specific filenames
            if header_path.name in ignore_files:
                continue

            if header_path.is_file():
                rel_path = header_path.relative_to(repo_root)
                header_files.append(f'  "{rel_path.as_posix()}",')

    return sorted(header_files)


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate doxygen input list for repo.toml")
    parser.add_argument(
        "--root", type=str, default=".", help="Root directory of the repository (default: current directory)"
    )
    args = parser.parse_args()

    # Convert to absolute path
    root_path = Path(args.root).resolve()

    # Add more folder substrings to ignore as needed
    ignore_folders = ["isaac_ros2_messages"]
    ignore_files = ["UsdPCH.h"]  # Add more filenames here

    # Get headers and update TOML
    headers = get_header_files(root_path, ignore_folders, ignore_files)
    update_repo_toml(root_path, headers)
    print(f"Updated {root_path/'repo.toml'} with {len(headers)} header files (excluded {len(ignore_files)} files)")
