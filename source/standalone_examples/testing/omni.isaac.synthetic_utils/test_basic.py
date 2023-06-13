# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import carb
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.kit.viewport.utility import get_active_viewport
from omni.syntheticdata.tests.utils import add_semantics

viewport_api = get_active_viewport()
simulation_app.update()
stage = get_current_stage()
simulation_app.update()

assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    exit()
robot_usd = assets_root_path + "/Isaac/Robots/Carter/carter_v1.usd"

# setup high-level robot prim
prim = stage.DefinePrim("/robot", "Xform")
prim.GetReferences().AddReference(robot_usd)
add_semantics(prim, "robot")

simulation_app.update()

sd_helper = SyntheticDataHelper()
sensor_names = [
    "rgb",
    "depth",
    "boundingBox2DTight",
    "boundingBox2DLoose",
    "instanceSegmentation",
    "semanticSegmentation",
    "boundingBox3D",
]
sd_helper.initialize(sensor_names, viewport_api)


for frame in range(100):
    simulation_app.update()

gt = sd_helper.get_groundtruth(sensor_names, viewport_api, verify_sensor_init=False)

print(gt)


simulation_app.close()
