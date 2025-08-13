from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import argparse
import csv
import os
import sys
from pathlib import Path

import carb
from isaacsim.storage.native import find_files_recursive, get_assets_root_path

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../tools/thumbnail_generator"))
from render_asset_utils import AssetRenderer


def download_thumbnails_for_paths(
    file_paths,
    version,
    output_dir="./tools/isaac/robot_asset_autogenerate/thumbnails",
    resolution=(1920, 1080),
    environment_path=None,
    force_create_scene=False,
):
    """Download thumbnails for a list of file paths.

    Args:
        file_paths: List of USD file paths to generate thumbnails for.
        output_dir: Directory to save thumbnail images.
        resolution: Tuple of (width, height) for thumbnail resolution.
        environment_path: Path to environment USD file for rendering.
        force_create_scene: Whether to force recreate scene files.

    Returns:
        List of successfully generated thumbnail paths.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the asset renderer
    renderer = AssetRenderer()

    # Set default environment if not provided
    if environment_path is None:
        environment_path = renderer._default_scene

    successful_thumbnails = []
    failed_paths = []

    # includes both capital and lowercase in case of files that are only different in capitalization
    exclude_paths = [
        "/.thumbs",
        "/parts",
        "/Parts",
        "/Materials",
        "/materials",
        "/Legacy",
        "/legacy",
        "/Props",
        "/props",
        "/DetailedProps",
        "/detailedprops",
        "/Config",
        "/config",
        "/Configuration",
        "/configuration",
        "/Grippers",
        "/grippers",
        "/Variants",
        "/variants",
        "/Physics",
        "/physics",
        "/Sensors_merged",
        "/sensors_merged",
        "/Sensors_merged_stage",
        "_sensors_merged",
        "/nova_carter_dev_kit",
        "/nova_dev_kit",
        "/payloads",
        "/HighResProps",
    ]
    failed_exceptions = {}
    for file_path in file_paths:
        if not any(exclude_path in file_path for exclude_path in exclude_paths):
            try:
                # Build job configuration

                # path = Path(file_path[49:].replace("/", "_").replace(" ", "_").replace("-", "_"))
                path = Path(file_path.split("Isaac/Robots/")[1].replace("/", "_").replace(" ", "_").replace("-", "_"))

                job_config = {
                    "asset_path": file_path,
                    "image_path": output_dir
                    + "/isim_"
                    + version
                    + "_full_ref_viewport_Isaac_Robots_"
                    + path.stem
                    + ".usd.png",
                    "resolution": resolution,
                    "environment_path": environment_path,
                }

                print(f"Generating thumbnail for: {file_path}")

                # Create the thumbnail

                success = renderer.create_image(
                    job_config, reposition_camera=True, force_create_scene=force_create_scene
                )

                if success:
                    successful_thumbnails.append(job_config["image_path"])
                    print(f"Successfully generated: {job_config['image_path']}")
                else:
                    failed_paths.append(file_path)
                    failed_exceptions[file_path] = "Failed to generate thumbnail"
                    print(f"Failed to generate thumbnail for: {file_path}")

            except Exception as e:
                failed_paths.append(file_path)
                failed_exceptions[file_path] = str(e)
                print(f"Error generating thumbnail for {file_path}: {str(e)}")

    # Print summary
    print(f"\nThumbnail generation complete:")
    print(f"Successfully generated: {len(successful_thumbnails)} thumbnails")
    print(f"Failed: {len(failed_paths)} files")

    if failed_paths:
        print("Failed files:")
        for path in failed_paths:
            print(f"  {path}")
            if path in failed_exceptions:
                print(f"  {failed_exceptions[path]}")

    return successful_thumbnails


def main():
    """Main function to handle command line arguments and generate thumbnails."""
    parser = argparse.ArgumentParser(description="Download thumbnails for USD files")
    parser.add_argument(
        "--input_file",
        "-i",
        required=False,
        default="./tools/isaac/robot_asset_autogenerate/outputs/robot_list.csv",
        help="File containing list of USD file paths",
    )
    parser.add_argument(
        "--output-dir",
        default="./tools/isaac/robot_asset_autogenerate/thumbnails",
        help="Output directory for thumbnails",
    )
    parser.add_argument("--resolution", default="1920x1080", help="Thumbnail resolution (WIDTHxHEIGHT)")
    parser.add_argument("--force-create-scene", action="store_true", help="Force recreate scene files")
    parser.add_argument("--version", "-v", required=True, help="Version of Isaac Sim to use for the RST documentation")

    args = parser.parse_args()

    # Parse resolution
    try:
        width, height = map(int, args.resolution.split("x"))
        resolution = (width, height)
    except ValueError:
        print("Error: Resolution must be in WIDTHxHEIGHT format (e.g., 256x256)")
        return

    # Read file paths from input file
    try:
        with open(args.input_file, "r", newline="") as f:
            reader = csv.reader(f)
            file_paths = []

            for row in reader:
                if row and row[0].strip():  # Check if row exists and first column is not empty
                    file_paths.append(row[0].strip())

            print(f"Loaded {len(file_paths)} file paths")
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found")
        return
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return

    # Generate thumbnails
    successful_thumbnails = download_thumbnails_for_paths(
        file_paths=file_paths,
        version=args.version,
        output_dir=args.output_dir,
        resolution=resolution,
        environment_path=None,
        force_create_scene=args.force_create_scene,
    )

    print(f"\nThumbnails saved to: {args.output_dir}")

    simulation_app.close()


if __name__ == "__main__":
    main()
