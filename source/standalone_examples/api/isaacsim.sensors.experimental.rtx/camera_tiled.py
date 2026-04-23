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

"""Batch/tiled multi-camera rendering with TiledCameraSensor.

This example demonstrates how to:
- Create multiple cameras at different positions
- Use ``TiledCameraSensor`` for efficient batched rendering
- Retrieve data as a single tiled frame or as a batch of individual frames
- Access per-camera and tiled resolution properties
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Tiled multi-camera rendering example.")
parser.add_argument("--num-cameras", type=int, default=4, help="Number of cameras.")
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
from isaacsim.core.experimental.objects import Camera, Cube
from isaacsim.sensors.experimental.rtx import TiledCameraSensor

# =============================================================================
# CREATE SCENE
# =============================================================================

for i, (x, y, color) in enumerate([(3, 0, [1, 0, 0]), (5, 2, [0, 1, 0]), (4, -2, [0, 0, 1])]):
    Cube(f"/World/cube_{i}", sizes=1.0, positions=np.array([float(x), float(y), 0.5]), colors=color)

# =============================================================================
# CREATE MULTIPLE CAMERAS
# =============================================================================
# Place cameras at different positions around the scene.

for i in range(args.num_cameras):
    angle = 2 * np.pi * i / args.num_cameras
    x = 3.0 * np.cos(angle)
    y = 3.0 * np.sin(angle)
    Camera(
        f"/World/camera_{i}",
        positions=np.array([x, y, 1.0]),
    )

print(f"Created {args.num_cameras} cameras")

# =============================================================================
# CREATE TILED CAMERA SENSOR
# =============================================================================
# TiledCameraSensor uses ``rep.create.render_product_tiled`` to render all
# cameras into a single tiled texture, then provides methods to retrieve
# data as either a tiled frame or a batch of individual frames.

resolution = (240, 320)  # (height, width) per camera
sensor = TiledCameraSensor(
    "/World/camera_.*",  # regex to match all camera prims
    resolution=resolution,
    annotators=["rgb", "distance_to_image_plane"],
)

print(f"Created TiledCameraSensor:")
print(f"  Number of cameras: {len(sensor)}")
print(f"  Per-camera resolution: {sensor.resolution}")
print(f"  Tiled resolution: {sensor.tiled_resolution}")

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

    # Get batched data: shape (num_cameras, height, width, channels)
    rgb_batch, _ = sensor.get_data("rgb", tiled=False)

    # Get tiled data: shape (tiled_height, tiled_width, channels)
    rgb_tiled, _ = sensor.get_data("rgb", tiled=True)

    if rgb_batch is not None and not printed:
        printed = True
        print(f"\nFrame {frame_count}:")
        print(f"  Batched RGB shape: {rgb_batch.shape}")
        print(f"  Tiled RGB shape:   {rgb_tiled.shape}")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
