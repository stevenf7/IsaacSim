# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# This file is meant as a tool for the isaac sim developers to test and debug.
# It is not meant for users, so use at your own risk.
import sys

import carb
from omni.isaac.kit import SimulationApp

# Example for creating a RTX lidar sensor and publishing PCL data
simulation_app = SimulationApp({"headless": False})
import omni
import omni.kit.viewport.utility
import omni.replicator.core as rep
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import nucleus, stage
from omni.isaac.core.utils.extensions import disable_extension, enable_extension
from omni.isaac.core.utils.render_product import create_hydra_texture
from pxr import Gf, UsdGeom, UsdPhysics

# enable ROS bridge extension
# enable_extension("omni.isaac.debug_draw")
# disable_extension("omni.replicator.core")


def printinc(i):
    print(f"{i}")
    return i + 1


i = 0

i = printinc(i)


def add_cube(stage, path, scale, offset, physics=False):
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)
    cubeGeom.CreateSizeAttr(1.0)
    cubeGeom.AddTranslateOp().Set(offset)
    cubeGeom.AddScaleOp().Set(scale)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)
    return cubePrim


i = printinc(i)
simulation_app.update()

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

i = printinc(i)
simulation_app.update()


if len(sys.argv) >= 2:
    geo_type = sys.argv[1]
    if geo_type == "warehouse":
        # Loading the simple_room environment
        stage.add_reference_to_stage(
            assets_root_path + "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd",
            "/background"
            # assets_root_path + "/Users/mcarlson@nvidia.com/Environments/Simple_Warehouse/full_warehouse.usd", "/background"
        )
    elif geo_type == "cubes":
        add_cube(stage.get_current_stage(), "/World/cube_1", (1, 20, 1), (5, 0, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cube_2", (1, 20, 1), (-5, 0, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cube_3", (20, 1, 1), (0, 5, 0), physics=False)
        add_cube(stage.get_current_stage(), "/World/cube_4", (20, 1, 1), (0, -5, 0), physics=False)
    elif geo_type == "floor":
        stage.add_reference_to_stage(
            assets_root_path + "/Users/mcarlson@nvidia.com/Environments/Simple_Warehouse/just_floor.usd", "/background"
        )
    elif geo_type == "floora":
        stage.add_reference_to_stage("/home/mcarlson/data/just_floor/just_floor0.usda", "/background")


lidar_config = "Example_Rotary"
if len(sys.argv) >= 3:
    lidar_config = sys.argv[1]

i = printinc(i)
simulation_app.update()

# Create the lidar sensor that generates data into "RtxSensorCpu"
# Sensor needs to be rotated 90 degrees about X so that its Z up

# Possible options are Example_Rotary and Example_Solid_State
# drive sim applies 0.5,-0.5,-0.5,w(-0.5), we have to apply the reverse

i = printinc(i)
_, sensor = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor",
    parent=None,
    config=lidar_config,
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
)

if 0:
    _, sensor2 = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path="/sensor2",
        parent=None,
        config=lidar_config,
        translation=(0, -1, 1.0),
        orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
    )

i = printinc(i)
_, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)
# _, render_product_path2 = create_hydra_texture([1, 1], sensor2.GetPath().pathString)

# Create the debug draw pipeline in the post process graph
if 1:
    i = printinc(i)
    # writer = rep.writers.get("RtxLidar" + "DebugDrawPointCloud")
    writer = rep.writers.get("Writer" + "IsaacReadRTXLidarData")

    i = printinc(i)
    writer.attach([render_product_path])  # , render_product_path2])
else:
    # print("try RtxSensorCpuExportRaw")
    from omni.syntheticdata import sensors

    sensors.get_synthetic_data().activate_node_template(
        "RtxSensorCpu" + "ExportRaw",
        # "RtxSensorCpuIsaacPrintRTXLidarInfo",
        # "RtxLidar" + "DebugDrawPointCloud",
        # "Template" + "RtxLidar" + "DebugDrawPointCloud",
        # "RtxSensorCpuIsaacReadRTXLidarData",
        0,
        [render_product_path],
    )

# disable_extension("omni.replicator.core")
i = printinc(i)
simulation_app.update()
simulation_app.update()

i = printinc(i)
simulation_context = SimulationContext(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0, stage_units_in_meters=1.0)

i = printinc(i)
simulation_context.play()

i = printinc(i)
while simulation_app.is_running():
    simulation_app.update()
    # break

# cleanup and shutdown

i = printinc(i)
simulation_context.stop()

i = printinc(i)
simulation_app.close()
