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
