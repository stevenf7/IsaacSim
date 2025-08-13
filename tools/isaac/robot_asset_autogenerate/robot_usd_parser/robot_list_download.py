# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import carb
import isaacsim.core.utils.stage as stage_utils
import numpy as np
import omni
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.api.robots import Robot
from isaacsim.core.experimental.prims import Articulation, XformPrim
from isaacsim.core.utils.prims import get_prim_at_path
from isaacsim.core.utils.stage import add_reference_to_stage, get_stage_units
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import (
    find_files_recursive,
    get_assets_root_path,
    get_stage_references,
    is_absolute_path,
    is_path_external,
    is_valid_usd_file,
)
from pxr import Gf, Sdf, Usd, UsdGeom

parser = argparse.ArgumentParser(description="Parse through relevant robot files and output a list of robot names")
parser.add_argument(
    "--csv",
    "-c",
    type=str,
    required=False,
    default="./tools/isaac/robot_asset_autogenerate/outputs/robot_list.csv",
    help="Path of the list of robot names (as a csv file) to output to",
)
args = parser.parse_args()
os.makedirs(os.path.dirname(args.csv), exist_ok=True)

root_path = carb.settings.get_settings().get("/persistent/isaac/asset_root/default")
search_paths = [
    root_path + "/Isaac/Robots",
]
exclude_paths = ["Environments/Outdoor/Rivermark", ".thumbs"]

all_files = find_files_recursive(search_paths)
output = []
for file in all_files:
    if file.endswith(".usd") and not any(exclude_path in file for exclude_path in exclude_paths):
        output.append(file)


with open(args.csv, "w", newline="") as f:
    writer = csv.writer(f)
    for item in output:
        writer.writerow([item])


simulation_app.close()
