# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse
import datetime
import fnmatch
import os
import re

from isaacsim import SimulationApp

# Initialize the parser
parser = argparse.ArgumentParser(description="Render Assets Script", formatter_class=argparse.RawTextHelpFormatter)

# Add positional arguments that can accept zero or more values
parser.add_argument(
    "assets",
    nargs="*",
    help="USD files or directories (must use -R to recurse)",
)


def timestamp(date_string):
    date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(date_object.timestamp())


def parser_resolution_type(value):
    m = re.match(r"^(\d+)x(\d+)$", value)
    if not m:
        raise argparse.ArgumentTypeError("Resolution not in WIDTHxHEIGHT format")
    width, height = map(int, m.groups())
    return width, height


parser.add_argument(
    "-r",
    "--resolution",
    type=parser_resolution_type,
    default=(256, 256),
    help="Image resolution in WIDTHxHEIGHT format (default: 256x256)",
)
parser.add_argument("-i", "--input", action="append", type=str, help="Use an inputs text file with USD paths.")
parser.add_argument("-e", "--environment", type=str, help="USD file containing the scene and lighting for the asset.")
parser.add_argument("--scenes-dir", type=str, default=None, help="Path of the scene created to render the assset.")
parser.add_argument(
    "--scenes-usd-prefix", type=str, default="scene", help='The string before the ".usd" in the scene filename.'
)
parser.add_argument("--images-dir", type=str, default="./", help="Output directory for rendered asset images.")
parser.add_argument(
    "-T",
    "--thumbnail",
    action="store_true",
    help="""
Assets are thumbnails, equivalent to :
  --scenes-dir .thumbs --scenes-usd-prefix thumb --images-dir .thumbs/256x256
""",
)
parser.add_argument("-R", "--recursive", action="store_true", default=False, help="Recurse directories.")
parser.add_argument(
    "-f",
    "--force-create-scene",
    action="store_true",
    default=False,
    help="Always create the scene and overwrite the existing one.",
)
parser.add_argument(
    "--use-full-path-name",
    action="store_true",
    default=False,
    help="""
Use the full path of the asset when creating the image and scene filenames.  Used to avoid conflicts when rendering
multiple assets with an absolute scene or image path.
For example :
  asset_path : omniverse://isaac-dev.ov.nvidia.com/Isaac/Robots/Franka/franka.usd
  with --use-full-path-name :
    image_filename : Isaac_Robots_Franka_franka.usd.png
  without :
    image_filename : franka.usd.png
""",
)
parser.add_argument(
    "-E",
    "--exclude",
    action="append",
    type=str,
    default=[],
    help="Excludes files or directories matching the argument, with wildcard support.",
)
parser.add_argument(
    "--reposition-camera",
    action="store_true",
    default=False,
    help="Useful when rendering an asset with the created scene USD file.",
)
parser.add_argument(
    "--skip-existing",
    action="store_true",
    default=False,
    help="If a scene USD and image file have already been generated, skip the asset.",
)
parser.add_argument(
    "--pretend", action="store_true", default=False, help="Don't do anything, but show what would be done."
)
parser.add_argument("--headless", action="store_true", default=False, help="Run without the UI.")

parser.add_argument("--log_latest", action="store_true", default=False, help="Log the latest generated time.")

args, _ = parser.parse_known_args()

# We've got thumbnails, set the defaults of certain args
if args.thumbnail:
    args.scenes_dir = ".thumbs"
    args.scenes_usd_prefix = "thumb"
    args.images_dir = ".thumbs/" + "x".join([str(v) for v in args.resolution])
    args.log_latest = True

if not args.input and not args.assets:
    parser.error("Must provide assets or an input file.")

# launch app
simulation_app = SimulationApp({"headless": args.headless})


import posixpath
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# Enable isaacsim.util.internal
import omni.kit

omni.kit.app.get_app().get_extension_manager().set_extension_enabled_immediate("isaacsim.util.internal", True)
import isaacsim.util.internal.utils.render_assets as render_assets
import omni.client
import omni.timeline
from isaacsim.util.internal.utils.file_utils import join
from omni.isaac.core import World
from omni.isaac.nucleus import is_dir, is_file


def is_a_dir(path):
    try:
        return is_dir(path)
    except:
        return False


def file_exists(path):
    try:
        return is_file(path)
    except:
        return False


def find_files(start_path, filter_fn=lambda a: True, ignore_dir_fn=lambda d: False):
    if filter_fn(start_path):
        return [start_path]

    remaining_folders = []
    remaining_folders.append(start_path)
    files = []
    while len(remaining_folders):
        path = remaining_folders.pop()
        result, entries = omni.client.list(path)
        if result == omni.client.Result.OK:
            files = files + [
                join(path, e.relative_path) for e in entries if (e.flags & 4) == 0 and filter_fn(e.relative_path)
            ]
            remaining_folders = remaining_folders + [
                join(path, e.relative_path) for e in entries if (e.flags & 4) > 0 and not ignore_dir_fn(e.relative_path)
            ]
    return files


def collect_asset_paths(args):
    def is_excluded(path):
        return any(fnmatch.fnmatch(path, e) for e in args.exclude)

    paths = []
    if args.input:
        for i in args.input:
            with open(i) as f:
                for l in f:
                    paths.append(l.strip())
    paths.extend(args.assets)
    asset_paths = []
    for p in paths:
        if is_a_dir(p):
            if not args.recursive:
                raise Exception("Directory provided but --recursive not set.")
            files = find_files(
                p,
                lambda d: os.path.splitext(d)[1] in [".usd", ".usda", ".usdc"],
                lambda d: d == ".thumbs" or is_excluded(d),
            )
            files = [f for f in files if not is_excluded(f)]
            # asset_paths.extend(files)

        elif not is_excluded(p):
            asset_paths.append(p)

    return asset_paths


def join_path_and_filename_with_directory_of_path(path, other_path, filename):
    """
    Like os.path.join but combines the asset paths directory with the other directory and filename, and works with URLs
    """
    parsed = urlparse(path)
    parsed_other = urlparse(other_path)

    # The other path is a URL, ignore the path
    if parsed_other.scheme and parsed_other.netloc:
        return other_path + "/" + filename

    # The other path is absolute and not a URL, ignore the path
    elif os.path.isabs(other_path):
        return os.path.join(other_path, filename)

    # We have a relative other_path

    # The path is a URL
    if parsed.scheme and parsed.netloc:
        dir_path = parsed.path.rsplit("/", 1)[0]
        file_path = dir_path + "/" + other_path + "/" + filename
        return urlunparse(parsed._replace(path=file_path))

    # The path is not a URL
    else:
        return os.path.join(os.path.dirname(path), other_path, filename)


def path_split(path):
    parsed = urlparse(path)
    if parsed.scheme and parsed.netloc:
        return posixpath.split(parsed.path)
    else:
        # Local file paths
        return os.path.split(path)


def build_job(path, args):

    # Build the paths for the output image and the scene USD file
    path_parts = path_split(path)
    filename_parts = path_parts[1].rsplit(".", 1)

    image_filename = f"{filename_parts[0]}.{filename_parts[1]}.png"
    last_generated_filename = f".{filename_parts[0]}.{filename_parts[1]}.last_generated"
    if args.scenes_dir:
        scene_filename = f"{filename_parts[0]}.{args.scenes_usd_prefix}.{filename_parts[1]}"

    # Use the whole path with _ instead of / as a prefix to the filename
    if args.use_full_path_name:
        filename_prefix = path_parts[0].strip("/").replace("/", "_")
        image_filename = filename_prefix + "_" + image_filename
        last_generated_filename = image_filename + ".last_generated"
        if args.scenes_dir:
            scene_filename = filename_prefix + "_" + scene_filename

    image_path = join_path_and_filename_with_directory_of_path(path, args.images_dir, image_filename)
    last_generated_path = join_path_and_filename_with_directory_of_path(path, args.images_dir, last_generated_filename)

    job = {
        "asset_path": path,
        "image_path": image_path,
        "resolution": args.resolution,
        "last_generated": last_generated_path,
    }

    if args.scenes_dir:
        scene_path = join_path_and_filename_with_directory_of_path(path, args.scenes_dir, scene_filename)
        job["scene_path"] = scene_path

    if args.environment:
        job["environment_path"] = args.environment

    return job


renderer = render_assets.AssetRenderer()

asset_paths = collect_asset_paths(args)
asset_paths.sort(reverse=False)

# Send all our jobs one at a time to the renderer, keep track of the failures
successes = []
fails = []
num_skipped = 0
for path in asset_paths:

    job = build_job(path, args)

    if args.skip_existing and file_exists(job["image_path"]) and file_exists(job["scene_path"]):
        print(f"Skipping {path}")
        num_skipped += 1
        continue

    elif args.log_latest:
        # Check if there were changes in the asset or thumbnail scene since the last time it was generated
        result, image_stat = omni.client.stat(job["asset_path"])
        scene_result, scene_stat = omni.client.stat(job["asset_path"])
        if result == omni.client.Result.OK:
            result, stat = omni.client.stat(job["last_generated"])
            if result == omni.client.Result.OK:
                result, _, content = omni.client.read_file(job["last_generated"])
                if result == omni.client.Result.OK:
                    created_time = memoryview(content).tobytes().decode("utf-8")

                    if timestamp(str(image_stat.created_time)) <= timestamp(created_time) or (
                        scene_result == omni.client.Result.OK
                        and timestamp(str(scene_stat.created_time)) <= timestamp(created_time)
                    ):
                        print(f"Skipping {path}")
                        num_skipped += 1
                        continue

    print(f"Creating image for {path}")

    if args.pretend:
        continue
    success = renderer.create_image(
        job, reposition_camera=args.reposition_camera, force_create_scene=args.force_create_scene
    )
    if args.log_latest:
        result, image_stat = omni.client.stat(job["image_path"])
        omni.client.write_file_ex(job["last_generated"], bytes(str(image_stat.created_time).encode("utf-8")))

    if not success:
        fails.append(job)
    else:
        successes.append(job)

print()
print()
print("Render Asset Results")

num_total = len(asset_paths)
num_failed = len(fails)
num_succeeded = num_total - num_failed - num_skipped

if not args.pretend:
    print(f"Successfully rendered {num_succeeded} / {num_total} assets.")
    print(f"Skipped {num_skipped} / {num_total} assets.")
    print(f"Failed to render {num_failed} / {num_total} assets")
    if fails:
        print("Unsuccessful assets:")
        for fail in fails:
            asset_path = fail["asset_path"]
            print(f"  {asset_path}")
    print()

    print(f"Assets Generated:")
    for job in successes:
        print(f"  {job['image_path']}")
    print(" ")
    for job in successes:
        print(f"  {job['scene_path']}")

else:
    print(f"Skipped {num_skipped} / {num_total} assets.")


# Cleanup
simulation_app.close()
