import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--test", action="store_true", help="Run in test mode.")
args, unknown = parser.parse_known_args()

import carb
from isaacsim import SimulationApp

BACKGROUND_STAGE_PATH = "/background"
BACKGROUND_USD_PATH = "/Isaac/Environments/Simple_Warehouse/warehouse_with_forklifts.usd"

CONFIG = {"renderer": "RayTracedLighting", "headless": False}

# Example ROS 2 bridge sample demonstrating the manual loading of stages and manual publishing of images
simulation_app = SimulationApp(CONFIG)
import isaacsim.core.utils.numpy.rotations as rot_utils
import numpy as np
import omni
import omni.graph.core as og
import omni.replicator.core as rep
import omni.syntheticdata._syntheticdata as sd
from isaacsim.core.api import SimulationContext
from isaacsim.core.nodes.scripts.utils import set_target_prims
from isaacsim.core.utils import extensions, stage
from isaacsim.core.utils.prims import is_prim_path_valid, set_targets
from isaacsim.sensors.camera import Camera
from isaacsim.storage.native import get_assets_root_path

# Enable ROS 2 bridge extension
extensions.enable_extension("isaacsim.ros2.bridge")

simulation_app.update()

simulation_context = SimulationContext(stage_units_in_meters=1.0)

# Locate Isaac Sim assets folder to load environment and robot stages
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    simulation_app.close()
    sys.exit()

# Loading the environment
stage.add_reference_to_stage(assets_root_path + BACKGROUND_USD_PATH, BACKGROUND_STAGE_PATH)


###### Camera helper functions for setting up publishers. ########

# Paste functions from the tutorial here
# def publish_camera_tf(camera: Camera): ...
# def publish_camera_info(camera: Camera, freq): ...
# def publish_pointcloud_from_depth(camera: Camera, freq): ...
# def publish_depth(camera: Camera, freq): ...
# def publish_rgb(camera: Camera, freq): ...

###################################################################

# Create a Camera prim. The Camera class takes the position and orientation in the world axes convention.
camera = Camera(
    prim_path="/World/floating_camera",
    position=np.array([-3.11, -1.87, 1.0]),
    frequency=20,
    resolution=(256, 256),
    orientation=rot_utils.euler_angles_to_quats(np.array([0, 0, 0]), degrees=True),
)
camera.initialize()

simulation_app.update()
camera.initialize()

############### Calling Camera publishing functions ###############

# Call the publishers.
# Make sure you pasted in the helper functions above, and uncomment out the following lines before running.

approx_freq = 30
# publish_camera_tf(camera)
# publish_camera_info(camera, approx_freq)
# publish_rgb(camera, approx_freq)
# publish_depth(camera, approx_freq)
# publish_pointcloud_from_depth(camera, approx_freq)

####################################################################

# Initialize physics
simulation_context.initialize_physics()
simulation_context.play()

i = 0
while simulation_app.is_running() and (not args.test or i < 100):
    simulation_context.step(render=True)
    i += 1
simulation_context.stop()
simulation_app.close()
