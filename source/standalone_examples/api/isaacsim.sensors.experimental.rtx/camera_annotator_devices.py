# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Retrieve camera annotator data on different devices (CPU vs CUDA).

This example demonstrates how to:
- Use ``CameraSensor.get_data()`` to retrieve data on the default device (CUDA)
- Use the ``out`` parameter with a pre-allocated warp array to control the output device
- Compare GPU and CPU data retrieval for RGB and depth annotators
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Camera annotator device selection example.")
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
import warp as wp
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera

# =============================================================================
# CREATE SCENE
# =============================================================================

for i, (x, y, color) in enumerate([(3, 0, [1, 0, 0]), (5, 2, [0, 1, 0]), (4, -2, [0, 0, 1])]):
    Cube(f"/World/cube_{i}", sizes=1.0, positions=np.array([float(x), float(y), 0.5]), colors=color)

# =============================================================================
# CREATE CAMERA SENSOR
# =============================================================================

resolution = (480, 640)
cam = RtxCamera("/World/camera", translations=np.array([0.0, 0.0, 0.5]))
sensor = CameraSensor(cam, resolution=resolution, annotators=["rgb", "distance_to_image_plane"])

# =============================================================================
# PRE-ALLOCATE OUTPUT ARRAYS
# =============================================================================
# Using the ``out`` parameter lets you control:
# 1. Which device the data lives on (CPU or CUDA)
# 2. Memory reuse across frames (no allocation per frame)

rgb_gpu = wp.empty((*resolution, 3), dtype=wp.uint8, device="cuda:0")
depth_gpu = wp.empty((*resolution, 1), dtype=wp.float32, device="cuda:0")

# =============================================================================
# RUN SIMULATION AND RETRIEVE DATA
# =============================================================================

timeline = omni.timeline.get_timeline_interface()
timeline.play()

frame_count = 0
printed = False

while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1

    # Default: data returned on CUDA
    rgb_default, _ = sensor.get_data("rgb")
    if rgb_default is None:
        continue

    # Once data is flowing, demonstrate pre-allocated output arrays
    if not printed:
        printed = True

        # GPU output via pre-allocated array (same device, no copy overhead)
        rgb_on_gpu, _ = sensor.get_data("rgb", out=rgb_gpu)

        # Depth on GPU via pre-allocated array
        depth_on_gpu, _ = sensor.get_data("distance_to_image_plane", out=depth_gpu)

        print(f"\nFrame {frame_count}:")
        print(f"  Default RGB — device: {rgb_default.device}, shape: {rgb_default.shape}")
        print(f"  GPU RGB     — device: {rgb_on_gpu.device}, shape: {rgb_on_gpu.shape}")
        print(f"  GPU Depth   — device: {depth_on_gpu.device}, shape: {depth_on_gpu.shape}")

        # To get data on CPU, use .numpy() on the default CUDA result
        rgb_np = rgb_default.numpy()
        print(f"  As numpy:   shape={rgb_np.shape}, dtype={rgb_np.dtype}")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
