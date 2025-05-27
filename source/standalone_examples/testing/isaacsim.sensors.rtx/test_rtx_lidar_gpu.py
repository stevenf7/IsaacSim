from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import argparse

import carb
import numpy as np
import omni
import omni.replicator.core as rep
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
from isaacsim.sensors.rtx import LidarRtx, get_gmo_data
from isaacsim.storage.native import get_assets_root_path

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode")
args, unknown = parser.parse_known_args()

assets_root_path = get_assets_root_path()

# Create a world
my_world = World(stage_units_in_meters=1.0)

# Load the small warehouse scene
assets_root_path = get_assets_root_path()
add_reference_to_stage(
    usd_path=assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd", prim_path="/World/warehouse"
)

# Place a basic lidar in the scene, overriding attributes as necessary
lidar = my_world.scene.add(LidarRtx(prim_path="/World/lidar", position=np.array([0.0, 0.0, 1.0]), name="lidar"))

simulation_app.update()
simulation_app.update()

# Initialize the lidar and attach an annotator
# ANNOTATOR_NAME = "GenericModelOutputLidarPointAccumulator"
ANNOTATOR_NAME = "IsaacExtractRTXSensorPointCloud"
lidar.initialize()
lidar.attach_annotator(ANNOTATOR_NAME)

timeline = omni.timeline.get_timeline_interface()
timeline.play()

stage = get_current_stage()
stage.Export("repro_rtx_lidar_on_gpu_segfault.usd")

i = 0
# Run for 10 frames in test mode
while simulation_app.is_running() and (not args.test or i < 10):
    simulation_app.update()
    i += 1
timeline.stop()

simulation_app.close()
