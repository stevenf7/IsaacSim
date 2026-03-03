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
"""Script to update changelogs across extensions.

Bumps the patch version in each extension's config/extension.toml and adds a
new entry to docs/CHANGELOG.md.  Validation and formatting of changelog files
is handled separately by tools/isaac/pre_merge/validate_changelog.py.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


def parse_toml(toml_str):
    """Very simple TOML parser for basic needs."""
    result = {}
    current_section = result

    for line in toml_str.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section = result
            if "." in section_name:
                parts = section_name.split(".")
                for part in parts:
                    if part not in current_section:
                        current_section[part] = {}
                    current_section = current_section[part]
            else:
                if section_name not in result:
                    result[section_name] = {}
                current_section = result[section_name]
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.isdigit():
                value = int(value)
            elif value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            current_section[key] = value

    return result


try:
    import tomli as toml_reader
except ImportError:
    try:
        import tomlkit as toml_reader
    except ImportError:

        class TomliWrapper:
            @staticmethod
            def load(file_obj):
                data = file_obj.read()
                if isinstance(data, bytes):
                    data = data.decode()
                return parse_toml(data)

        toml_reader = TomliWrapper()


class ChangelogManager:
    """Bump extension versions and add changelog entries."""

    def __init__(
        self,
        verbose: bool = True,
        check_modified_branch: Optional[str] = None,
        force: bool = False,
    ):
        self.verbose = verbose
        self.check_modified_branch = check_modified_branch
        self.force = force

    def process_extensions(self, root_folder: str, changelog_message: Optional[str] = None) -> Dict[str, List[str]]:
        """Walk *root_folder*, bump versions and add changelog entries.

        Args:
            root_folder: Root directory to search for extensions.
            changelog_message: Message to include in each new changelog entry.

        Returns:
            Dict mapping extension names to a list of error strings (empty on
            success) or a ``(old_version, new_version)`` tuple.
        """
        results: Dict[str, Any] = {}

        for dirpath, dirnames, filenames in os.walk(root_folder):
            if "config" not in dirnames or "docs" not in dirnames:
                continue

            dirnames[:] = []
            extension_name = os.path.basename(dirpath)

            if self.verbose:
                print(f"\nProcessing extension: {extension_name}")
            else:
                print(f"Processing: {extension_name}")

            results[extension_name] = []
            version_info = None

            try:
                should_process, error_message = self._should_process_extension(dirpath, extension_name)
                if not should_process:
                    if error_message:
                        results[extension_name].append(error_message)
                        print(f"  Skipped {extension_name}: {error_message}")
                    else:
                        results[extension_name].append("Skipped due to filter conditions")
                        print(f"  Skipped {extension_name} due to filter conditions")
                    continue

                config_path = os.path.join(dirpath, "config")
                docs_path = os.path.join(dirpath, "docs")
                toml_path = os.path.join(config_path, "extension.toml")
                changelog_path = os.path.join(docs_path, "CHANGELOG.md")

                rel_toml_path = os.path.relpath(toml_path, root_folder)
                rel_changelog_path = os.path.relpath(changelog_path, root_folder)

                if not self._validate_paths(toml_path, changelog_path, rel_toml_path, rel_changelog_path):
                    continue

                if changelog_message is not None:
                    version_result = self._update_extension_version(toml_path, rel_toml_path)
                    if version_result:
                        old_version, new_version = version_result
                        version_info = (old_version, new_version)
                        self._update_changelog_file(changelog_path, rel_changelog_path, new_version, changelog_message)
                    else:
                        results[extension_name].append(f"Failed to update version in {rel_toml_path}")

                if not results[extension_name]:
                    version_display = f" ({version_info[0]} -> {version_info[1]})" if version_info else ""
                    print(f"  Extension {extension_name} processed successfully{version_display}")
                    results[extension_name] = version_info if version_info else []

            except Exception as e:
                error_msg = f"Error processing extension: {str(e)}"
                results[extension_name].append(error_msg)
                print(f"  {extension_name}: {error_msg}")

        return results

    def _should_process_extension(self, dirpath: str, extension_name: str = None) -> tuple:
        """Check all conditional requirements for processing."""
        if self.check_modified_branch:
            git_status, git_message = self._has_git_changes(dirpath, extension_name)
            if not git_status:
                if git_message and "behind" in git_message:
                    return False, git_message
                return False, f"No uncommitted changes vs {self.check_modified_branch} branch"
        return True, None

    def _has_git_changes(self, dirpath: str, extension_name: str = None) -> tuple:
        """Check if directory has changes against the specified branch."""
        branch = self.check_modified_branch
        try:
            if "/" in branch:
                remote, remote_branch = branch.split("/", 1)
                subprocess.run(["git", "fetch", remote, remote_branch], capture_output=True, text=True)

                if not self.force:
                    local_branch = remote_branch
                    status_cmd = subprocess.run(
                        ["git", "rev-list", "--count", f"{local_branch}..{branch}"], capture_output=True, text=True
                    )
                    behind_count = status_cmd.stdout.strip()
                    if behind_count and behind_count.isdigit() and int(behind_count) > 0:
                        error_msg = (
                            f"Local {local_branch} branch is {behind_count} commits behind {branch}. "
                            f"Please pull latest changes or use --force to skip this check."
                        )
                        if self.verbose:
                            print(f"  {error_msg}")
                        return False, error_msg

            result = subprocess.run(["git", "diff", "--quiet", branch, "--", dirpath], capture_output=True, text=True)
            if result.returncode == 0:
                if self.verbose:
                    print(f"  No uncommitted changes vs {branch} branch")
                return False, None
            return True, None
        except Exception as e:
            error_msg = f"Git check failed: {str(e)}"
            if self.verbose:
                print(f"  {error_msg}")
            return False, error_msg

    def _validate_paths(self, toml_path: str, changelog_path: str, rel_toml_path: str, rel_changelog_path: str) -> bool:
        """Validate required files exist."""
        if not os.path.exists(toml_path):
            if self.verbose:
                print(f"  Missing extension.toml at {toml_path}")
            return False
        if not os.path.exists(changelog_path):
            if self.verbose:
                print(f"  Missing CHANGELOG.md at {changelog_path}")
            return False
        return True

    def _update_extension_version(self, toml_path: str, rel_toml_path: str) -> Optional[Tuple[str, str]]:
        """Update version in extension.toml and return old and new versions."""
        try:
            with open(toml_path, "r") as f:
                content = f.read()

            with open(toml_path, "rb") as f:
                data = toml_reader.load(f)

            package = data.get("package", {})
            version_str = package.get("version", "")

            if not version_str:
                if self.verbose:
                    print(f"  Missing 'package.version' in {rel_toml_path}")
                return None

            try:
                parts = list(map(int, version_str.split(".")))
                if len(parts) != 3:
                    raise ValueError
            except ValueError:
                if self.verbose:
                    print(f"  Invalid version format '{version_str}' in {rel_toml_path}, expected X.Y.Z")
                return None

            old_version = version_str
            parts[-1] += 1
            new_version = ".".join(map(str, parts))

            version_pattern = re.compile(r'(version\s*=\s*")([^"]+)(")')
            match = version_pattern.search(content)
            if not match:
                if self.verbose:
                    print(f"  Could not find version pattern in {rel_toml_path}")
                return None

            updated_content = content[: match.start(2)] + new_version + content[match.end(2) :]

            with open(toml_path, "w") as f:
                f.write(updated_content)

            if self.verbose:
                print(f"  Version updated in {rel_toml_path}: {version_str} -> {new_version}")
            return (old_version, new_version)

        except Exception as e:
            if self.verbose:
                print(f"  Failed to update version in {rel_toml_path}: {str(e)}")
            return None

    def _update_changelog_file(
        self, changelog_path: str, rel_changelog_path: str, new_version: str, changelog_message: str
    ) -> List[str]:
        """Add new entry to changelog."""
        try:
            with open(changelog_path, "r") as f:
                content = f.read()

            changelog_header = "# Changelog"
            if changelog_header not in content:
                if self.verbose:
                    print(f"  Changelog header not found in {rel_changelog_path}")
                return None

            today = datetime.date.today().strftime("%Y-%m-%d")
            default_message = "Update extension description and add extension specific test settings"
            message = changelog_message or default_message

            new_entry = f"\n## [{new_version}] - {today}\n" "### Changed\n" f"- {message}\n"

            updated_content = content.replace(changelog_header, f"{changelog_header}{new_entry}", 1)

            with open(changelog_path, "w") as f:
                f.write(updated_content)

            if self.verbose:
                print(f"  Changelog updated in {rel_changelog_path} with version {new_version}")

            return updated_content.split("\n")

        except Exception as e:
            if self.verbose:
                print(f"  Failed to update changelog in {rel_changelog_path}: {str(e)}")

        return None


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict[str, Any]) -> callable:
    """Setup function for the repo tool."""
    tool_config = config.get("repo_update_changelogs", {})

    parser.add_argument(
        "--message",
        "-m",
        help="Custom changelog message (default: Update extension description and add extension specific test settings)",
    )
    parser.add_argument(
        "--check-modified",
        nargs="?",
        const="origin/develop",
        default=tool_config.get("check_modified", None),
        metavar="BRANCH",
        help="Only update extensions with changes vs specified branch (default: origin/develop)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        default=tool_config.get("force", False),
        help="Force update even if local branch is behind the specified branch",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=tool_config.get("verbose", False), help="Enable verbose output"
    )

    extensions_dirs_default = tool_config.get("extensions_dir", ["source/extensions"])
    if isinstance(extensions_dirs_default, str):
        extensions_dirs_default = [extensions_dirs_default]

    parser.add_argument(
        "--extensions-dir",
        action="append",
        default=None,
        help=f"Directory containing extensions (can be specified multiple times, default: {extensions_dirs_default})",
    )

    parser.set_defaults(extensions_dir_default=extensions_dirs_default)

    return run_repo_tool


def run_repo_tool(args: argparse.Namespace, config: Dict[str, Any]) -> int:
    """Run the changelog update tool in repo mode."""
    if args.extensions_dir is None:
        args.extensions_dir = getattr(args, "extensions_dir_default", ["source/extensions"])

    manager = ChangelogManager(
        verbose=args.verbose,
        check_modified_branch=args.check_modified,
        force=args.force,
    )

    error_count = 0
    success_count = 0
    all_results: Dict[str, Any] = {}

    for extensions_dir in args.extensions_dir:
        full_extensions_dir = os.path.join(config.get("root", "."), extensions_dir)

        if args.verbose:
            print(f"\nProcessing extensions in: {full_extensions_dir}")

        results = manager.process_extensions(full_extensions_dir, args.message)
        all_results.update(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful_extensions = []
    extensions_with_errors = []

    for ext_name, errors in all_results.items():
        if not errors or not isinstance(errors, list) or not errors:
            success_count += 1
            version_info = errors if isinstance(errors, tuple) and len(errors) == 2 else None
            successful_extensions.append((ext_name, version_info))
        else:
            extensions_with_errors.append((ext_name, errors))
            error_count += len(errors)

    for ext_name, version_info in successful_extensions:
        version_display = f" ({version_info[0]} -> {version_info[1]})" if version_info else ""
        print(f"Extension '{ext_name}' processed successfully{version_display}")

    if extensions_with_errors:
        print("\nExtensions with issues:")
        for ext_name, errors in extensions_with_errors:
            changelog_path = f"{ext_name}/docs/CHANGELOG.md"
            print(
                f"Extension '{ext_name}' ({changelog_path}) had {len(errors)} issue{'s' if len(errors) != 1 else ''}:"
            )
            for error in errors:
                print(f"  - {error}")

    total_count = len(all_results)
    failed_count = total_count - success_count
    print(f"\nProcessed {total_count} extensions: {success_count} successful, {failed_count} with issues")

    if error_count > 0:
        print(f"Found {error_count} total issues")
        return 1
    else:
        print("All operations completed successfully!")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update changelogs across extensions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    run_tool = setup_repo_tool(parser, {"root": os.getcwd()})
    args = parser.parse_args()

    sys.exit(run_tool(args, {"root": os.getcwd()}))
