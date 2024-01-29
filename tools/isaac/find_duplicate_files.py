# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import argparse
import os
from typing import Callable, Dict

from omni.repo.package.duplicate_files_finder import check_for_duplicate_files


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Find duplicate files."

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_find_duplicate_files"]
        path = os.path.dirname(os.path.realpath(__file__)) + "/../../"

        check_for_duplicate_files(path, tool_config["min_file_size_to_warn"], tool_config["min_file_size_to_fail"])

    return run_repo_tool
