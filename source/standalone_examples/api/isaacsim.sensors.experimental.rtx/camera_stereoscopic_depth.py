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

"""Configure a single-view stereoscopic depth camera sensor.

This example demonstrates how to:
- Create a camera with ``SingleViewDepthCameraSensor`` for depth simulation
- Configure depth-specific parameters (baseline, focal length, disparity, noise)
- Retrieve depth data from the ``depth_sensor_distance`` annotator

The single-view depth sensor simulates a stereo camera pair from a single viewpoint,
computing disparity and depth using the ``OmniSensorDepthSensorSingleViewAPI`` schema
applied to the render product.
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Single-view stereoscopic depth camera example.")
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import RtxCamera, SingleViewDepthCameraSensor

# =============================================================================
# CREATE SCENE
# =============================================================================

for i, dist in enumerate([2.0, 5.0, 10.0, 20.0]):
    Cube(
        f"/World/cube_{i}",
        sizes=1.0,
        positions=np.array([dist, 0.0, 0.5]),
        colors=[float(i % 2), float((i + 1) % 2), 0.5],
    )

# =============================================================================
# CREATE CAMERA
# =============================================================================

cam = RtxCamera(
    "/World/depth_camera",
    translations=np.array([0.0, 0.0, 0.5]),
)

# Set optical parameters
cam.camera.set_focal_lengths(18.0)
cam.camera.set_clipping_ranges(0.1, 100.0)

print(f"Created depth camera at {cam.paths[0]}")

# =============================================================================
# CREATE DEPTH SENSOR
# =============================================================================
# SingleViewDepthCameraSensor inherits from CameraSensor and adds the
# OmniSensorDepthSensorSingleViewAPI schema to the render product,
# enabling depth-specific annotators and configuration.

sensor = SingleViewDepthCameraSensor(
    cam,
    resolution=(480, 640),
    annotators=["depth_sensor_distance"],
)

# Configure depth sensor parameters
sensor.set_sensor_baseline(55.0)  # mm — stereo baseline
sensor.set_sensor_focal_length(897.0)  # pixels — simulated focal length
sensor.set_sensor_size(1280.0)  # pixels — sensor width
sensor.set_sensor_maximum_disparity(110.0)  # max disparity pixels
sensor.set_sensor_disparity_confidence(0.7)  # confidence threshold
sensor.set_sensor_distance_cutoffs(minimum_distance=0.5, maximum_distance=100.0)
sensor.set_sensor_noise_parameters(noise_mean=0.25, noise_sigma=0.25)
sensor.set_enabled_post_processing(True)

print(f"Depth sensor configured:")
print(f"  Baseline: {sensor.get_sensor_baseline()} mm")
print(f"  Focal length: {sensor.get_sensor_focal_length()} px")
print(f"  Disparity range: 0 - {sensor.get_sensor_maximum_disparity()} px")
print(f"  Distance cutoffs: {sensor.get_sensor_distance_cutoffs()}")

# =============================================================================
# RUN SIMULATION AND RETRIEVE DEPTH DATA
# =============================================================================

timeline = omni.timeline.get_timeline_interface()
timeline.play()

frame_count = 0
printed = False

while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1

    depth_data, _ = sensor.get_data("depth_sensor_distance")

    if depth_data is not None and not printed:
        printed = True
        depth_np = depth_data.numpy()
        print(f"\nFrame {frame_count}:")
        print(f"  Depth shape: {depth_data.shape}")
        print(f"  Depth range: [{depth_np.min():.2f}, {depth_np.max():.2f}] meters")
        # Count valid depth samples (finite, positive)
        valid = np.isfinite(depth_np) & (depth_np > 0)
        print(f"  Valid samples: {valid.sum()} / {depth_np.size} ({100*valid.mean():.1f}%)")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
