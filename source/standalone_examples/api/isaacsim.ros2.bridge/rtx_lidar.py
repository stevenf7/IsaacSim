# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import omni.kit.viewport.utility
import omni.replicator.core as rep
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf

# enable ROS2 bridge extension
app_utils.enable_extension("isaacsim.ros2.bridge")

simulation_app.update()


# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

simulation_app.update()
# Loading the simple_room environment
stage_utils.add_reference_to_stage(
    assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/background"
)
simulation_app.update()

# Create the lidar sensor that generates data into "RtxSensorCpu"
# Sensor needs to be rotated 90 degrees about X so that its Z up

# Possible options are Example_Rotary and Example_Solid_State
# drive sim applies 0.5,-0.5,-0.5,w(-0.5), we have to apply the reverse
_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor",
    parent=None,
    config="Example_Rotary",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),  # Gf.Quatd is w,i,j,k
)

# RTX sensors are cameras and must be assigned to their own render product
hydra_texture = rep.create.render_product(sensor.GetPath(), [1, 1], name="Isaac")

# Additionally, create a 2D lidar sensor with Example_Rotary_2D config
_, sensor_2D = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor_2D",
    parent=None,
    config="Example_Rotary_2D",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),  # Gf.Quatd is w,i,j,k
)

# RTX sensors are cameras and must be assigned to their own render product
hydra_texture_2D = rep.create.render_product(sensor_2D.GetPath(), [1, 1], name="Isaac")

SimulationManager.setup_simulation(dt=1.0 / 60.0, device="cpu")
simulation_app.update()

# Create Point cloud publisher pipeline in the post process graph
writer = rep.writers.get("RtxLidar" + "ROS2PublishPointCloud")
writer.initialize(topicName="point_cloud", frameId="base_scan")
writer.attach([hydra_texture])

# Create the Point Clouddebug draw pipeline in the post process graph
writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
writer.attach([hydra_texture])

# Create Laser Scan publisher pipeline in the post process graph
writer = rep.writers.get("RtxLidar" + "ROS2PublishLaserScan")
writer.initialize(topicName="scan", frameId="base_scan")
writer.attach([hydra_texture_2D])

# Create the Laser Scan debug draw pipeline in the post process graph
writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
writer.attach([hydra_texture_2D])

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
