# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import subprocess

# Initialize the parser
parser = argparse.ArgumentParser(
    description="Documents Asset Image Renderer", formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "asset_list",
    help="Text file of USD files to render.",
)
parser.add_argument(
    "output_dir",
    help="The output directory.",
)

parser.add_argument(
    "--pretend", action="store_true", default=False, help="Don't do anything, but show what would be done."
)
parser.add_argument("--headless", action="store_true", default=False, help="Run without the UI.")

args = parser.parse_args()


images_dir = args.output_dir
scenes_dir = args.output_dir + "/scenes"

cmd = [
    "./python.sh",
    "standalone_examples/api/isaacsim.util.internal/render_assets.py",
    "-i",
    args.asset_list,
    "-r",
    "1920x1080",
    "--images-dir",
    images_dir,
    "--scenes-dir",
    scenes_dir,
    "--use-full-path-name",
    "--reposition-camera",
]

if args.headless:
    cmd.append("--headless")

print("Running : " + " ".join(cmd))

if args.pretend:
    exit(0)

subprocess.run(cmd)
