import sys
import numpy as np
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp()
sys.stdout.flush()
import omni

simulation_app.update()
omni.usd.get_context().new_stage()
simulation_app.update()

from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.isaac.core.objects import VisualCuboid
from omni.kit.viewport.utility import get_active_viewport

viewport_api = get_active_viewport()
sd_helper = SyntheticDataHelper()
sensor_names = [
    "rgb",
    "depth",
    "boundingBox2DTight",
    "boundingBox2DLoose",
    "instanceSegmentation",
    "semanticSegmentation",
    "boundingBox3D",
    "camera",
    "pose",
]
VisualCuboid(
    prim_path="/new_cube_1",
    name="visual_cube",
    position=np.array([0, 0, 0.5]),
    size=1.0,
    color=np.array([255, 255, 255]),
)

simulation_app.update()
sd_helper.initialize(sensor_names, viewport_api)
gt = sd_helper.get_groundtruth(sensor_names, viewport_api, verify_sensor_init=False)
print(gt["rgb"].size)

if gt["rgb"].size != 1280 * 720 * 4:
    raise ValueError(f"RGB buffer has size of {gt['rgb'].size} which is not {1280*720*4}")

# Cleanup application
simulation_app.close()
