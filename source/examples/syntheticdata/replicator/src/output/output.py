# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import shutil

import carb

from sampling import Sampler
from output import GenerateDisparity, DataWriter


class OutputManager:
    """ For managing Replicator outputs, including sending data to the data writer. """

    def __init__(self, sim_app, sim_context, sensor_manager, output_dir):
        """ Construct OutputManager. Start data writer threads and set-up output directories. """

        self.sim_app = sim_app
        self.sim_context = sim_context
        self.sensor_manager = sensor_manager
        self.output_dir = output_dir

        self.viewports = self.sensor_manager.viewports
        self.stage = self.sim_context.stage
        self.sample = Sampler().sample

        self.setup_data_output()

        max_queue_size = 500
        self.data_writer = DataWriter(self.output_data_dir, self.sample("num_data_writer_threads"), max_queue_size)
        self.data_writer.start_threads()

        from omni.isaac.synthetic_utils import SyntheticDataHelper

        self.sd_helper = SyntheticDataHelper()

        self.carb_settings = carb.settings.acquire_settings_interface()

    def setup_data_output(self):
        """ Create output directories and copy input files to output. """

        # Create output directories, as needed
        self.output_data_dir = os.path.join(self.output_dir, "data")
        self.parameter_dir = os.path.join(self.output_dir, "parameters")
        self.parameter_profiles_dir = os.path.join(self.parameter_dir, "profiles")
        self.content_log_dir = os.path.join(self.output_dir, "log")

        os.makedirs(self.output_data_dir, exist_ok=True)
        os.makedirs(self.parameter_profiles_dir, exist_ok=True)
        os.makedirs(self.content_log_dir, exist_ok=True)

        # Copy input parameters file to output
        input_file_name = os.path.basename(self.sample("input_file"))
        input_file_copy = os.path.join(self.parameter_dir, input_file_name)
        shutil.copy(self.sample("input_file"), input_file_copy)

        # Copy profile parameters file(s) to output
        if self.sample("profile_files"):
            for profile_file in self.sample("profile_files"):
                profile_file_name = os.path.basename(profile_file)
                profile_file_copy = os.path.join(self.parameter_profiles_dir, profile_file_name)
                shutil.copy(profile_file, profile_file_copy)

    def capture_groundtruth(self, index):
        """ Capture groundtruth data from Isaac Sim. Send data to data writer. """

        depths = []
        for i in range(len(self.viewports)):
            viewport_name, viewport_window = self.viewports[i]

            num_digits = len(str(self.sample("num_samples") - 1))
            id = str(index)
            id = id.zfill(num_digits)

            groundtruth = {
                "METADATA": {
                    "image_id": id,
                    "viewport_name": viewport_name,
                    "DEPTH": {},
                    "DEPTH_BOUNDARY": {},
                    "INSTANCE": {},
                    "SEMANTIC": {},
                    "BBOX2DTIGHT": {},
                    "BBOX2DLOOSE": {},
                    "BBOX3D": {},
                },
                "DATA": {},
            }

            gt_list = []
            if self.sample("rgb"):
                gt_list.append("rgb")
            if (self.sample("depth") or self.sample("depth_boundary")) or (
                self.sample("disparity") and self.sample("stereo")
            ):
                gt_list.append("depthLinear")
            if self.sample("instance_seg"):
                gt_list.append("instanceSegmentation")
            if self.sample("semantic_seg"):
                gt_list.append("semanticSegmentation")
            if self.sample("bbox_2d_tight"):
                gt_list.append("boundingBox2DTight")
            if self.sample("bbox_2d_loose"):
                gt_list.append("boundingBox2DLoose")
            if self.sample("bbox_3d"):
                gt_list.append("boundingBox3D")

            # Collect Groundtruth
            gt = self.sd_helper.get_groundtruth(gt_list, viewport_window)

            # RGB
            if gt["state"]["rgb"]:
                groundtruth["DATA"]["RGB"] = gt["rgb"]

            # Depth
            if "depthLinear" in gt["state"]:
                depth_data = gt["depthLinear"].squeeze()
                depths.append(depth_data)

            if i == 0 or self.sample("groundtruth_stereo"):
                # Depth
                if "depthLinear" in gt["state"]:
                    depth_data = gt["depthLinear"].squeeze()
                    if self.sample("depth"):
                        groundtruth["DATA"]["DEPTH"] = depth_data
                        groundtruth["METADATA"]["DEPTH"]["COLORIZE"] = self.sample("groundtruth_visual")
                        groundtruth["METADATA"]["DEPTH"]["NPY"] = True

                    if self.sample("depth_boundary"):
                        groundtruth["DATA"]["DEPTH_BOUNDARY"] = depth_data
                        groundtruth["METADATA"]["DEPTH_BOUNDARY"]["COLORIZE"] = False
                        groundtruth["METADATA"]["DEPTH_BOUNDARY"]["NPY"] = True

                # Instance Segmentation
                if "instanceSegmentation" in gt["state"]:
                    instance_data = gt["instanceSegmentation"][0]
                    groundtruth["DATA"]["INSTANCE"] = instance_data
                    groundtruth["METADATA"]["INSTANCE"]["WIDTH"] = instance_data.shape[1]
                    groundtruth["METADATA"]["INSTANCE"]["HEIGHT"] = instance_data.shape[0]
                    groundtruth["METADATA"]["INSTANCE"]["COLORIZE"] = self.sample("groundtruth_visual")
                    groundtruth["METADATA"]["INSTANCE"]["NPY"] = True

                # Semantic Segmentation
                if "semanticSegmentation" in gt["state"]:
                    semantic_data = gt["semanticSegmentation"]
                    semantic_data[semantic_data == 65535] = 0  # deals with invalid semantic id
                    groundtruth["DATA"]["SEMANTIC"] = semantic_data
                    groundtruth["METADATA"]["SEMANTIC"]["WIDTH"] = semantic_data.shape[1]
                    groundtruth["METADATA"]["SEMANTIC"]["HEIGHT"] = semantic_data.shape[0]
                    groundtruth["METADATA"]["SEMANTIC"]["COLORIZE"] = self.sample("groundtruth_visual")
                    groundtruth["METADATA"]["SEMANTIC"]["NPY"] = True

                # 2D Tight BBox
                if "boundingBox2DTight" in gt["state"]:
                    groundtruth["DATA"]["BBOX2DTIGHT"] = gt["boundingBox2DTight"]
                    groundtruth["METADATA"]["BBOX2DTIGHT"]["COLORIZE"] = self.sample("groundtruth_visual")
                    groundtruth["METADATA"]["BBOX2DTIGHT"]["NPY"] = True

                # 2D Loose BBox
                if "boundingBox2DLoose" in gt["state"]:
                    groundtruth["DATA"]["BBOX2DLOOSE"] = gt["boundingBox2DLoose"]
                    groundtruth["METADATA"]["BBOX2DLOOSE"]["COLORIZE"] = self.sample("groundtruth_visual")
                    groundtruth["METADATA"]["BBOX2DLOOSE"]["NPY"] = True

                # 3D BBox
                if "boundingBox3D" in gt["state"]:
                    groundtruth["DATA"]["BBOX3D"] = gt["boundingBox3D"]
                    groundtruth["METADATA"]["BBOX3D"]["COLORIZE"] = self.sample("groundtruth_visual")
                    groundtruth["METADATA"]["BBOX3D"]["NPY"] = True

                # Wireframe
                if self.sample("wireframe"):
                    gt_list = ["rgb"]
                    self.carb_settings.set("/rtx/wireframe/mode", 2.0)
                    self.sim_context.render()
                    gt = self.sd_helper.get_groundtruth(gt_list, viewport_window)
                    groundtruth["DATA"]["WIREFRAME"] = gt["rgb"]
                    self.carb_settings.set("/rtx/wireframe/mode", 0)
                    self.sim_context.render()

            if self.sample("write_data"):
                self.data_writer.q.put(groundtruth)

        # Disparity
        if self.sample("disparity") and self.sample("stereo"):
            depth1, depth2 = depths

            cam_intrinsics = self.sensor_manager.cam_intrinsics[0]
            gen_disp = GenerateDisparity(
                depth1,
                depth2,
                cam_intrinsics["fx"],
                cam_intrinsics["fy"],
                cam_intrinsics["cx"],
                cam_intrinsics["cy"],
                self.sample("stereo_baseline"),
            )
            disp_l, disp_r = gen_disp.get_disp()
            disparities = [disp_l, disp_r]

            for i in range(len(self.viewports)):
                viewport_name, viewport_window = self.viewports[i]
                groundtruth = {
                    "METADATA": {"image_id": id, "viewport_name": viewport_name, "DISPARITY": {}},
                    "DATA": {},
                }
                disparity_data = disparities[i]
                groundtruth["DATA"]["DISPARITY"] = disparity_data
                groundtruth["METADATA"]["DISPARITY"]["COLORIZE"] = self.sample("groundtruth_visual")
                groundtruth["METADATA"]["DISPARITY"]["NPY"] = True

                if self.sample("write_data"):
                    self.data_writer.q.put(groundtruth)

        return groundtruth
