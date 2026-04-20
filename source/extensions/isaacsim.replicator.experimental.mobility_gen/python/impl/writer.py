# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Writer for saving MobilityGen recorded data to disk."""


import os
import shutil

import numpy as np
import PIL.Image

from .config import Config
from .occupancy_map import OccupancyMap


class MobilityGenWriter:
    """Writer for saving MobilityGen recordings to a directory.

    Args:
        path: The output directory path for the recording.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def write_state_dict_common(self, state_dict: dict, step: int) -> None:
        """Write the common (non-image) state dictionary to disk.

        Args:
            state_dict: The state dictionary to save.
            step: The current step index used as the filename.
        """
        dict_folder = os.path.join(self.path, "state", "common")
        if not os.path.exists(dict_folder):
            os.makedirs(dict_folder)
        state_dict_path = os.path.join(dict_folder, f"{step:08d}.npy")
        np.save(state_dict_path, state_dict)

    def write_state_dict_rgb(self, state_rgb: dict, step: int) -> None:
        """Write RGB image frames to disk.

        Args:
            state_rgb: A dict mapping camera name to RGB numpy array.
            step: The current step index used as the filename.
        """
        for name, value in state_rgb.items():
            if value is not None:
                image_folder = os.path.join(self.path, "state", "rgb", name)
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                image_path = os.path.join(image_folder, f"{step:08d}.jpg")
                image = PIL.Image.fromarray(value)
                image.save(image_path)

    def write_state_dict_segmentation(self, state_segmentation: dict, step: int) -> None:
        """Write segmentation image frames to disk.

        Args:
            state_segmentation: A dict mapping camera name to segmentation numpy array.
            step: The current step index used as the filename.
        """
        for name, value in state_segmentation.items():
            if value is not None:
                image_folder = os.path.join(self.path, "state", "segmentation", name)
                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)
                image_path = os.path.join(image_folder, f"{step:08d}.png")
                image = PIL.Image.fromarray(value)
                image.save(image_path)

    def write_state_dict_depth(self, state_np: dict, step: int) -> None:
        """Write depth images to disk as 16-bit inverse depth PNGs.

        Args:
            state_np: A dict mapping camera name to depth numpy array.
            step: The current step index used as the filename.
        """
        for name, value in state_np.items():
            if value is not None:
                output_folder = os.path.join(self.path, "state", "depth", name)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                # Inverse depth 16bit
                inverse_depth = 1.0 / (1.0 + value)
                inverse_depth = (65535 * inverse_depth).astype(np.uint16)
                image = PIL.Image.fromarray(inverse_depth, "I;16")

                output_path = os.path.join(output_folder, f"{step:08d}.png")

                image.save(output_path)

    def write_state_dict_normals(self, state_np: dict, step: int) -> None:
        """Write surface normals frames to disk as .npy files.

        Args:
            state_np: A dict mapping camera name to normals numpy array.
            step: The current step index used as the filename.
        """
        for name, value in state_np.items():
            if value is not None:
                output_folder = os.path.join(self.path, "state", "normals", name)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                output_path = os.path.join(output_folder, f"{step:08d}.npy")
                np.save(output_path, value)

    def copy_stage(self, input_path: str) -> None:
        """Copy the stage USD file to the recording directory.

        Args:
            input_path: The source path to the USD or USDZ stage file.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if input_path.endswith(".usdz"):
            shutil.copyfile(input_path, os.path.join(self.path, "stage.usdz"))
        else:
            shutil.copyfile(input_path, os.path.join(self.path, "stage.usd"))

    def write_config(self, config: Config) -> None:
        """Write the scenario configuration to disk as JSON.

        Args:
            config: The Config object to serialize and save.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(os.path.join(self.path, "config.json"), "w") as f:
            f.write(config.to_json())

    def write_occupancy_map(self, occupancy_map: OccupancyMap) -> None:
        """Write the occupancy map to disk in ROS format.

        Args:
            occupancy_map: The OccupancyMap to save.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        occupancy_map.save_ros(os.path.join(self.path, "occupancy_map"))

    def copy_init(self, other_path: str) -> None:
        """Copy the initialization data (stage, config, occupancy map) from another recording.

        Args:
            other_path: The source recording directory to copy from.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if os.path.exists(os.path.join(other_path, "stage.usdz")):
            shutil.copyfile(os.path.join(other_path, "stage.usdz"), os.path.join(self.path, "stage.usdz"))
        else:
            shutil.copyfile(os.path.join(other_path, "stage.usd"), os.path.join(self.path, "stage.usd"))
        shutil.copyfile(os.path.join(other_path, "config.json"), os.path.join(self.path, "config.json"))
        shutil.copytree(os.path.join(other_path, "occupancy_map"), os.path.join(self.path, "occupancy_map"))
