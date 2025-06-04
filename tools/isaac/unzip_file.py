# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import glob
import logging
import os
from typing import Callable, Dict

import omni.repo.man
import packmanapi

logger = logging.getLogger(__name__)


def _unzip_file(file_path, dst_folder):
    ext = os.path.splitext(file_path)[1]
    if ext == ".7z":
        packmanapi.extract_archive7z_to_folder(file_path, dst_folder)
    elif ext == ".zip":
        packmanapi.extract_archivezip_to_folder(file_path, dst_folder)
    elif ext == ".tar":
        packmanapi.extract_archivetar_to_folder(file_path, dst_folder)
    else:
        omni.repo.man.print_log(f"Skipping {file_path} because archive extension is not supported", logging.WARN)


def setup_repo_tool(parser: argparse.ArgumentParser, config: Dict) -> Callable:
    parser.description = "Unzip (.7z|.zip|.tar) files"
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Source file to unzip",
    )
    parser.add_argument(
        "--dst",
        type=str,
        required=False,
        help="Destination folder. If not provided, the file's parent folder will be used",
    )

    def run_repo_tool(options: Dict, config: Dict):
        # source files
        paths = [options.file] if os.path.exists(options.file) else glob.glob(options.file)
        if not paths:
            omni.repo.man.print_log(f"Cannot find or open {options.file}", logging.WARN)
            return

        for path in paths:
            # destination folder
            dst_folder = options.dst
            if not dst_folder:
                dst_folder = os.path.dirname(path)
            os.makedirs(dst_folder, exist_ok=True)
            # unzip file
            omni.repo.man.print_log(f"Unzipping: {path} -> {dst_folder}", logging.INFO)
            _unzip_file(path, dst_folder)

    return run_repo_tool
