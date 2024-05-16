# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import logging
import os
from typing import Callable, Dict

import omni.repo.man

logger = logging.getLogger(__name__)


def _comment_archives(file_path, archives):
    with open(file_path, "r") as f:
        content = f.read()
    for archive in archives:
        if archive in content:
            content = content.replace(f'"{archive}"', f'## "{archive}"')
            content = content.replace(f"'{archive}'", f'## "{archive}"')
            omni.repo.man.print_log(f"{file_path} -> {archive}", logging.INFO)
    with open(file_path, "w") as f:
        f.write(content)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Comment archives extension dependencies in *.kit and config/extension.toml files"

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_comment_archive_deps"]
        search_folder = tool_config["search_folder"]
        archives = tool_config["archives"]

        if not os.path.isdir(search_folder):
            omni.repo.man.print_log(f"The search folder doesn't exist: {search_folder}", logging.WARN)
            return

        for root, dirs, files in os.walk(search_folder, followlinks=True):
            for file in files:
                if file == "extension.toml" or file.endswith(".kit"):
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        _comment_archives(file_path, archives)
                    else:
                        omni.repo.man.print_log(f"Skipping {file_path} because it doesn't exist", logging.WARN)
                        continue

    return run_repo_tool
