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
import os
import subprocess
import tempfile
from urllib.parse import urlparse, urlunparse

# Initialize the parser
parser = argparse.ArgumentParser(
    description="Documents Asset Image Renderer", formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "asset_list",
    help="Text file of USD files to render. Each line should be a path to a USD file.",
)
parser.add_argument(
    "output_dir",
    help="The output directory to save the images to.",
)
parser.add_argument(
    "--pretend", action="store_true", default=False, help="Don't do anything, but show what would be done."
)
parser.add_argument("--headless", action="store_true", default=False, help="Run without the UI.")

args = parser.parse_args()


def convert_to_thumbnail_path(asset_path):
    """Convert an asset path to its corresponding thumbnail path if original usd asset is given."""
    # Parse the URL to get the path components
    parsed = urlparse(asset_path)

    # Split the path into directory and filename
    path_parts = parsed.path.split("/")

    # Find the filename (last part)
    filename = path_parts[-1]

    # Split filename into name and extension
    name_parts = filename.rsplit(".", 1)
    if len(name_parts) != 2:
        return asset_path  # Can't parse, return original

    name, ext = name_parts

    # Create thumbnail filename
    thumbnail_filename = f"{name}.thumb.usd"

    # Check if the path already contains .thumbs to avoid double insertion
    if ".thumbs" in path_parts:
        # Path already has .thumbs, check if filename already has .thumb
        if filename.endswith(".thumb.usd"):
            # Already a thumbnail file, return as-is
            return asset_path
        else:
            # Replace the filename with thumbnail version
            new_path_parts = path_parts[:-1] + [thumbnail_filename]
    else:
        # Insert .thumbs directory before the filename
        new_path_parts = path_parts[:-1] + [".thumbs", thumbnail_filename]

    # Reconstruct the URL
    new_path = "/".join(new_path_parts)
    new_parsed = parsed._replace(path=new_path)

    return urlunparse(new_parsed)


def create_thumbnail_asset_list(original_asset_list_path):
    """Create a temporary asset list file with thumbnail paths."""
    thumbnail_paths = []

    # Read the original asset list
    with open(original_asset_list_path, "r") as f:
        for line in f:
            asset_path = line.strip()
            if asset_path:
                # Convert to thumbnail path
                thumbnail_path = convert_to_thumbnail_path(asset_path)
                thumbnail_paths.append(thumbnail_path)
                print(f"Converting: {asset_path} -> {thumbnail_path}")

    # Create a temporary file with thumbnail paths
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for thumbnail_path in thumbnail_paths:
        temp_file.write(thumbnail_path + "\n")
    temp_file.close()

    return temp_file.name


images_dir = args.output_dir

# Convert asset paths to thumbnail paths
thumbnail_asset_list = create_thumbnail_asset_list(args.asset_list)

cmd = [
    "./python.sh",
    "../../../tools/thumbnail_generator/render_assets.py",
    "-i",
    thumbnail_asset_list,
    "-r",
    "1920x1080",
    "--images-dir",
    images_dir,
    "--reposition-camera",
    "--skip-existing",
]

if args.headless:
    cmd.append("--headless")

print("Running : " + " ".join(cmd))

if args.pretend:
    # Clean up temp file
    os.remove(thumbnail_asset_list)
    exit(0)

try:
    subprocess.run(cmd)
finally:
    # Clean up temp file
    os.remove(thumbnail_asset_list)
