# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import sys

# Example for creating a RTX lidar sensor and publishing PCL data
simulation_app = SimulationApp({"headless": False})
import omni
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import viewports, stage, nucleus
from omni.syntheticdata import sensors
import omni.kit.viewport.utility
from pxr import Gf

# enable ROS bridge extension
enable_extension("omni.isaac.ros_bridge")

simulation_app.update()

# check if rosmaster node is running
# this is to prevent this sample from waiting indefinetly if roscore is not running
# can be removed in regular usage
import rosgraph

if not rosgraph.is_master_online():
    carb.log_error("Please run roscore before executing this script")
    simulation_app.close()
    exit()


# Create a new viewport for the RTX sensor and acquire the viewport window
window = omni.kit.viewport.utility.create_viewport_window("Viewport 2")
# in order for the sensor to generate data properly we let the viewport know that it should create a buffer for the associated render variable.
omni.kit.viewport.utility.add_aov_to_viewport(window.viewport_api, "RtxSensorCpu")


# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

simulation_app.update()
# Loading the simple_room environment
stage.add_reference_to_stage(
    assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd", "/background"
)
simulation_app.update()

# Create the post process graph that publishes the render var
sensors.get_synthetic_data().activate_node_template(
    "RtxSensorCpu" + "ROS1PublishPointCloud", 0, [viewport.get_render_product_path()]
)

# Create the lidar sensor that generates data into "RtxSensorCpu"
# Sensor needs to be rotated 90 degrees about X so that its Z up

# Possible options are Example_Rotary and Example_Solid_State
_, (_, sensor) = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor",
    parent=None,
    config="Example_Rotary",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(0.707, 0.707, 0, 0),
)

# RTX sensors are cameras and must be assigned to their own viewport
viewport.set_active_camera(sensor.GetPath().pathString)

simulation_app.update()
simulation_app.update()

simulation_context = SimulationContext(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=1.0)

simulation_context.play()

while simulation_app.is_running():
    simulation_app.update()

# cleanup and shutdown
simulation_context.stop()
simulation_app.close()
