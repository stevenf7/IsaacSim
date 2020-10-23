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

import carb
import omni
from omni.isaac.synthetic_utils import OmniKitHelper, SyntheticDataHelper, DataWriter, DomainRandomization
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

# Default rendering parameters
RENDER_CONFIG = {
    "width": 600,
    "height": 600,
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 12,
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
}


class RandomScenario(torch.utils.data.IterableDataset):
    def __init__(self, scenario_path):

        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        self.sd_helper = SyntheticDataHelper()
        self.dr_helper = DomainRandomization()
        self.dr_helper.toggle_manual_mode()
        self.stage = self.kit.get_stage()
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self.asset_path = nucleus_server + "/Isaac"
        if scenario_path is None:
            scenario_path = self.asset_path + "/Samples/Synthetic_Data/Stage/warehouse_with_sensors.usd"
        self.scenario_path = scenario_path
        self.data_writer = None

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
        self.dr_helper.randomize_once()
        self.kit.update()
        while self.kit.is_loading():
            self.kit.update()

        # Collect Groundtruth
        gt = self.sd_helper.get_groundtruth(
            [
                "rgb",
                "depthLinear",
                "instanceSegmentation",
                "semanticSegmentation",
                "boundingBox2DTight",
                "boundingBox2DLoose",
            ]
        )

        # RGB
        image = gt["rgb"]

        # Enable/disable sensor output and their format
        self._enable_rgb = True
        self._enable_depth = True
        self._enable_instance = True
        self._enable_semantic = True
        self._enable_bbox_2d_tight = True
        self._enable_bbox_2d_loose = True
        self._enable_depth_colorize = True
        self._enable_instance_colorize = True
        self._enable_semantic_colorize = True
        self._enable_bbox_2d_tight_colorize = True
        self._enable_bbox_2d_loose_colorize = True
        self._enable_depth_npy = True
        self._enable_instance_npy = True
        self._enable_semantic_npy = True
        self._enable_bbox_2d_tight_npy = True
        self._enable_bbox_2d_loose_npy = True
        self._num_worker_threads = 4
        self._output_folder = os.getcwd() + "/output"

        # Write to disk
        if self.data_writer is None:
            self.data_writer = DataWriter(self._output_folder, self._num_worker_threads)
            self.data_writer.start_threads()

        groundtruth = {
            "METADATA": {
                "image_id": str(self.cur_idx),
                "DEPTH": {},
                "INSTANCE": {},
                "SEMANTIC": {},
                "BBOX2DTIGHT": {},
                "BBOX2DLOOSE": {},
            },
            "DATA": {},
        }
        # RGB
        if self._enable_rgb:
            groundtruth["DATA"]["RGB"] = gt["rgb"]

        # Depth
        if self._enable_depth:
            groundtruth["DATA"]["DEPTH"] = gt["depthLinear"]
            groundtruth["METADATA"]["DEPTH"]["COLORIZE"] = self._enable_depth_colorize
            groundtruth["METADATA"]["DEPTH"]["NPY"] = self._enable_depth_npy

        # Instance Segmentation
        if self._enable_instance:
            instance_data = self.sd_helper._get_sensor_data(self.sd_helper.sd.SensorType.InstanceSegmentation, "uint32")
            instance_data_shape = instance_data.shape
            groundtruth["DATA"]["INSTANCE"] = instance_data
            groundtruth["METADATA"]["INSTANCE"]["WIDTH"] = instance_data_shape[1]
            groundtruth["METADATA"]["INSTANCE"]["HEIGHT"] = instance_data_shape[0]
            groundtruth["METADATA"]["INSTANCE"]["COLORIZE"] = self._enable_instance_colorize
            groundtruth["METADATA"]["INSTANCE"]["NPY"] = self._enable_instance_npy

        # Semantic Segmentation
        if self._enable_semantic:
            semantic_data = self.sd_helper._get_sensor_data(self.sd_helper.sd.SensorType.SemanticSegmentation, "uint32")
            semantic_data_shape = semantic_data.shape
            groundtruth["DATA"]["SEMANTIC"] = semantic_data
            groundtruth["METADATA"]["SEMANTIC"]["WIDTH"] = semantic_data_shape[1]
            groundtruth["METADATA"]["SEMANTIC"]["HEIGHT"] = semantic_data_shape[0]
            groundtruth["METADATA"]["SEMANTIC"]["COLORIZE"] = self._enable_semantic_colorize
            groundtruth["METADATA"]["SEMANTIC"]["NPY"] = self._enable_semantic_npy

        # 2D Tight BBox
        if self._enable_bbox_2d_tight:
            bboxes_2d_tight_sensor = self.sd_helper.sd.SensorType.BoundingBox2DTight
            bboxes_2d_tight_size = self.sd_helper.sd_interface.get_sensor_size(bboxes_2d_tight_sensor)
            bboxes_2d_tight_data = self.sd_helper.sd_interface.get_sensor_host_bounding_box_2d_buffer_array(
                bboxes_2d_tight_sensor, bboxes_2d_tight_size
            )
            groundtruth["DATA"]["BBOX2DTIGHT"] = bboxes_2d_tight_data
            groundtruth["METADATA"]["BBOX2DTIGHT"]["COLORIZE"] = self._enable_bbox_2d_tight_colorize
            groundtruth["METADATA"]["BBOX2DTIGHT"]["NPY"] = self._enable_bbox_2d_tight_npy

        # 2D Loose BBox
        if self._enable_bbox_2d_loose:
            bboxes_2d_loose_sensor = self.sd_helper.sd.SensorType.BoundingBox2DLoose
            bboxes_2d_loose_size = self.sd_helper.sd_interface.get_sensor_size(bboxes_2d_loose_sensor)
            bboxes_2d_loose_data = self.sd_helper.sd_interface.get_sensor_host_bounding_box_2d_buffer_array(
                bboxes_2d_loose_sensor, bboxes_2d_loose_size
            )
            groundtruth["DATA"]["BBOX2DLOOSE"] = bboxes_2d_loose_data
            groundtruth["METADATA"]["BBOX2DLOOSE"]["COLORIZE"] = self._enable_bbox_2d_loose_colorize
            groundtruth["METADATA"]["BBOX2DLOOSE"]["NPY"] = self._enable_bbox_2d_loose_npy

        self.data_writer.q.put(groundtruth)

        self.cur_idx += 1
        return image


if __name__ == "__main__":
    "Typical usage"
    import argparse

    parser = argparse.ArgumentParser("Dataset test")
    parser.add_argument("--scenario", type=str, help="Scenario to load from omniverse server")
    parser.add_argument("--num_frames", type=int, default=10, help="Number of frames to record")
    args = parser.parse_args()

    dataset = RandomScenario(args.scenario)

    # Iterate through dataset and visualize the output
    print("Loading materials. Will generate data soon...")
    for image in dataset:
        print("ID: ", dataset.cur_idx)
        if dataset.cur_idx == args.num_frames:
            break
