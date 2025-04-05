# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import argparse
import os
from pprint import pprint
from typing import Callable, Dict
from urllib.request import urlopen

import requests
import toml


def list_folders(directory, substring=None, exclude_substring=False):
    """Lists all folders in a given directory.

    Args:
        directory: The path to the directory.
        substring: The substring to search for in folder names.
                If None, all folders are returned.

    Returns:
        A list of folder names.
    """
    if substring is None:
        return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    else:
        if exclude_substring:
            return [
                name
                for name in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, name)) and substring not in name
            ]
        else:
            return [
                name
                for name in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, name)) and substring in name
            ]


def get_commit_hash_from_file(file_path):
    """Reads a file and extracts the commit hash from a specific line.

    Args:
      file_path: The path to the file.

    Returns:
      The commit hash string, or None if not found.
    """
    try:
        with open(file_path, "r") as f:
            for line in f:
                if "# Kit SDK Version:" in line:
                    # Assuming the commit hash is the last part of the line
                    return line.split(".")[-2].strip().replace("gl", "")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None


def read_text_from_url(url):
    """Reads a TOML file from a URL.

    Args:
      url: The URL of the TOML file.

    Returns:
      A dictionary containing the TOML data, or None if an error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching file: {e}")
        return None


def read_text(file_path):
    with open(file_path, "r") as file:
        text = file.read()
    return text


def process_exact_version_dependencies(lines):
    start_index = None
    end_index = None

    for i, line in enumerate(lines):
        if line.startswith("# Exact Version dependencies:"):
            start_index = i + 1
        elif start_index is not None and not line.startswith("#"):
            end_index = i
            break

    if start_index is not None:
        return [line.lstrip("# ").strip() for line in lines[start_index:end_index]]
    else:
        return None


def process_version_lock(lines):
    parsed_toml = toml.loads(lines)
    return parsed_toml["settings"]["app"]["exts"]["enabled"]


def remove_after_hyphen(input_string):
    """Removes everything after the first hyphen in a string.

    Args:
      input_string: The input string.

    Returns:
      The string with everything after the first hyphen removed.
    """
    try:
        return input_string.split("-", 1)[0]
    except IndexError:
        return input_string


def remove_after_hyphen_from_dict_lists(input_dict):
    """Removes everything after the first hyphen in strings within list values
       of a dictionary.

    Args:
      input_dict: The input dictionary where values are lists of strings.

    Returns:
      A new dictionary with the modified lists.
    """
    new_dict = {}
    for key, value_list in input_dict.items():
        new_list = []
        for value in value_list:
            try:
                new_list.append(value.split("-", 1)[0])
            except IndexError:
                new_list.append(value)
        new_dict[key] = new_list
    return new_dict


def convert_lists_to_sets(input_dict):
    """Converts a dictionary of lists into a dictionary of sets.

    Args:
      input_dict: A dictionary where the values are lists.

    Returns:
      A new dictionary where the values are sets.
    """
    return {key: set(value) for key, value in input_dict.items()}


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Dump extension list."
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="release",
    )

    def run_repo_tool(options: Dict, config: Dict):
        # Read config info from ./repo.toml
        tool_config = config["repo_dump_extensions"]
        root_path = tool_config["root_folder"].replace("${config}", options.config)

        hash = get_commit_hash_from_file(root_path + "/apps/exts.deps.generated.kit")
        # Isaac extensions, just list out the directory
        all_exts = {}
        all_exts["isaac"] = list_folders(root_path + "/exts")
        all_exts["isaac_deprecated"] = list_folders(root_path + "/extsDeprecated")
        all_exts["kit_exts"] = list_folders(root_path + "/extscache", hash)
        all_exts["other_exts"] = list_folders(root_path + "/extscache", hash, True)
        all_exts["kit_kernel"] = list_folders(root_path + "/kit/extscore")
        all_exts["physics"] = list_folders(root_path + "/extsPhysics")

        url = "https://gitlab-master.nvidia.com/omniverse/kit-github/kit-app-template/-/raw/main/templates/omni.all.template.extensions.kit?ref_type=heads"
        # url_p1 = "https://gitlab-master.nvidia.com/omniverse/sample-p1-extensions/-/raw/main/source/apps/omni.sample_p1.extensions.kit"
        url_p1 = "/home/hmazhar/repos/omni_isaac_sim/omni.sample_p1.extensions.kit"
        text = read_text_from_url(url)
        text_p1 = read_text(url_p1)
        all_exts["exact_versions"] = process_exact_version_dependencies(text.splitlines())
        all_exts["version_lock"] = process_version_lock(text)

        all_exts["exact_versions_p1"] = process_exact_version_dependencies(text_p1.splitlines())
        all_exts["version_lock_p1"] = process_version_lock(text_p1)
        all_exts_sets = convert_lists_to_sets(remove_after_hyphen_from_dict_lists(all_exts))

        all_isaac_sim_exts = all_exts_sets["isaac"] | all_exts_sets["isaac_deprecated"]
        template_exts = all_exts_sets["exact_versions"] | all_exts_sets["version_lock"]  # all extension template exts
        p1_exts = all_exts_sets["exact_versions_p1"] | all_exts_sets["version_lock_p1"]
        non_template_exts = all_exts_sets["other_exts"] - template_exts - p1_exts

        print("Isaac Sim Extensions")
        pprint(all_isaac_sim_exts)
        print("Kit Extensions")
        pprint(all_exts_sets["kit_exts"])
        print("Kit Kernel")
        pprint(all_exts_sets["kit_kernel"])
        print("Other Extensions")
        pprint(all_exts_sets["other_exts"])
        print("Non Template Extensions")
        pprint(non_template_exts)

    return run_repo_tool
