import argparse
import datetime
import glob
import os
import platform
import re
import sys
from pprint import pprint
from typing import Callable, Dict, List, Set, Tuple

import toml


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Generate vscode settings."
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        required=False,
        default="release",
        help="Package only specified config. (default: %(default)s)",
    )

    def run_repo_tool(options: Dict, config: Dict):
        tool_config = config["repo_edit_sysconfig"]
        sysconfig_path = tool_config["sysconfig_path"]
        # args = parser.parse_args()
        if platform.system().lower() == "windows":
            print("On windows this command does nothing")
            return
        env_replace_string = """
# ISAAC SIM BEGIN GENERATED PART
base_directory = os.path.abspath(os.path.dirname(__file__) + "../../../")
for k,v in build_time_vars.items():
        if isinstance(v, str):
                build_time_vars[k] = v.replace("/builds/omniverse/externals/python-build/_build/repopackageroot", base_directory)
# ISAAC SIM END GENERATED PART"""

        sysconfig_path = sysconfig_path.replace("${config}", options.config)
        print(sysconfig_path)

        sysconfig_file = os.path.abspath(sysconfig_path)

        with open(sysconfig_file, "r+") as tf:
            last_line = ""
            for line in tf:
                last_line = line
                pass
            if "# ISAAC SIM END GENERATED PART" in last_line:
                print("end block found, not writing")
            else:
                print("writing env_replace_string into file")
                tf.write(env_replace_string)

    return run_repo_tool
