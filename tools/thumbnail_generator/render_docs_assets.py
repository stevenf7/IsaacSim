# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

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
