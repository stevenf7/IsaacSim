# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import argparse
import os
import signal
import sys

from omni.isaac.kit import SimulationApp

from input import Parser
from distributions import Walk
from output import Logger, OutputManager
from scene import SceneManager, SensorManager
from sampling import Sampler


class Generator:
    def __init__(self, params, index, output_dir):
        """ Construct Generator. Start simulator and prepare for generation. """

        self.params = params
        self.index = index
        self.output_dir = output_dir

        self.sample = Sampler().sample

        # Start Simulator
        Logger.start_log_item("start-up")
        Logger.print("Isaac Sim starting up...")

        config = {
            "renderer": "RayTracedLighting",
            "samples_per_pixel_per_frame": 12,
            "headless": self.sample("headless"),
            "sync_loads": True,
        }

        self.sim_app = SimulationApp(config)

        from omni.isaac.core import SimulationContext

        self.sim_context = SimulationContext()

        # Set-up Replicator
        Logger.print("Replicator setting up...")

        self.num_samples = self.sample("num_samples")

        self.scene_manager = SceneManager(self.sim_app, self.sim_context)
        self.sensor_manager = SensorManager(self.sim_app, self.sim_context)
        self.output_manager = OutputManager(self.sim_app, self.sim_context, self.sensor_manager, self.output_dir)

        Logger.content_log_dir = self.output_manager.content_log_dir

        self.initialize_walks(self.params)

        # Set-up exit message
        signal.signal(signal.SIGINT, self.handle_exit)

        Logger.finish_log_item()

    def handle_exit(self, *args, **kwargs):
        print("exiting dataset generation...")

    def initialize_walks(self, params):
        """ Initialize all parameters that are walks. """

        for key, val in params.items():
            if type(val) is dict:
                self.initialize_walks(val)
            elif type(val) is Walk:
                # TODO: update
                pass

    def generate_sample(self):
        """ Generate 1 dataset sample. Returns captured groundtruth data. """

        self.scene_manager.prepare_scene(self.index)

        cam_data = self.sensor_manager.place_camera()

        self.scene_manager.populate_scene(cam_data)

        self.scene_manager.update_scene()

        groundtruth = self.output_manager.capture_groundtruth(self.index)

        self.scene_manager.finish_scene()

        return groundtruth


def get_output_dir(params):
    """ Determine output directory. """

    if params["output_dir"].startswith("/"):
        output_dir = params["output_dir"]
    else:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "datasets", params["output_dir"])
    return output_dir


def get_starting_index(params, output_dir):
    """ Determine starting index of dataset. """

    if params["overwrite"]:
        return 0

    output_data_dir = os.path.join(output_dir, "data")
    if not os.path.exists(output_data_dir):
        return 0

    def find_min_missing(indices):
        indices.sort()
        for i in range(indices[-1]):
            if i not in indices:
                return i
        return indices[-1]

    sensor_dirs = [os.path.join(output_data_dir, sub_dir) for sub_dir in os.listdir(output_data_dir)]

    min_indices = []
    for sensor_dir in sensor_dirs:
        data_dirs = [os.path.join(sensor_dir, sub_dir) for sub_dir in os.listdir(sensor_dir)]
        for data_dir in data_dirs:
            indices = []
            for filename in os.listdir(data_dir):
                try:
                    index = int(filename[: filename.rfind(".")])
                    indices.append(index)
                except:
                    pass
            min_index = find_min_missing(indices)
            min_indices.append(min_index)

    if min_indices:
        minest_index = min(min_indices)
        return minest_index + 1
    else:
        return 0


def assert_dataset_complete(params, index):
    """ Check if dataset is already complete. """

    num_samples = params["num_samples"]
    if index >= num_samples:
        print(
            'Dataset is completed. Number of generated samples {} satifies "num_samples" {}'.format(index, num_samples)
        )
        sys.exit()
    else:
        print("Starting at index ", index)

    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        default="parameters/warehouse.yaml",
        help="Path to input parameter file, relative to replicator directory.",
    )
    parser.add_argument(
        "--input-mount", type=str, default="/", help="Path to mount referenced in input parameter file via ~."
    )
    parser.add_argument("--output", type=str, help="Output directory.")
    parser.add_argument("--num-samples", type=int, help="Num of samples in the dataset.")
    parser.add_argument(
        "--no-overwrite",
        default=False,
        action="store_true",
        help="Begin generating dataset at the last sample's index.",
    )
    parser.add_argument("--headless", default=False, action="store_true", help="Do not launch Isaac SIM window.")
    parser.add_argument(
        "--visualize-models",
        default=False,
        action="store_true",
        help="Visualize all object models defined in input parameter file, instead of generating a dataset.",
    )
    args, _ = parser.parse_known_args()

    # Parse input parameter file
    parser = Parser(args)
    params = parser.parse_input()
    Sampler.params = params

    # Determine output directory
    output_dir = get_output_dir(params)

    # Run Replicator in Visualize mode
    if args.visualize_models:
        from visualize import Visualizer

        print("Visualizing object models...")
        visuals = Visualizer(parser, params, output_dir)
        visuals.visualize_models()
        sys.exit()

    # Set verbose mode
    Logger.verbose = params["verbose"]

    # Get starting index of dataset
    index = get_starting_index(params, output_dir)

    # Check if dataset is already complete
    assert_dataset_complete(params, index)

    # Initialize generator
    generator = Generator(params, index, output_dir)

    # Generate dataset
    while generator.index < params["num_samples"]:
        generator.generate_sample()
        generator.index += 1

    generator.sim_app.close()
