# SPDX-FileCopyrightText: Copyright (c) 2020-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Demonstrate RTX lidar sensor with ROS 2 PointCloud2 publishing."""

import argparse
import sys

from isaacsim import SimulationApp

parser = argparse.ArgumentParser()
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode")
args, _ = parser.parse_known_args()

# Example for creating a RTX lidar sensor and publishing PointCloud2 data
simulation_app = SimulationApp({"headless": False})
import carb
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni
import omni.replicator.core as rep
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.sensors.experimental.rtx import Lidar
from isaacsim.storage.native import get_assets_root_path

# Enable the ROS 2 bridge so the RtxLidar*ROS2Publish* writers are registered.
app_utils.enable_extension("isaacsim.ros2.bridge")
simulation_app.update()

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Loading the simple_room environment
stage_utils.add_reference_to_stage(
    assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/background"
)
simulation_app.update()

# Create the 3D rotating RTX Lidar. Example_Rotary scans at 10 Hz, so tick_rate must be 10
# (see isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate).
lidar = Lidar.create(
    path="/sensor",
    config="Example_Rotary",
    tick_rate=10.0,
    translations=[[0.0, 0.0, 1.0]],
)

# RTX sensors are cameras and must be assigned to their own render product.
hydra_texture = rep.create.render_product(lidar.paths[0], [1, 1], name="Isaac")

# Create a 2D solid-state-style RTX Lidar with the Example_Rotary_2D config.
lidar_2D = Lidar.create(
    path="/sensor_2D",
    config="Example_Rotary_2D",
    tick_rate=10.0,
    translations=[[0.0, 0.0, 1.0]],
)
hydra_texture_2D = rep.create.render_product(lidar_2D.paths[0], [1, 1], name="Isaac")

SimulationManager.setup_simulation(dt=1.0 / 60.0, device="cpu")
simulation_app.update()

# Create the PointCloud2 publisher pipeline for the 3D Lidar.
writer = rep.writers.get("RtxLidarROS2PublishPointCloud")
writer.initialize(topicName="point_cloud", frameId="base_scan")
writer.attach([hydra_texture])

# Visualize the 3D Lidar point cloud in the viewport.
debug_writer = rep.writers.get("RtxLidarDebugDrawPointCloud")
debug_writer.attach([hydra_texture])

# Create the LaserScan publisher pipeline for the 2D Lidar.
writer = rep.writers.get("RtxLidarROS2PublishLaserScan")
writer.initialize(topicName="scan", frameId="base_scan")
writer.attach([hydra_texture_2D])

# Visualize the 2D Lidar scan in the viewport.
debug_writer = rep.writers.get("RtxLidarDebugDrawPointCloud")
debug_writer.attach([hydra_texture_2D])

simulation_app.update()

app_utils.play()

frame_count = 0
while simulation_app.is_running():
    simulation_app.update()
    frame_count += 1
    if args.test and frame_count >= 10:
        break

# cleanup and shutdown
app_utils.stop()
simulation_app.close()
