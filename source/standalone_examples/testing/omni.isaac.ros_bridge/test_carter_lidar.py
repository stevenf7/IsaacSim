# Copyright (c) 2020-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp
import numpy as np
import sys

CARTER_STAGE_PATH = "/Carter"
CARTER_USD_PATH = "/Isaac/Robots/Carter/carter_v1.usd"
BACKGROUND_STAGE_PATH = "/FlatGrid"
BACKGROUND_USD_PATH = "/Isaac/Environments/Grid/default_environment.usd"

CONFIG = {"renderer": "RayTracedLighting", "headless": False}

simulation_app = SimulationApp(CONFIG)
import omni
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils import viewports, stage, extensions, prims, rotations, nucleus
from pxr import Gf

extensions.enable_extension("omni.isaac.ros_bridge")

simulation_context = SimulationContext(stage_units_in_meters=1.0)

assets_root_path = nucleus.get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Preparing stage
viewports.set_camera_view(eye=np.array([120, 120, 80]), target=np.array([0, 0, 50]))

# Loading the flat grid environment
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)

# Loading the carter robot USD
prims.create_prim(
    CARTER_STAGE_PATH,
    "Xform",
    position=np.array([0, 0, 25]),
    orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 90)),
    usd_path=assets_root_path + CARTER_USD_PATH,
)

simulation_app.update()

# Load Lidar as disabled
omni.kit.commands.execute(
    "ROSBridgeCreateLidar",
    path="/ROS_Lidar",
    lidar_prim_rel=[CARTER_STAGE_PATH + "/chassis_link/carter_lidar"],
    enabled=False,
)


simulation_app.update()

# Tick component once to make sure ROS node is initialized
omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Lidar")

# need to initialize physics getting any articulation..etc
simulation_context.initialize_physics()
simulation_context.play()

frame = 0

while simulation_app.is_running():

    # Run with a fixed step size
    simulation_context.step(render=True)

    # Publish Lidar each frame
    omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Lidar")

    if frame > 120:
        break
    frame = frame + 1

simulation_context.stop()
simulation_app.close()
