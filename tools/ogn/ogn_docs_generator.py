# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import json
import glob
from typing import Dict, Callable
from pathlib import Path, PurePath
import mmap
import logging, os, argparse

logger = logging.getLogger(os.path.basename(__file__))


def parse_ogn(ogn_doc_file, ogn_src_file):
    """
        parse the ogn_src_file and write to ogn_doc_file.
    """
    f = open(ogn_src_file, "r")
    ogn_src_file = json.load(f)
    nodename = list(ogn_src_file.keys())[0]
    node_description = ogn_src_file[nodename]["description"]
    if "$comment" in ogn_src_file[nodename].keys():
        comment = "\n    {}".format(ogn_src_file[nodename]["$comment"])
    else:
        comment = ""
    node_markup = "*" * len(nodename)
    ogn_doc_file.write("\n\n\n{}\n{}\n    {}\n{}\n".format(nodename, node_markup, node_description, comment))

    if "inputs" in ogn_src_file[nodename].keys():
        ogn_doc_file.write("\n**Inputs**")
        input_dict = ogn_src_file[nodename]["inputs"]
        if "$comment" in input_dict.keys():
            comment = ", {}".format(input_dict["$comment"])
        else:
            comment = ""
        for key in input_dict.keys():
            data_type = input_dict[key]["type"]
            if "optional" in input_dict[key]:
                optional = ", optional"
            else:
                optional = ""
            if "default" in input_dict[key]:
                if input_dict[key]["default"] == "":
                    default = ""
                else:
                    default = ". Default to {}".format(input_dict[key]["default"])
            else:
                default = ""
            if "$comment" in input_dict[key].keys():
                comment = ". {}".format(input_dict[key]["$comment"].rstrip(" ."))
            else:
                comment = ""
            if isinstance(input_dict[key]["description"], list):
                description = input_dict[key]["description"][0]
            else:
                description = input_dict[key]["description"]

            description = description.rstrip(" .")
            if description == "" and comment == "" and default == "":
                ogn_doc_file.write("\n    - **{}** (*{}{}*)".format(key, data_type, optional))
            else:
                ogn_doc_file.write(
                    "\n    - **{}** (*{}{}*): {}{}{}.".format(key, data_type, optional, description, comment, default)
                )

    if "outputs" in ogn_src_file[nodename].keys():
        ogn_doc_file.write("\n\n**Outputs**")
        output_dict = ogn_src_file[nodename]["outputs"]
        for key in output_dict.keys():
            data_type = output_dict[key]["type"]
            if isinstance(output_dict[key]["description"], list):
                description = output_dict[key]["description"][0]
            else:
                description = output_dict[key]["description"]

            description = description.rstrip(" .")
            if description == "":
                ogn_doc_file.write("\n    - **{}** (*{}*)".format(key, data_type))
            else:
                ogn_doc_file.write("\n    - **{}** (*{}*): {}.".format(key, data_type, description))

    f.close()


def locate_ogn(ext_dir):
    """
        given the extension directory, locate all the ognfiles
    """
    ognfiles_list = list(Path(ext_dir).rglob("*.ogn"))
    return ognfiles_list


def append_index_doc(ext_dir):
    """
        automatically add a line in the main index.rst to include the ogn.rst
        or create a new index.rst with ogn.rst included
    """

    index_rst = ext_dir + "/docs/index.rst"

    if Path(index_rst).exists():
        with open(index_rst, "a+b", 0) as file, mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(b".. include::  ogn.rst") == -1:
                file.write(b"\n\nOmnigraph Nodes")
                file.write(b"\n=======================")
                file.write(b"\n\n.. include::  ogn.rst")
        file.close()
    else:
        logger.info("creating docs/index.rst for %s", ext_dir)
        with open(index_rst, "w") as file:
            ext_folder = PurePath(ext_dir).name
            ext_title = ext_folder[11:].replace("_", " ").title()
            first_line = "{} [{}]\n".format(ext_title, ext_folder)
            second_line = "#" * len(first_line)
            file.write(first_line)
            file.write(second_line)
            file.write("\n\nOmnigraph Nodes")
            file.write("\n=======================")
            file.write("\n\n.. include::  ogn.rst")
        file.close()


def compile_ogn_doc(ext_dir):
    """
        write the ogn.rst per directory, include ogn.rst in the index.rst
    """
    ogn_doc_path = ext_dir + "/docs/ogn.rst"  # default ogn docs location and file name
    ogn_rst = open(ogn_doc_path, "w")  # will overwrite any existing ogn.rst file
    ogn_list = locate_ogn(ext_dir)  # find all the ogn files
    for file in ogn_list:  # parse them and write
        parse_ogn(ogn_rst, file)
    ogn_rst.close()
    append_index_doc(ext_dir)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Generate omnigraph documentations."

    def run_repo_tool(options: Dict, config: Dict):
        ogn_config = config["repo_ogn"]
        home_dir = ogn_config["home_path"]
        ogn_exts = ogn_config["ogn_exts_includes"]
        for ext in ogn_exts:
            print("ogn_ext", home_dir + ext)
            compile_ogn_doc(home_dir + ext)

    return run_repo_tool
