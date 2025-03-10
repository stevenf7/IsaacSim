#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class ClangTidyFixer:
    def __init__(self, input_file=None, dry_run=False, root_dir=None):
        self.input_file = input_file
        self.dry_run = dry_run
        self.root_dir = root_dir or os.getcwd()
        self.verbose = True  # Add verbose mode to print more details

        # Track different types of issues
        self.identifier_renames = []  # (file_path, old_name, new_name, line_number)
        self.nullptr_replacements = []  # (file_path, line_number)
        self.processed_files = set()
        self.error_files = set()

        # Track success counts
        self.successful_renames = 0
        self.failed_renames = 0
        self.successful_nullptrs = 0
        self.failed_nullptrs = 0

    def normalize_path(self, file_path):
        """Normalize file paths from clang-tidy output to match the actual file system."""
        # Remove any build directory prefixes and normalize the path
        # This handles paths like /some/build/dir/../../../source/actual_path.cpp
        normalized_path = os.path.normpath(file_path)

        # Try to find the file - first check if it exists as-is
        if os.path.exists(normalized_path):
            return normalized_path

        # Try stripping common build directory components
        # Look for patterns like /_compiler/gmake2/something.plugin/../../../source/
        match = re.search(r"/_compiler/[^/]+/[^/]+/\.\./\.\./\.\./(.+)", normalized_path)
        if match:
            source_path = match.group(1)
            # Try relative to root dir
            candidate = os.path.join(self.root_dir, source_path)
            if os.path.exists(candidate):
                if self.verbose:
                    print(f"  Resolved path: {file_path} -> {candidate}")
                return candidate

        # If we're still here, try to find the file by its name in the source tree
        filename = os.path.basename(normalized_path)
        if self.verbose:
            print(f"  Trying to find {filename} in source tree...")

        # Use find command to locate the file
        try:
            cmd = ["find", self.root_dir, "-name", filename, "-type", "f"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                candidates = result.stdout.strip().split("\n")
                # Try to find the best match based on path components
                path_components = normalized_path.split(os.sep)
                for candidate in candidates:
                    if all(comp in candidate for comp in path_components[-3:]):
                        if self.verbose:
                            print(f"  Found match: {candidate}")
                        return candidate

                # If no good match, just use the first one found
                if self.verbose:
                    print(f"  Using first match found: {candidates[0]}")
                return candidates[0]
        except Exception as e:
            if self.verbose:
                print(f"  Error searching for file: {e}")

        # If all else fails, return the original path and let the caller handle the error
        return normalized_path

    def parse_clang_tidy_output(self):
        """Parse the clang-tidy output file to extract issues that need to be fixed."""
        print(f"Parsing clang-tidy output from {self.input_file}...")

        try:
            with open(self.input_file, "r") as f:
                content = f.read()

            # First, extract all file sections
            file_pattern = r"---\s+([^\n]+)\s+---\n(.*?)(?=---\s+|\Z)"
            file_matches = re.finditer(file_pattern, content, re.DOTALL)

            for file_match in file_matches:
                file_path = file_match.group(1).strip()
                file_content = file_match.group(2).strip()

                self.processed_files.add(file_path)

                # Check for errors in processing the file
                if "Error while processing" in file_content:
                    error_match = re.search(r"Error while processing ([^\n]+)", file_content)
                    if error_match:
                        error_file = error_match.group(1).strip()
                        self.error_files.add(error_file)

                # For identifier naming issues: Match the warning, code line, carets, and suggestion
                id_pattern = r"(?:source/extensions/[^:]+):(\d+):\d+: warning: invalid case style for ([^\']+) \'([^\']+)\' \[readability-identifier-naming\][^\n]*\n[^\n]*\n\s+\^[~]*\s*\n\s+([^\n]+)"
                id_matches = re.finditer(id_pattern, file_content, re.DOTALL)

                for id_match in id_matches:
                    line_num, issue_type, old_name, new_name = id_match.groups()

                    # Extract the actual source file path from the error message
                    file_path_match = re.search(r"(source/extensions/[^:]+):", id_match.group(0))
                    if file_path_match:
                        issue_file = file_path_match.group(1)
                        self.identifier_renames.append((issue_file, old_name, new_name, int(line_num)))
                        if self.verbose:
                            print(
                                f"  Found identifier naming issue: '{old_name}' -> '{new_name}' in {issue_file}:{line_num}"
                            )

                # For nullptr issues
                nullptr_pattern = r"(source/extensions/[^:]+):(\d+):\d+: warning: use nullptr \[modernize-use-nullptr\]"
                nullptr_matches = re.finditer(nullptr_pattern, file_content)

                for nullptr_match in nullptr_matches:
                    issue_file, line_num = nullptr_match.groups()
                    self.nullptr_replacements.append((issue_file, int(line_num)))

            print(f"Found {len(self.identifier_renames)} identifier naming issues")
            print(f"Found {len(self.nullptr_replacements)} nullptr issues")
            print(f"Total files processed: {len(self.processed_files)}")
            print(f"Files with errors: {len(self.error_files)}")

            # Print actual naming issues for debugging
            if self.verbose and self.identifier_renames:
                print("\nIdentifier naming issues found:")
                for file_path, old_name, new_name, line_num in self.identifier_renames:
                    print(f"  {file_path}:{line_num} - '{old_name}' -> '{new_name}'")

        except Exception as e:
            print(f"Error parsing clang-tidy output: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def fix_identifier_naming(self):
        """Fix identifier naming issues based on the recommendations."""
        print("Fixing identifier naming issues...")

        # Group by file to reduce the number of file operations
        file_to_renames = defaultdict(list)
        for file_path, old_name, new_name, line_num in self.identifier_renames:
            # Fix the redundant m_m prefix that clang-tidy suggests
            if new_name.startswith("m_m"):
                # Extract the part after 'm_m' and make sure the first letter is lowercase
                variable_part = new_name[3:]
                if variable_part and variable_part[0].isupper():
                    # If the original name started with 'm', then we're converting mName to m_mName
                    # We should convert it to m_name instead (lowercase the first letter after m_)
                    if old_name.startswith("m") and len(old_name) > 1 and old_name[1].isupper():
                        # Convert first char after prefix to lowercase
                        variable_part = variable_part[0].lower() + variable_part[1:]
                new_name = "m_" + variable_part
                print(
                    f"  Corrected redundant prefix: Changed suggested '{old_name}' → 'm_m{variable_part}' to '{old_name}' → '{new_name}'"
                )

            # For global variables, if suggestion is g_gName, correct to g_name
            if new_name.startswith("g_g"):
                variable_part = new_name[3:]
                if old_name.startswith("g") and not old_name.startswith("g_"):
                    new_name = "g_" + variable_part
                    print(f"  Corrected redundant prefix: Changed suggested '{old_name}' → '{new_name}'")

            normalized_path = self.normalize_path(file_path)
            file_to_renames[normalized_path].append((old_name, new_name, line_num))

        for file_path, renames in file_to_renames.items():
            if not os.path.exists(file_path):
                print(f"  Warning: File {file_path} does not exist, skipping")
                self.failed_renames += len(renames)
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                original_content = content
                fixed_content = content

                for old_name, new_name, line_num in renames:
                    print(f"  Renaming '{old_name}' to '{new_name}' in {file_path}")

                    # This is a basic replacement strategy that might need refinement for complex cases
                    if self.dry_run:
                        continue

                    # Use a more targeted approach to prevent partial matches
                    pattern = r"\b" + re.escape(old_name) + r"\b"
                    fixed_content = re.sub(pattern, new_name, fixed_content)

                # Check if any changes were made
                if fixed_content == original_content:
                    print(f"  Warning: No changes were made to {file_path} despite {len(renames)} rename requests")

                    # Try to get some context for debugging
                    if self.verbose and len(renames) > 0:
                        old_name, new_name, line_num = renames[0]
                        try:
                            with open(file_path, "r") as f:
                                lines = f.readlines()
                                context_start = max(0, line_num - 2)
                                context_end = min(len(lines), line_num + 2)
                                print(f"  Context (lines {context_start+1}-{context_end}):")
                                for i in range(context_start, context_end):
                                    print(f"    {i+1}: {lines[i].rstrip()}")

                                # Recreate the pattern here to avoid the scoping issue
                                debug_pattern = r"\b" + re.escape(old_name) + r"\b"
                                print(f"  Looking for pattern: '{debug_pattern}'")

                                # Try a direct string search for more insight
                                found = old_name in lines[line_num - 1]
                                print(
                                    f"  Direct string search for '{old_name}' in line {line_num}: {'Found' if found else 'Not found'}"
                                )

                                # Check if there might be whitespace or encoding issues
                                if not found:
                                    line_bytes = lines[line_num - 1].encode("utf-8")
                                    print(f"  Line bytes: {line_bytes}")
                                    print(f"  Old name bytes: {old_name.encode('utf-8')}")
                        except Exception as e:
                            print(f"  Error getting context: {e}")

                    self.failed_renames += len(renames)
                else:
                    if not self.dry_run:
                        with open(file_path, "w") as f:
                            f.write(fixed_content)
                        print(f"  Successfully updated {file_path}")
                        self.successful_renames += len(renames)
            except Exception as e:
                print(f"  Error fixing {file_path}: {e}")
                self.failed_renames += len(renames)

    def fix_nullptr_issues(self):
        """Replace '0' with 'nullptr' as recommended."""
        print("Fixing nullptr issues...")

        file_to_lines = defaultdict(list)
        for file_path, line_num in self.nullptr_replacements:
            normalized_path = self.normalize_path(file_path)
            file_to_lines[normalized_path].append(line_num)

        for file_path, line_nums in file_to_lines.items():
            if not os.path.exists(file_path):
                print(f"  Warning: File {file_path} does not exist, skipping")
                self.failed_nullptrs += len(line_nums)
                continue

            try:
                with open(file_path, "r") as f:
                    lines = f.readlines()

                modified = False
                for line_num in line_nums:
                    if line_num <= 0 or line_num > len(lines):
                        self.failed_nullptrs += 1
                        continue

                    # Adjust for 0-indexed list
                    line_idx = line_num - 1
                    line = lines[line_idx]

                    # Replace '0' with 'nullptr' but be careful not to replace other 0s
                    # We're looking for patterns like 'return 0;' or '= { 0 };'
                    if "return 0;" in line:
                        new_line = line.replace("return 0;", "return nullptr;")
                        lines[line_idx] = new_line
                        modified = True
                        print(f"  Replacing '0' with 'nullptr' in {file_path}:{line_num}")
                        self.successful_nullptrs += 1
                    elif re.search(r"=\s*{\s*0\s*}", line):
                        new_line = re.sub(r"=\s*{\s*0\s*}", "= { nullptr }", line)
                        lines[line_idx] = new_line
                        modified = True
                        print(f"  Replacing '0' with 'nullptr' in {file_path}:{line_num}")
                        self.successful_nullptrs += 1
                    else:
                        print(f"  Warning: Could not find '0' to replace with 'nullptr' in {file_path}:{line_num}")
                        if self.verbose:
                            print(f"    Line content: {line.strip()}")
                        self.failed_nullptrs += 1

                if not self.dry_run and modified:
                    with open(file_path, "w") as f:
                        f.writelines(lines)
                    print(f"  Successfully updated {file_path}")
            except Exception as e:
                print(f"  Error fixing {file_path}: {e}")
                self.failed_nullptrs += len(line_nums)

    def run(self):
        """Execute the fixing process."""
        if not os.path.exists(self.input_file):
            print(f"Input file not found: {self.input_file}")
            return False

        self.parse_clang_tidy_output()

        if self.dry_run:
            print("DRY RUN: No changes will be made to files")

        self.fix_identifier_naming()
        # self.fix_nullptr_issues()

        print("\nSummary:")
        print(f"  Files processed: {len(self.processed_files)}")
        print(f"  Files with errors: {len(self.error_files)}")
        print(f"  Identifier naming issues found: {len(self.identifier_renames)}")
        print(f"    - Successfully renamed: {self.successful_renames}")
        print(f"    - Failed to rename: {self.failed_renames}")
        print(f"  nullptr issues found: {len(self.nullptr_replacements)}")
        print(f"    - Successfully fixed: {self.successful_nullptrs}")
        print(f"    - Failed to fix: {self.failed_nullptrs}")

        if self.failed_renames > 0 or self.failed_nullptrs > 0:
            print("\nSome changes could not be applied. Possible reasons:")
            print("  1. Files could not be found (check paths)")
            print("  2. Files have already been modified")
            print("  3. Insufficient permissions to modify files")
            if self.dry_run:
                print("  4. Dry run mode was enabled (no actual changes were made)")

        return True


def main():
    parser = argparse.ArgumentParser(description="Fix clang-tidy issues in a codebase")
    parser.add_argument("input_file", help="Path to the clang-tidy output file")
    parser.add_argument("--dry-run", action="store_true", help="Do not make any changes, just print what would be done")
    parser.add_argument("--root-dir", default=None, help="Root directory of the codebase (default: current directory)")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output for debugging")

    args = parser.parse_args()

    fixer = ClangTidyFixer(input_file=args.input_file, dry_run=args.dry_run, root_dir=args.root_dir)
    fixer.verbose = args.verbose

    success = fixer.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
