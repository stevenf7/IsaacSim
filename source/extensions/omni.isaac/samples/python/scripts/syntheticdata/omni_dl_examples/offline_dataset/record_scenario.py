#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Generate offline synthetic dataset
"""


import asyncio
import os
import torch
import numpy as np

import omni
from omni_dl_examples.helpers import OmniKitHelper, SyntheticDataHelper, DataWriter
from omni.isaac.dr import _dr

# Default rendering parameters
RENDER_CONFIG = {"width": 600, "height": 600, "renderer": "PathTracing", "samples_per_pixel_per_frame": 12}


class RandomScenario(torch.utils.data.IterableDataset):
    def __init__(self, scenario_path):

        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        self.sd_helper = SyntheticDataHelper()
        self.stage = self.kit.get_stage()
        self.scenario_path = scenario_path
        self.data_writer = None
        self.dr = _dr.acquire_dr_interface()
        self.dr.toggle_manual_mode()

        self._setup_world(scenario_path)
        self.cur_idx = 0

    async def load_stage(self, path):
        await omni.kit.asyncapi.open_stage(path)

    def _setup_world(self, scenario_path):
        # Load scenario
        setup_task = asyncio.ensure_future(self.load_stage(scenario_path))
        while not setup_task.done():
            self.kit.update()
        self.kit.update()

    def __iter__(self):
        return self

    def __next__(self):
        # step once and then wait for materials to load
        self.dr.randomize_once()
        self.kit.update()
        while self.kit.is_loading():
            self.kit.update()

        # Collect Groundtruth
        gt = self.sd_helper.get_groundtruth(["rgb", "depth", "instanceSegmentation"])

        # RGB
        image = gt["rgb"]

        # Write to disk
        if self.data_writer is None:
            self.data_writer = DataWriter(os.getcwd() + "/output")
            self.data_writer.start_threads()
        groundtruth = {"metadata": {"image_id": str(self.cur_idx)}, "data": {}}
        groundtruth["data"]["rgb"] = gt["rgb"]
        groundtruth["data"]["depth"] = gt["depth"]
        groundtruth["data"]["instanceSegmentation"] = self.sd_helper._get_sensor_data(
            self.sd_helper.sd.SensorType.InstanceSegmentation, "uint32"
        )
        self.data_writer.q.put(groundtruth)

        self.cur_idx += 1
        return image


if __name__ == "__main__":
    "Typical usage"
    import argparse
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser("Dataset test")
    parser.add_argument(
        "--scenario",
        type=str,
        default="omniverse://drivesim-dev/Users/sdebnath/debris_scenario.usd",
        help="Scenario to load from omniverse server",
    )
    args = parser.parse_args()

    dataset = RandomScenario(args.scenario)

    # Iterate through dataset and visualize the output
    plt.ion()
    _, axes = plt.subplots(1, 1, figsize=(10, 5))
    plt.tight_layout()
    print("Generating data...")
    for image in dataset:
        axes.clear()
        axes.axis("off")

        axes.imshow(image)

        plt.draw()
        plt.pause(0.01)
