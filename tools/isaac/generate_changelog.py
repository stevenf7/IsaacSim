import argparse
import datetime
import glob
import os
import re
from distutils.version import LooseVersion
from pprint import pprint
from typing import Callable, Dict, List, Set, Tuple

import toml


def parse_version(line: str):
    """
    Parse version in an extension changelog file
    Try parse line as a version, assuming it will look like ' [2.3.1] - 2020-09-30 '
    This is copied from /kit/source/extensions/omni.kit.registry.nucleus/omni/kit/registry/nucleus/changelog_parser.py
    """
    line = line.lstrip(" #")
    m = re.match(r"\[?(?P<version>[^(\]|\s)]+)\]? - (?P<release_date>\d{4}-\d{1,2}-\d{1,2})$", line)
    if m:
        return (m.group("version"), (datetime.datetime.strptime(m.group("release_date"), "%Y-%m-%d").date()))

    m = re.match(r"\[(?P<version>Unreleased)\]$", line)
    if m:
        return (m.group("version"), None)

    return None


def validate_changelog(change: str):
    i = 0
    prev_version = None
    prev_date = None
    for line in change.splitlines():
        i += 1
        # line should not begin with space
        # line should begin with #, ##, ###, - or emptyline

        if len(line) > 0 and not line.startswith(
            ("# Changelog", "## [", "### ", "    -", "-", "\n", "The format is based on")
        ):
            print("Line looks incorrect: ")
            print(line, i)
            return False

        # Check for an approved types
        if line.startswith("### "):
            temp = line.strip("### ")
            if not temp.startswith(("Added", "Changed", "Deprecated", "Fixed", "Removed", "Security")):
                print(temp, i)
                return False
        res = parse_version(line)
        if res is not None:
            version, date = res
            if version is not None and date is not None:
                if prev_version is not None and prev_date is not None:
                    if LooseVersion(version) > LooseVersion(prev_version):
                        print(f"Version decresed: {version} vs {prev_version}")
                        return False
                    if date > prev_date:
                        print(f"date decresed: {date} vs {prev_date}")
                        return False
                else:
                    prev_version = version
                    prev_date = date
                pass
            else:
                print("Version or date is None: ")
                print(version, date, line, i)

    return True


def parse_changelog(change: str) -> Tuple[str, datetime.date, List]:
    """Parse an extension changelog content and yield tuples of version, date and list of strings"""
    version = None
    date = None
    content = {"Added": [], "Removed": [], "deprecated": [], "Changed": [], "Fixed": [], "General": []}
    category = "General"

    for line in change.splitlines():
        res = parse_version(line)
        if res:
            yield version, date, content
            version, date = res
            content = {"Added": [], "Removed": [], "deprecated": [], "Changed": [], "Fixed": [], "General": []}
        else:
            if len(line) > 0:
                if line.startswith("### "):
                    category = line.strip("### ")
                else:
                    if category not in content:
                        content[category] = []
                    content[category].append(line.strip("### ").strip("- "))

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


def validate(changelog_path: str) -> bool:
    """
    returns for this extension a list of tuples of (version, changelog strings) for each version between old and new
    """

    if os.path.exists(changelog_path):
        print("validating", changelog_path)
        with open(changelog_path) as changelog_file:
            changelog_str = changelog_file.read()
            if not validate_changelog(changelog_str):
                print("FAIL")
                exit()
                return False
    else:
        print("Path doesn't exist")
    return True


def get_extension_diff_data(
    changelog_path: str, old_date: datetime.date, new_date: datetime.date
) -> List[Tuple[str, List[str]]]:
    """
    returns for this extension a list of tuples of (version, changelog strings) for each version between old and new
    """

    found_new = False
    found_old = False
    curr_log = []
    result = []

    if os.path.exists(changelog_path):
        with open(changelog_path) as changelog_file:
            changelog_str = changelog_file.read()
            # parses each entry
            for v, d, content in parse_changelog(changelog_str):
                if d is not None:
                    if d <= new_date and d >= old_date:
                        curr_log.append((v, d, content))
                        found_new = True
                    else:
                        found_new = False

    for entry in curr_log:
        result.append((entry[0], entry[2]))

    return result, found_new


def generate_extension_diff_report(
    name: str, changelog_path: str, old_date: datetime.date, new_date: datetime.date
) -> List[Tuple[str, List[str]]]:
    """
    generate a changelog for an extension by reading a range of versions
    from it's CHANGELOG.md
    """
    results, is_new = get_extension_diff_data(changelog_path, old_date, new_date)
    if len(results) > 0:
        print(f"\n- **{name}**")
    all_entries = {}
    if is_new:
        print("\n    - New Extension")
        return
    for entry in results:
        for k, values in entry[1].items():
            if k not in all_entries:
                all_entries[k] = []
            for v in values:
                all_entries[k].append(v)
        # print("\t", entry[0])
        # for k, values in entry[1].items():
        #     if(len(values)>0):
        #         print("\t\t", k)
        #         for change in values:
        #             print("\t\t\t", change)
        # print("\t", entry[0], "".join(entry[1]))
    for k, values in all_entries.items():
        if len(values) > 0:
            print(f"\n    - {k}\n")
            for change in values:
                print("        - ", change)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Generate changelog documentation"
    parser.add_argument("--validate", dest="validate", required=False, default=False, help="Validate all changelogs")

    def run_repo_tool(options: Dict, config: Dict):
        # tool_config = config.get("repo_build", {})
        # print(config)
        tool_config = config["repo_generate_changelog"]
        home_path = tool_config["home_path"]
        # args = parser.parse_args()
        # print(args)
        extensions = sorted(os.listdir(home_path))

        for e in extensions:
            if e not in ["omni.isaac.internal_tools"]:
                name = e.split("\\")[-1]
                # print(name)
                changelog_path = os.path.join(home_path, e, "docs", "CHANGELOG.md")
                if options.validate:
                    validate(changelog_path)

                generate_extension_diff_report(name, changelog_path, datetime.date(2023, 10, 31), datetime.date.today())

    return run_repo_tool
