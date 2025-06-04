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

import os
import re
from collections import defaultdict
from pathlib import Path


def parse_doxygen_warnings(log_path, output_path):
    """Parse doxygen warnings from repo.log and write organized warnings to output file"""

    # Regex pattern to match warning lines with file paths, line numbers, and messages
    pattern = r"(\/[^:]+\.[h|cpp]+):(\d+): warning: (.+)"

    warnings_by_file = defaultdict(list)  # Dict to hold warnings grouped by file

    try:
        print(f"Parsing doxygen warnings from: {log_path}")

        with open(log_path, "r") as f:
            content = f.read()
            print(f"Read {len(content)} bytes from log file")

        # Find all matches
        matches = re.finditer(pattern, content)
        raw_count = 0

        for match in matches:
            file_path = match.group(1).strip()
            line_num = match.group(2)
            message = match.group(3).strip()

            # Store warning with line number and message
            warnings_by_file[file_path].append((line_num, message))
            raw_count += 1

        print(f"Found {raw_count} total warnings")
        print(f"Affecting {len(warnings_by_file)} unique files")

        # Sort files alphabetically
        sorted_files = sorted(warnings_by_file.keys())

        # Write organized output
        print(f"Writing organized warnings to: {output_path}")
        with open(output_path, "w") as f:
            f.write("Doxygen Documentation Warnings\n")
            f.write("============================\n\n")

            for file_path in sorted_files:
                f.write(f"\nFile: {file_path}\n")
                f.write("-" * (len(file_path) + 6) + "\n")

                # Sort warnings by line number
                warnings = sorted(warnings_by_file[file_path], key=lambda x: int(x[0]))

                for line_num, message in warnings:
                    f.write(f"Line {line_num}: {message}\n")

        print(f"\nProcessing complete!")
        print(f"Total warnings: {raw_count}")
        print(f"Warnings organized by {len(sorted_files)} files")
        print(f"Output written to: {output_path}")

    except FileNotFoundError:
        print(f"Error: Could not find {log_path}")
    except Exception as e:
        print(f"Error processing files: {e}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    repo_dir = script_dir.parent

    log_path = repo_dir / "_repo" / "repo.log"
    output_path = repo_dir / "doxygen_warnings.txt"

    parse_doxygen_warnings(log_path, output_path)
