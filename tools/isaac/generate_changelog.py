# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import datetime
import glob
import logging
import os
import re
import subprocess
from collections import OrderedDict
from pprint import pprint
from typing import Callable, Dict, List, Set, Tuple

import omni.repo.man
import toml

logger = logging.getLogger(__name__)


def parse_version(line: str):
    """
    Parse version in an extension changelog file
    Try parse line as a version, assuming it will look like ' [2.3.1] - 2020-09-30 '
    This is copied from /kit/source/extensions/omni.kit.registry.nucleus/omni/kit/registry/nucleus/changelog_parser.py
    """
    try:
        line = line.lstrip(" #")
        m = re.match(r"\[?(?P<version>[^(\]|\s)]+)\]? - (?P<release_date>\d{4}-\d{1,2}-\d{1,2})$", line)
        if m:
            return (m.group("version"), (datetime.datetime.strptime(m.group("release_date"), "%Y-%m-%d").date()))

        m = re.match(r"\[(?P<version>Unreleased)\]$", line)
        if m:
            return (m.group("version"), None)
    except Exception as e:
        print(line)
        print(e)

    return None


# Canonical changelog categories and the order they should appear in the output.
CATEGORY_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "General"]
_CATEGORY_ALIASES = {c.lower(): c for c in CATEGORY_ORDER}


def normalize_category(name: str) -> str:
    """Normalize a changelog category heading to its canonical capitalization."""
    cleaned = name.lstrip("# ").strip()
    return _CATEGORY_ALIASES.get(cleaned.lower(), cleaned or "General")


def _empty_content() -> Dict[str, List[str]]:
    return {c: [] for c in CATEGORY_ORDER}


def parse_changelog(change: str) -> Tuple[str, datetime.date, List]:
    """Parse an extension changelog content and yield tuples of version, date and list of strings"""
    version = None
    date = None
    content = _empty_content()
    category = "General"

    for line in change.splitlines():
        res = parse_version(line)
        if res:
            yield version, date, content
            version, date = res
            content = _empty_content()
            category = "General"
        else:
            if len(line) > 0:
                if line.startswith("###"):
                    category = normalize_category(line)
                    if category not in content:
                        content[category] = []
                else:
                    if category not in content:
                        content[category] = []
                    # Strip a leading markdown bullet ("- ") without corrupting trailing characters.
                    entry = line.strip()
                    if entry.startswith("- "):
                        entry = entry[2:]
                    elif entry.startswith("-"):
                        entry = entry[1:]
                    content[category].append(entry.strip())

    if version:
        yield version, date, content


def get_local_extension_paths(package_build_root: str) -> Dict[str, List[str]]:
    """
    Find all of the local extension paths
    NOTE: looking in "exts" might be making some Create specific assumptions
    NOTE: There can be multiple versions of the same extension in the folder
    return a dict of extension_name-> path
    """
    extension_roots = ["exts", "extscache"]
    local_extension_paths = {}
    for root in extension_roots:
        ext_dir_path_root = os.path.join(package_build_root, root)
        if not os.path.exists(ext_dir_path_root):
            continue
        ext_dir_paths = os.listdir(ext_dir_path_root)
        ext_dir_paths = [p for p in ext_dir_paths if p.startswith("omni.") != -1]

        for ext_path in ext_dir_paths:
            name_ver = ext_path.split("-")
            path_list = local_extension_paths.setdefault(name_ver[0], [])
            path_list.append(os.path.join(package_build_root, root, ext_path))
    return local_extension_paths


def read_extension_data_from_app_kitfiles(repo_root: str) -> Dict[str, str]:
    """
    This really only works for Apps like Create where the extension versioning
    info is "baked" into the Kit files

    return a dictionary of {extension_name: version}
    """

    # Load all of the Kit files and read the extension versions from them...
    app_folder = os.path.join(repo_root, "source", "apps")
    kit_files = glob.glob(app_folder + "/*.kit")
    ext_to_version_map = {}
    print(f"processing {len(kit_files)} kit files")
    for kit_filename in kit_files:
        kit_file = open(os.path.join(repo_root, "apps", kit_filename))
        kit_text = kit_file.read()
        index = kit_text.find("# BEGIN GENERATED PART")
        if index == -1:
            print(f"skipping kit file {kit_filename} as can't find generated part")
            continue
        kit_text = kit_text[index:]
        the_new_data = toml.loads(kit_text)

        """
        we're reading a list of items like:
        "omni.anim.curve-102.1.4",
	    "omni.anim.skelJoint-102.1.0"
        """
        extension_list = the_new_data["settings"]["app"]["exts"]["enabled"]
        for ext in extension_list:
            name_ver = ext.split("-")
            ext_to_version_map[name_ver[0]] = name_ver[1]

    # return a dict of extension name : version
    return ext_to_version_map


def get_extension_diff_data(
    changelog_path: str, old_date: datetime.date, new_date: datetime.date
) -> Tuple[List[Tuple[str, Dict[str, List[str]]]], bool, str]:
    """
    Returns a tuple of:
      - a list of ``(version, content)`` tuples for each version released within the range
      - ``is_new``: True when the extension has entries in range but none dated before ``old_date``
        (i.e. it first appeared during this range).
      - ``prior_version``: the most recent version dated before ``old_date`` (i.e. the version that
        was current at the start of the range), or ``None`` if the extension had no prior release.
    """

    in_range = []
    prior_version = None
    prior_date = None

    if os.path.exists(changelog_path):
        with open(changelog_path) as changelog_file:
            changelog_str = changelog_file.read()
            # parses each entry
            for v, d, content in parse_changelog(changelog_str):
                if d is None:
                    continue
                if old_date <= d <= new_date:
                    in_range.append((v, content))
                elif d < old_date:
                    # Track the latest release that predates the range start.
                    if prior_date is None or d > prior_date:
                        prior_date = d
                        prior_version = v

    is_new = len(in_range) > 0 and prior_version is None

    return in_range, is_new, prior_version


def generate_extension_diff_report(
    name: str, changelog_path: str, old_date: datetime.date, new_date: datetime.date, format_: str
) -> None:
    """
    Generate a changelog report for a specific extension by reading a range of versions
    from its CHANGELOG.md file.

    Args:
        name (str): Name of the extension.
        changelog_path (str): Path to the extension's CHANGELOG.md file.
        old_date (datetime.date): Start date for the changelog range.
        new_date (datetime.date): End date for the changelog range.
        format_ (str): Output format, either "md" (Markdown) or "rst" (reStructuredText).

    The report is printed directly to stdout.
    """
    # Get the changelog entries, whether this is a new extension, and the version current at range start.
    results, is_new, prior_version = get_extension_diff_data(changelog_path, old_date, new_date)

    # Nothing changed in range, nothing to report.
    if len(results) == 0:
        return

    # Build the extension header showing the version at the start of the range -> the current version.
    # results are newest-first (CHANGELOG.md order), so the first entry is the current version.
    current_version = results[0][0]
    if prior_version is None or prior_version == current_version:
        version_range = f"{current_version}"
    else:
        version_range = f"{prior_version} -> {current_version}"

    report = f"\n- **{name}** ({version_range})"

    # If this is a new extension, emit a single "New extension" note.
    if is_new:
        report += f"\n  - New extension" if format_ == "md" else "\n\n    - New extension"
        print(report)
        return

    # Aggregate all changelog entries by their category, preserving order of appearance.
    all_entries: Dict[str, List[str]] = {}
    for _version, content in results:
        for change_type, values in content.items():
            for value in values:
                all_entries.setdefault(change_type, []).append(value)

    # Emit categories in the canonical order, then any unexpected categories alphabetically.
    ordered_categories = [c for c in CATEGORY_ORDER if all_entries.get(c)]
    ordered_categories += sorted(c for c in all_entries if c not in CATEGORY_ORDER and all_entries.get(c))

    for change_type in ordered_categories:
        values = sorted(all_entries[change_type])
        if not values:
            continue
        report += f"\n  - {change_type}" if format_ == "md" else f"\n\n    - {change_type}\n"
        for change in values:
            report += f"\n    - {change}" if format_ == "md" else f"\n      - {change}"

    print(report)


def generate_extscache_diff_report(
    extscache_paths: List[str], range: Dict, format_: str, merge_extscache_sections: bool
):
    """Generate extscache report from .kit files"""
    for path in extscache_paths:
        try:
            cmd = ["git", "diff", "-U0", range[0]["commit"], range[1]["commit"], "--", path]
            omni.repo.man.print_log(f"Executing: {' '.join(cmd)}", logging.INFO)
            output = subprocess.check_output(cmd).decode()
        except subprocess.CalledProcessError as e:
            omni.repo.man.print_log(str(e), logging.ERROR)
            exit()

        data = {"kit": {}, "dependencies": {}, "exact_version_dependencies": {}, "version_lock_dependencies": {}}
        for line in output.split("\n")[4:]:
            if line.startswith("@@"):
                continue
            # parse: -"omni.replicator.core" = {version = "1.11.12", exact = true}
            if "version =" in line:
                status = line[:2]
                if status not in ['+"', '-"']:
                    omni.repo.man.print_log(f"Skipping: {line}", logging.INFO)
                    continue
                extension_name = line.split(" = ")[0][2:-1]
                extension_version = line.split("version = ")[1].split('"')[1]
                if not extension_name in data["dependencies"]:
                    data["dependencies"][extension_name] = {}
                data["dependencies"][extension_name][status[0]] = extension_version
            # parse: -# Kit SDK Version: 106.0.1+release.126909.3a7abd1c.gl
            elif "Kit SDK Version:" in line:
                status = line[:2]
                if status not in ["+#", "-#"]:
                    omni.repo.man.print_log(f"Skipping: {line}", logging.INFO)
                    continue
                kit_version = line.split("Kit SDK Version: ")[1]
                data["kit"][status[0]] = kit_version
            # parse: -#      semantics.schema.property-1.0.3
            elif line.startswith("-# \t") or line.startswith("+# \t"):
                status = line[:2]
                if status not in ["+#", "-#"]:
                    omni.repo.man.print_log(f"Skipping: {line}", logging.INFO)
                    continue
                extension_name = line[4:].split("-")[0]
                extension_version = line[4:].split("-")[-1]
                if not extension_name in data["exact_version_dependencies"]:
                    data["exact_version_dependencies"][extension_name] = {}
                data["exact_version_dependencies"][extension_name][status[0]] = extension_version
            # parse: -       "omni.kit.converter.common-500.0.6"
            elif line.startswith('-\t"') or line.startswith('+\t"'):
                status = line[:2]
                if status not in ["+\t", "-\t"]:
                    omni.repo.man.print_log(f"Skipping: {line}", logging.INFO)
                    continue
                extension_name = line[3:].split("-")[0]
                extension_version = line[3:].split("-")[-1][:-2]
                if not extension_name in data["version_lock_dependencies"]:
                    data["version_lock_dependencies"][extension_name] = {}
                data["version_lock_dependencies"][extension_name][status[0]] = extension_version

        # sort dicts
        data["dependencies"] = OrderedDict(sorted(data["dependencies"].items()))
        data["exact_version_dependencies"] = OrderedDict(sorted(data["exact_version_dependencies"].items()))
        data["version_lock_dependencies"] = OrderedDict(sorted(data["version_lock_dependencies"].items()))

        # merge results to "dependencies"
        if merge_extscache_sections:
            # Merge all three dictionaries by combining version info (not overwriting).
            merged = {}

            # Order matters: the merge keeps the first value seen for each +/- status, so the
            # sections carrying fully-resolved exact versions (version lock and exact-version
            # dependencies, e.g. "209.4.0") are processed before the plain dependency
            # declarations, whose versions may be semver ranges (e.g. "~209.4"). This ensures the
            # report shows the concrete resolved version rather than the range specifier.
            for section_data in [
                data["version_lock_dependencies"],
                data["exact_version_dependencies"],
                data["dependencies"],
            ]:
                for ext_name, versions in section_data.items():
                    if ext_name not in merged:
                        merged[ext_name] = {}
                    # Merge version info - if same key exists, keep both values
                    for status, version in versions.items():
                        if status not in merged[ext_name]:
                            merged[ext_name][status] = version
                        # If status already exists with different version, keep the first one
                        # (the more precise resolved version, given the section ordering above).

            data["dependencies"] = OrderedDict(sorted(merged.items()))
            data["exact_version_dependencies"] = {}
            data["version_lock_dependencies"] = {}

        report = ""

        # kit
        if data["kit"]:
            report += "# Kit SDK Version\n" if format_ == "md" else "Kit SDK Version\n===============\n"
            v = data["kit"]
            # changed
            if "+" in list(v.keys()) and "-" in list(v.keys()):
                report += f"\nChanged: {v['-']} -> {v['+']}\n"
            # added
            elif "+" in list(v.keys()):
                report += f"\nAdded: {v['+']}\n"
            # removed
            elif "-" in list(v.keys()):
                report += f"\nRemoved: {v['-']}\n"

        if data["dependencies"] or data["exact_version_dependencies"] or data["version_lock_dependencies"]:
            report += (
                "\n# Cached extensions (Kit)\n"
                if format_ == "md"
                else "\nCached extensions (Kit)\n=======================\n"
            )

        # dependencies
        if data["dependencies"]:
            extension_added = []
            extension_changed = []
            extension_removed = []

            for k, v in data["dependencies"].items():
                # changed
                if "+" in list(v.keys()) and "-" in list(v.keys()):
                    # Only show as changed if versions are actually different
                    if v["-"] != v["+"]:
                        extension_changed.append(f"{k}: {v['-']} -> {v['+']}")
                # added
                elif "+" in list(v.keys()):
                    extension_added.append(f"{k}: {v['+']}")
                # removed
                elif "-" in list(v.keys()):
                    extension_removed.append(f"{k}: {v['-']}")

            report += "\n## Dependencies\n" if format_ == "md" else "\nDependencies\n------------\n"
            if len(extension_added):
                report += "\n### Added\n" if format_ == "md" else "\nAdded\n^^^^^\n"
                for extension in extension_added:
                    report += f"- {extension}\n"
            if len(extension_removed):
                report += "\n### Removed\n" if format_ == "md" else "\nRemoved\n^^^^^^^\n"
                for extension in extension_removed:
                    report += f"- {extension}\n"
            if len(extension_changed):
                report += "\n### Changed\n" if format_ == "md" else "\nChanged\n^^^^^^^\n"
                for extension in extension_changed:
                    report += f"- {extension}\n"

        # exact version dependencies
        if data["exact_version_dependencies"]:
            extension_added = []
            extension_changed = []
            extension_removed = []

            for k, v in data["exact_version_dependencies"].items():
                # changed
                if "+" in list(v.keys()) and "-" in list(v.keys()):
                    # Only show as changed if versions are actually different
                    if v["-"] != v["+"]:
                        extension_changed.append(f"{k}: {v['-']} -> {v['+']}")
                # added
                elif "+" in list(v.keys()):
                    extension_added.append(f"{k}: {v['+']}")
                # removed
                elif "-" in list(v.keys()):
                    extension_removed.append(f"{k}: {v['-']}")

            report += (
                "\n## Exact Version Dependencies\n"
                if format_ == "md"
                else "\nExact Version Dependencies\n--------------------------\n"
            )
            if len(extension_added):
                report += "\n### Added\n" if format_ == "md" else "\nAdded\n^^^^^\n"
                for extension in extension_added:
                    report += f"- {extension}\n"
            if len(extension_removed):
                report += "\n### Removed\n" if format_ == "md" else "\nRemoved\n^^^^^^^\n"
                for extension in extension_removed:
                    report += f"- {extension}\n"
            if len(extension_changed):
                report += "\n### Changed\n" if format_ == "md" else "\nChanged\n^^^^^^^\n"
                for extension in extension_changed:
                    report += f"- {extension}\n"

        # version lock dependencies
        if data["version_lock_dependencies"]:
            extension_added = []
            extension_changed = []
            extension_removed = []

            for k, v in data["version_lock_dependencies"].items():
                # changed
                if "+" in list(v.keys()) and "-" in list(v.keys()):
                    # Only show as changed if versions are actually different
                    if v["-"] != v["+"]:
                        extension_changed.append(f"{k}: {v['-']} -> {v['+']}")
                # added
                elif "+" in list(v.keys()):
                    extension_added.append(f"{k}: {v['+']}")
                # removed
                elif "-" in list(v.keys()):
                    extension_removed.append(f"{k}: {v['-']}")

            report += (
                "\n## Version Lock for all Dependencies\n"
                if format_ == "md"
                else "\nVersion Lock for all Dependencies\n---------------------------------\n"
            )
            if len(extension_added):
                report += "\n### Added\n" if format_ == "md" else "\nAdded\n^^^^^\n"
                for extension in extension_added:
                    report += f"- {extension}\n"
            if len(extension_removed):
                report += "\n### Removed\n" if format_ == "md" else "\nRemoved\n^^^^^^^\n"
                for extension in extension_removed:
                    report += f"- {extension}\n"
            if len(extension_changed):
                report += "\n### Changed\n" if format_ == "md" else "\nChanged\n^^^^^^^\n"
                for extension in extension_changed:
                    report += f"- {extension}\n"

        print()
        print(report)


def get_range(range: str):
    def parse(token: str):
        def _get_commit_date(commit):
            try:
                output = subprocess.check_output(["git", "show", "--no-patch", "--pretty=reference", value]).decode()
                return output.split("\n")[0][:-1].split(" ")[-1]
            except subprocess.CalledProcessError:
                pass
            return None

        if token.count(":") == 1:
            key, value = token.split(":")
            # commit
            if key.lower() == "commit":
                # get date from commit ID
                date = _get_commit_date(value)
                if not date:
                    omni.repo.man.print_log(f"Invalid commit ID ({value})", logging.ERROR)
                    exit()
                return {"commit": value, "date": date}
            # date
            elif key.lower() == "date":
                return {"commit": f"HEAD@{{{value} ago}}", "date": value}
            # tag
            elif key.lower() == "tag":
                commit = None
                # get commit ID from tag
                try:
                    output = subprocess.check_output(["git", "rev-list", "-n", "1", value]).decode()
                    if len(output):
                        commit = output[:7]
                except subprocess.CalledProcessError:
                    commit = None
                # get available tags
                if not commit:
                    try:
                        output = subprocess.check_output(["git", "show-ref", "--tags"]).decode()
                        output = [line.split("refs/tags/")[1] for line in output.split("\n") if "refs/tags/" in line]
                        omni.repo.man.print_log(
                            f"Invalid range tag ({token}). Available tags: {', '.join(output)}", logging.ERROR
                        )
                    except subprocess.CalledProcessError:
                        pass
                    exit()
                # get date from commit ID
                date = _get_commit_date(value)
                if not date:
                    omni.repo.man.print_log(f"Invalid commit ID ({value})", logging.ERROR)
                    exit()
                return {"commit": commit, "date": date}
        omni.repo.man.print_log(
            f"Invalid range format ({token}). Supported format is type:value (e.g.: commit:fc1ec839, tag:1.0.0, date:2024-01-31)",
            logging.ERROR,
        )
        exit()

    range = range.split("..")
    return (
        parse(range[0]),
        parse(range[1]) if len(range) == 2 else {"commit": "HEAD", "date": datetime.date.today().isoformat()},
    )


def collect_extensions(home_paths: List[str], exts_exclude: Set[str]) -> List[Tuple[str, str]]:
    """
    Walk every configured extension root and collect ``(name, changelog_path)`` pairs.

    Directories without a ``config/extension.toml`` are skipped (e.g. dependency-only
    folders such as ``source/internal_extensions/deps``). Names are de-duplicated across
    roots (first occurrence wins) and the result is sorted alphabetically so the output
    remains a single flat list.
    """
    collected: Dict[str, str] = {}
    for home_path in home_paths:
        if not os.path.isdir(home_path):
            omni.repo.man.print_log(f"Skipping missing extension root: {home_path}", logging.WARNING)
            continue
        for entry in sorted(os.listdir(home_path)):
            if entry in exts_exclude or entry in collected:
                continue
            ext_dir = os.path.join(home_path, entry)
            if not os.path.isdir(ext_dir):
                continue
            # Only treat directories with an extension manifest as extensions.
            if not os.path.exists(os.path.join(ext_dir, "config", "extension.toml")):
                continue
            collected[entry] = os.path.join(ext_dir, "docs", "CHANGELOG.md")

    return sorted(collected.items())


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Generate changelog documentation"
    parser.add_argument(
        "--extscache",
        required=False,
        default=False,
        action="store_true",
        help="Generate extscache changelog",
    )
    parser.add_argument(
        "--changelog",
        required=False,
        default=False,
        action="store_true",
        help="Generate extensions changelog",
    )
    parser.add_argument(
        "-r",
        "--range",
        dest="range",
        required=False,
        help='Single (from) or pair (from..to) of commits/tags/dates prefixed with "commit:", "tag:", or "date:" respectively',
    )
    parser.add_argument(
        "--format",
        type=str,
        default="rst",
        choices=["rst", "md"],
        help="Output format: reStructuredText (rst) or Markdown (md)",
    )
    parser.add_argument(
        "--merge-extscache",
        required=False,
        default=False,
        action="store_true",
        help="Whether to merge the sections generated for the extscache changelog",
    )

    def run_repo_tool(options: Dict, config: Dict):
        # tool_config = config.get("repo_build", {})
        # print(config)
        tool_config = config["repo_generate_changelog"]

        # Accept either the new "home_paths" list or the legacy "home_path" string.
        home_paths = tool_config.get("home_paths")
        if not home_paths:
            legacy = tool_config.get("home_path")
            home_paths = [legacy] if legacy else []
        if isinstance(home_paths, str):
            home_paths = [home_paths]

        exts_exclude = set(tool_config.get("exts_exclude", []))

        # get range
        if options.range is None:
            omni.repo.man.print_log(f"Missing --range argument", logging.ERROR)
            parser.print_help()
            exit()
        range = get_range(options.range)
        omni.repo.man.print_log(f"Report range: {range}", logging.INFO)

        # If neither flag is specified, generate both (backward compatibility)
        generate_changelog = options.changelog or (not options.extscache and not options.changelog)
        generate_extscache = options.extscache or (not options.extscache and not options.changelog)

        # generate extscache report
        if generate_extscache:
            generate_extscache_diff_report(
                tool_config["extscache_paths"], range, options.format, options.merge_extscache
            )

        # generate extensions report
        if generate_changelog:
            print("# Extensions" if options.format == "md" else "Extensions\n==========")
            for name, changelog_path in collect_extensions(home_paths, exts_exclude):
                generate_extension_diff_report(
                    name,
                    changelog_path,
                    datetime.date.fromisoformat(range[0]["date"]),
                    datetime.date.fromisoformat(range[1]["date"]),
                    options.format,
                )

    return run_repo_tool
