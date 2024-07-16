import csv
import filecmp
import json
import os

import numpy as np
from PIL import Image


# Compare the recorded datasets against the golden datasets (USDA, CSV, JSON, PNG files and content)
def compare_data(
    output_root_folder,
    golden_root_folder,
    num_datasets,
    num_render_products,
    raise_exception=True,
    print_if_identical=False,
):
    print(f"[AR] Comparing\n\tOutput:{output_root_folder}\n\tGolden:{golden_root_folder}")

    # Create the dataset folders
    output_dataset_folder = [
        os.path.join(output_root_folder, str(num_dataset).zfill(5)) for num_dataset in range(1, num_datasets + 1)
    ]
    golden_dataset_folder = [
        os.path.join(golden_root_folder, str(num_dataset).zfill(5)) for num_dataset in range(1, num_datasets + 1)
    ]

    # USDA files
    for output_folder, golden_folder in zip(output_dataset_folder, golden_dataset_folder):
        compare_usda_data(output_folder, golden_folder, num_render_products, raise_exception, print_if_identical)

    # CSV files
    for output_folder, golden_folder in zip(output_dataset_folder, golden_dataset_folder):
        compare_csv_data(output_folder, golden_folder, num_render_products, raise_exception, print_if_identical)

    # JSON files
    for output_folder, golden_folder in zip(output_dataset_folder, golden_dataset_folder):
        compare_json_files(output_folder, golden_folder, num_render_products, raise_exception, print_if_identical)

    # PNG files
    for output_folder, golden_folder in zip(output_dataset_folder, golden_dataset_folder):
        compare_png_files(output_folder, golden_folder, num_render_products, raise_exception, print_if_identical)


# Compare the USDA files in the selected dataset folder
def compare_usda_data(
    output_folder, golden_folder, num_render_products, raise_exception=True, print_if_identical=False
):
    print(f"[AR][USDA] Dataset: {os.path.basename(os.path.normpath(output_folder))}")

    # Compare variation.usda (e.g. 'data/00001/variation.usda')
    output_variation_usda = os.path.join(output_folder, "variation.usda")
    golden_variation_usda = os.path.join(golden_folder, "variation.usda")
    file_paths = f"\n\t{output_variation_usda}\n\t{golden_variation_usda}"
    print(f"[AR][USDA] Comparing: {file_paths}")

    # Check that the files exist
    if not os.path.exists(output_variation_usda) or not os.path.exists(golden_variation_usda):
        if raise_exception:
            raise Exception(f"Missing USDA file:{file_paths}")
        else:
            print(f"[FAIL]")

    # Compare the content of the files
    if not filecmp.cmp(output_variation_usda, golden_variation_usda, shallow=False):
        if raise_exception:
            raise Exception(f"Different USDA content:{file_paths}")
        else:
            print(f"[FAIL]")
    elif print_if_identical:
        print(f"[PASS]")

    # Compare simulation layers for each render product (e.g. 'data/00001/1/simulation_layer/*.usda')
    for rp_idx in range(1, num_render_products + 1):
        output_simulation_layer_folder = os.path.join(output_folder, f"{rp_idx}", "simulation_layer")
        golden_simulation_layer_folder = os.path.join(golden_folder, f"{rp_idx}", "simulation_layer")
        output_usda_filenames = sorted([f for f in os.listdir(output_simulation_layer_folder) if f.endswith(".usda")])
        golden_usda_filenames = sorted([f for f in os.listdir(golden_simulation_layer_folder) if f.endswith(".usda")])

        # Make sure the number of USDa files match, otherwise skip
        if len(output_usda_filenames) != len(golden_usda_filenames):
            message = f"Wrong number of USDA files in {output_simulation_layer_folder}"
            if raise_exception:
                raise Exception(message)
            else:
                print(message)
            continue

        for output_filename, golden_filename in zip(output_usda_filenames, golden_usda_filenames):
            output_usda_path = os.path.join(output_simulation_layer_folder, output_filename)
            golden_usda_path = os.path.join(golden_simulation_layer_folder, golden_filename)
            file_paths = f"\n\t{output_usda_path}\n\t{golden_usda_path}"
            print(f"[AR][USDA]Comparing: {file_paths}")

            # Make sure the filenames match, otherwise skip
            if output_filename != golden_filename:
                if raise_exception:
                    raise Exception(f"Different filenames:{file_paths}")
                else:
                    print(f"[FAIL] Different filenames\n")
                continue

            # Make sure the files exist
            if not os.path.exists(output_usda_path) or not os.path.exists(golden_usda_path):
                if raise_exception:
                    raise Exception(f"Missing USDA file:{file_paths}")
                else:
                    print(f"[FAIL]\n")
                continue

            # Compare the USDa files
            if not filecmp.cmp(output_usda_path, golden_usda_path, shallow=False):
                if raise_exception:
                    raise Exception(f"Different USDA content:{file_paths}")
                else:
                    print(f"[FAIL]\n")
            elif print_if_identical:
                print(f"[PASS]\n")


# Compare the CSV files in the selected dataset folder
def compare_csv_data(output_folder, golden_folder, num_render_products, raise_exception=True, print_if_identical=False):
    print(f"[AR][CSV] Dataset: {os.path.basename(os.path.normpath(output_folder))}")

    # Load and parse CSV file into NumPy arrays
    def load_and_parse_csv(file_path):
        frames = []
        usd_positions = []
        fabric_positions = []
        with open(file_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                frames.append(int(row["Frame"]))
                usd_position = tuple(map(float, row["USD Position"].strip("()").split(", ")))
                usd_positions.append(usd_position)
                # NOTE: Fabric position is empty atm. using 0 as placeholder
                fabric_positions.append(0)
                # fabric_position = tuple(map(float, row["Fabric Position"].strip("()").split(", ")))
                # fabric_positions.append(fabric_position)

        frames = np.array(frames)
        usd_positions = np.array(usd_positions)
        fabric_positions = np.array(fabric_positions)
        return frames, usd_positions, fabric_positions

    # Compare the CSV files for each render product (e.g. 'data/00001/1/prim_info/*.csv')
    for rp_idx in range(1, num_render_products + 1):
        output_csv_folder = os.path.join(output_folder, f"{rp_idx}", "prim_info")
        golden_csv_folder = os.path.join(golden_folder, f"{rp_idx}", "prim_info")
        output_csv_filenames = sorted([f for f in os.listdir(output_csv_folder) if f.endswith(".csv")])
        golden_csv_filenames = sorted([f for f in os.listdir(golden_csv_folder) if f.endswith(".csv")])

        # Make sure the number of CSV files match, otherwise skip
        if len(output_csv_filenames) != len(golden_csv_filenames):
            message = f"Wrong number of CSV files in {output_csv_folder}"
            if raise_exception:
                raise Exception(message)
            else:
                print(message)
            continue

        # Iterate over the CSV files and compare the content
        for output_filename, golden_filename in zip(output_csv_filenames, golden_csv_filenames):
            output_csv_path = os.path.join(output_csv_folder, output_filename)
            golden_csv_path = os.path.join(golden_csv_folder, golden_filename)
            file_paths = f"\n\t{output_csv_path}\n\t{golden_csv_path}"
            print(f"[AR][CSV] Comparing:{file_paths}")

            # Make sure the filenames match, otherwise skip
            if output_filename != golden_filename:
                if raise_exception:
                    raise Exception(f"Different filenames:{file_paths}")
                else:
                    print(f"[FAIL] -- Different filenames\n")
                continue

            # Make sure the files exist
            if not os.path.exists(output_csv_path) or not os.path.exists(golden_csv_path):
                if raise_exception:
                    raise Exception(f"Missing CSV file:{file_paths}")
                else:
                    print(f"[FAIL]\n")
                continue

            # Load and parse the CSV files
            output_frames, output_usd_positions, output_fabric_positions = load_and_parse_csv(output_csv_path)
            golden_frames, golden_usd_positions, golden_fabric_positions = load_and_parse_csv(golden_csv_path)

            # Compare the CSV files content
            frames_diff = not np.array_equal(output_frames, golden_frames)
            usd_positions_diff = not np.allclose(output_usd_positions, golden_usd_positions)
            fabric_positions_diff = not np.allclose(output_fabric_positions, golden_fabric_positions)

            if frames_diff or usd_positions_diff or fabric_positions_diff:
                if raise_exception:
                    raise Exception(f"Different CSV content:{file_paths}")
                else:
                    print(f"[FAIL]\n")
            elif print_if_identical:
                print(f"[PASS]\n")


def compare_json_files(
    output_folder, golden_folder, num_render_products, raise_exception=True, print_if_identical=False
):
    print(f"[AR][JSON] Dataset: {os.path.basename(os.path.normpath(output_folder))}")

    # Compare the JSON files for each render product (e.g. 'data/00001/1/*.json')
    for rp_idx in range(1, num_render_products + 1):
        output_json_folder = os.path.join(output_folder, f"{rp_idx}")
        golden_json_folder = os.path.join(golden_folder, f"{rp_idx}")
        output_json_filenames = sorted([f for f in os.listdir(output_json_folder) if f.endswith(".json")])
        golden_json_filenames = sorted([f for f in os.listdir(golden_json_folder) if f.endswith(".json")])

        # Make sure the number of JSON files match, otherwise skip
        if len(output_json_filenames) != len(golden_json_filenames):
            message = f"Wrong number of JSON files in {output_json_folder}"
            if raise_exception:
                raise Exception(message)
            else:
                print(message)
            continue

        # Compare the JSON files content
        for output_filename, golden_filename in zip(output_json_filenames, golden_json_filenames):
            output_json_path = os.path.join(output_json_folder, output_filename)
            golden_json_path = os.path.join(golden_json_folder, golden_filename)
            file_paths = f"\n\t{output_json_path}\n\t{golden_json_path}"
            print(f"[AR][JSON] Comparing:{file_paths}")

            # Make sure the filenames match, otherwise skip
            if output_filename != golden_filename:
                if raise_exception:
                    raise Exception(f"Different filenames:{file_paths}")
                else:
                    print(f"[FAIL] -- Different filenames\n")
                continue

            # Make sure the files exist
            if not os.path.exists(output_json_path) or not os.path.exists(golden_json_path):
                if raise_exception:
                    raise Exception(f"Missing JSON file:{file_paths}")
                else:
                    print(f"[FAIL]\n")
                continue

            # Compare the JSON files content
            with open(output_json_path, "r") as output_json_file:
                output_json_data = json.load(output_json_file)
            with open(golden_json_path, "r") as golden_json_file:
                golden_json_data = json.load(golden_json_file)

            if output_json_data != golden_json_data:
                if raise_exception:
                    raise Exception(f"Different JSON content:{file_paths}")
                else:
                    print(f"[FAIL]\n")
            elif print_if_identical:
                print(f"[PASS]\n")


def compare_png_files(
    output_folder, golden_folder, num_render_products, raise_exception=True, print_if_identical=False
):
    print(f"[AR][PNG] Dataset: {os.path.basename(os.path.normpath(output_folder))}")

    # Compare the PNG files for each render product (e.g. 'data/00001/1/*.png')
    for rp_idx in range(1, num_render_products + 1):
        output_png_folder = os.path.join(output_folder, f"{rp_idx}")
        golden_png_folder = os.path.join(golden_folder, f"{rp_idx}")
        output_png_filenames = sorted([f for f in os.listdir(output_png_folder) if f.endswith(".png")])
        golden_png_filenames = sorted([f for f in os.listdir(golden_png_folder) if f.endswith(".png")])

        # Make sure the number of PNG files match, otherwise skip
        if len(output_png_filenames) != len(golden_png_filenames):
            message = f"Wrong number of PNG files in {output_png_folder}"
            if raise_exception:
                raise Exception(message)
            else:
                print(message)
            continue

        # Compare the PNG files pixel-wise
        for output_filename, golden_filename in zip(output_png_filenames, golden_png_filenames):
            output_png_path = os.path.join(output_png_folder, output_filename)
            golden_png_path = os.path.join(golden_png_folder, golden_filename)
            file_paths = f"\n\t{output_png_path}\n\t{golden_png_path}"
            print(f"[AR][PNG] Comparing:{file_paths}")

            # Make sure the filenames match, otherwise skip
            if output_filename != golden_filename:
                if raise_exception:
                    raise Exception(f"Different filenames:{file_paths}")
                else:
                    print(f"Different filenames\n")
                continue

            # Make sure the files exist
            if not os.path.exists(output_png_path) or not os.path.exists(golden_png_path):
                if raise_exception:
                    raise Exception(f"Missing PNG file:{file_paths}")
                else:
                    print(f"[FAIL]\n")
                continue

            # Get the image arrays
            output_image = Image.open(output_png_path)
            golden_image = Image.open(golden_png_path)
            output_image_array = np.array(output_image)
            golden_image_array = np.array(golden_image)

            # Compare the array shapes
            if output_image_array.shape != golden_image_array.shape:
                if raise_exception:
                    raise Exception(
                        f"Different image shape:{file_paths};\n{output_image_array.shape} != {golden_image_array.shape}\n"
                    )
                else:
                    print(f"FAIL] -- Different image shape; {output_image_array.shape} != {golden_image_array.shape}\n")

            # Compare the array content
            if not np.allclose(output_image_array, golden_image_array, atol=2):
                if raise_exception:
                    raise Exception(f"Different PNG content:{file_paths}")
                else:
                    print(f"[FAIL]\n")
            elif print_if_identical:
                print(f"[PASS]\n")
