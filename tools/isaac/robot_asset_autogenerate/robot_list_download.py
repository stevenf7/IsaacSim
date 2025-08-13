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
import os

import carb
from isaacsim.storage.native import find_files_recursive, get_assets_root_path

parser = argparse.ArgumentParser(description="Parse through relevant robot files and output a list of file names")
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
# exclude environments, thumbnails, and any special exceptions
exclude_paths = [
    "Environments/Outdoor/Rivermark",
    ".thumbs",
    "Robotiq_2F_140_controller",
]

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
