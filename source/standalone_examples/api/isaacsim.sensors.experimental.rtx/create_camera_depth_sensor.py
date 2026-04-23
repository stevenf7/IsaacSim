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

"""Create a depth camera sensor with multiple depth annotators.

This example demonstrates how to:
- Create a ``SingleViewDepthCameraSensor`` with depth-specific annotators
- Compare different depth outputs: distance, imager, point cloud
- Access depth sensor parameters
"""

import argparse

from isaacsim import SimulationApp

parser = argparse.ArgumentParser(description="Create camera depth sensor example.")
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

for i, (x, y) in enumerate([(3, 0), (5, 2), (4, -2), (8, 1)]):
    Cube(f"/World/cube_{i}", sizes=1.0, positions=np.array([float(x), float(y), 0.5]))

# =============================================================================
# CREATE DEPTH CAMERA SENSOR
# =============================================================================

cam = RtxCamera("/World/depth_cam", translations=np.array([0.0, 0.0, 0.5]))

sensor = SingleViewDepthCameraSensor(
    cam,
    resolution=(480, 640),
    annotators=[
        "depth_sensor_distance",
        "depth_sensor_imager",
        "depth_sensor_point_cloud_position",
    ],
)
sensor.set_enabled_post_processing(True)

print(f"Created depth camera with annotators: {sensor.annotators}")

# =============================================================================
# RUN SIMULATION
# =============================================================================

timeline = omni.timeline.get_timeline_interface()
timeline.play()

frame_count = 0
printed = False

while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1

    distance, _ = sensor.get_data("depth_sensor_distance")
    imager, _ = sensor.get_data("depth_sensor_imager")
    point_cloud, _ = sensor.get_data("depth_sensor_point_cloud_position")

    if distance is not None and not printed:
        printed = True
        print(f"\nFrame {frame_count}:")
        print(f"  depth_sensor_distance shape: {distance.shape}")
        print(f"  depth_sensor_imager shape:   {imager.shape if imager is not None else 'N/A'}")
        print(f"  point_cloud shape:           {point_cloud.shape if point_cloud is not None else 'N/A'}")

    if args.test and frame_count >= 20:
        break

timeline.stop()
simulation_app.close()
