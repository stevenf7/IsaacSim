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
parser = argparse.ArgumentParser(description="Asset Thumbnails Renderer", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
    "asset_root",
    help="Omniverse asset root path.",
)

parser.add_argument(
    "--pretend", action="store_true", default=False, help="Don't do anything, but show what would be done."
)
parser.add_argument("--headless", action="store_true", default=False, help="Run without the UI.")

args = parser.parse_args()

# All the directories we'll generate thumbnails for
asset_dir_paths = [
    "Environments/Outdoor/Rivermark/dsready_content",
    "IsaacLab",
    "Materials",
    "People",
    "Props",
    "Robots",
    "Samples",
    "Sensors",
]

# These are always excluded
base_exclusions = [
    # "Parts",
    # "parts",
    # "Source",
    # "DetailedProps",
    # "Materials",
    # "HighResProps",
]

# Here we build a dict containing extra exclusions for specific directories
props_exclusions = ["Props", "props", "*instanceable_meshes*"]
extra_exclusions = {
    "Environments": ["Rivermark", "Modular_Warehouse"] + props_exclusions,
    "IsaacLab": props_exclusions,
    "People": props_exclusions + ["skelanim"],
    "Robots": props_exclusions,
    "Samples": props_exclusions,
    "Sensors": props_exclusions,
    "Props": ["*instanceable_meshes*"],
}


# Run the asset render once for each path
for asset_dir_path in asset_dir_paths:

    full_asset_dir_path = args.asset_root + "/" + asset_dir_path

    # Build our exclusion list
    exclusions = base_exclusions.copy()
    if asset_dir_path in extra_exclusions:
        exclusions.extend(extra_exclusions[asset_dir_path])

    cmd = [
        "./python.sh",
        "standalone_examples/api/isaacsim.util.internal/render_assets.py",
        "-r",
        "256x256",
        "-TR",
    ]

    for e in exclusions:
        cmd.extend(["-E", e])

    cmd.append(full_asset_dir_path)

    if args.headless:
        cmd.append("--headless")

    print("Running : " + " ".join(cmd))

    if args.pretend:
        continue

    subprocess.run(cmd)
